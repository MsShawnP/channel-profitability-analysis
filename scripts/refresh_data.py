"""Single-command data refresh: query DB, update constants, regenerate JSON, validate.

Usage: python scripts/refresh_data.py

Connects to cinderhaven-db on Fly.io via flyctl, extracts fiscal-year data,
updates generate_json.py constants, regenerates all JSON files, and runs the
prose validation test. Reports any data drift.

Requires: flyctl authenticated and on PATH.
"""
import json
import re
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
GENERATE_SCRIPT = SCRIPTS / "generate_json.py"
DATA_DIR = ROOT / "src" / "data"
TEST_SCRIPT = ROOT / "tests" / "test_prose_data.py"

APP = "cinderhaven-db"
DB = "cinderhaven"
FISCAL_START = "2025-04-01"
FISCAL_END = "2026-04-01"


def run_sql(sql):
    """Run SQL against cinderhaven-db via flyctl and return raw output."""
    cmd = ["flyctl", "postgres", "connect", "-a", APP, "--database", DB]
    full_sql = "\\pset pager off\n\\pset footer off\n" + sql
    result = subprocess.run(
        cmd, input=full_sql, capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"ERROR: flyctl failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def parse_table(output, skip_header_lines=2):
    """Parse psql tabular output into list of dicts."""
    lines = [l for l in output.strip().split("\n") if l.strip() and not l.startswith("Pager")]
    if len(lines) < skip_header_lines + 1:
        return []
    headers = [h.strip() for h in lines[0].split("|")]
    rows = []
    for line in lines[skip_header_lines:]:
        if line.strip().startswith("(") or set(line.strip()) <= {"-", "+", " "}:
            continue
        values = [v.strip() for v in line.split("|")]
        if len(values) == len(headers):
            rows.append(dict(zip(headers, values)))
    return rows


def fetch_revenue():
    """Fetch fiscal year revenue by channel."""
    sql = f"""
SELECT r.retailer_name AS channel_name,
       SUM(o.line_total) AS revenue
FROM public_marts.fct_orders o
JOIN public_marts.dim_retailers r ON o.retailer_id = r.retailer_id
WHERE o.order_date >= '{FISCAL_START}' AND o.order_date < '{FISCAL_END}'
GROUP BY r.retailer_name
ORDER BY revenue DESC;
"""
    output = run_sql(sql)
    rows = parse_table(output)
    result = {}
    for r in rows:
        try:
            result[r["channel_name"]] = float(r["revenue"])
        except (ValueError, KeyError):
            continue
    return result


def fetch_deductions():
    """Fetch fiscal year deductions by channel and type."""
    sql = f"""
SELECT r.retailer_name AS channel_name,
       d.deduction_type,
       COUNT(*) AS event_count,
       SUM(d.deduction_amount) AS total_amount
FROM public_marts.fct_deductions d
JOIN public_marts.dim_retailers r ON d.retailer_id = r.retailer_id
WHERE d.deduction_date >= '{FISCAL_START}' AND d.deduction_date < '{FISCAL_END}'
GROUP BY r.retailer_name, d.deduction_type
ORDER BY r.retailer_name, total_amount DESC;
"""
    output = run_sql(sql)
    rows = parse_table(output)
    result = {}
    for r in rows:
        try:
            name = r["channel_name"]
            dtype = r["deduction_type"]
            amount = float(r["total_amount"])
            count = int(r["event_count"])
            if name not in result:
                result[name] = {}
            result[name][dtype] = (amount, count)
        except (ValueError, KeyError):
            continue
    return result


def fetch_disputes():
    """Fetch fiscal year dispute data by channel."""
    sql = f"""
SELECT r.retailer_name AS channel_name,
       COUNT(DISTINCT d.deduction_id) FILTER (WHERE d.dispute_filed) AS disputes,
       COUNT(*) AS events,
       SUM(d.hours_to_resolve) AS total_hours
FROM public_marts.fct_deductions d
JOIN public_marts.dim_retailers r ON d.retailer_id = r.retailer_id
WHERE d.deduction_date >= '{FISCAL_START}' AND d.deduction_date < '{FISCAL_END}'
GROUP BY r.retailer_name
ORDER BY total_hours DESC;
"""
    output = run_sql(sql)
    rows = parse_table(output)
    result = {}
    for r in rows:
        try:
            result[r["channel_name"]] = {
                "disputes": int(r["disputes"]),
                "events": int(r["events"]),
                "hours": float(r["total_hours"]),
            }
        except (ValueError, KeyError):
            continue
    return result


def fetch_cogs_ratios():
    """Fetch COGS ratios from mart."""
    sql = """
SELECT channel_name, cogs_ratio
FROM public_marts.mart_channel_contribution
ORDER BY gross_revenue DESC;
"""
    output = run_sql(sql)
    rows = parse_table(output)
    result = {}
    for r in rows:
        try:
            result[r["channel_name"]] = float(r["cogs_ratio"])
        except (ValueError, KeyError):
            continue
    return result


def fetch_quarterly_data():
    """Fetch quarterly revenue and deductions for trends."""
    sql = f"""
SELECT DATE_TRUNC('quarter', o.order_date)::date AS quarter,
       r.retailer_name AS channel_name,
       SUM(o.line_total) AS revenue
FROM public_marts.fct_orders o
JOIN public_marts.dim_retailers r ON o.retailer_id = r.retailer_id
WHERE o.order_date >= '2025-01-01' AND o.order_date < '{FISCAL_END}'
GROUP BY quarter, r.retailer_name
ORDER BY quarter, revenue DESC;
"""
    rev_output = run_sql(sql)
    rev_rows = parse_table(rev_output)

    sql_ded = f"""
SELECT DATE_TRUNC('quarter', d.deduction_date)::date AS quarter,
       r.retailer_name AS channel_name,
       SUM(d.deduction_amount) AS deductions
FROM public_marts.fct_deductions d
JOIN public_marts.dim_retailers r ON d.retailer_id = r.retailer_id
WHERE d.deduction_date >= '2025-01-01' AND d.deduction_date < '{FISCAL_END}'
GROUP BY quarter, r.retailer_name
ORDER BY quarter, r.retailer_name;
"""
    ded_output = run_sql(sql_ded)
    ded_rows = parse_table(ded_output)

    quarterly_rev = {}
    for r in rev_rows:
        try:
            q = r["quarter"]
            quarterly_rev.setdefault(q, {})[r["channel_name"]] = float(r["revenue"])
        except (ValueError, KeyError):
            continue

    quarterly_ded = {}
    for r in ded_rows:
        try:
            q = r["quarter"]
            quarterly_ded.setdefault(q, {})[r["channel_name"]] = float(r["deductions"])
        except (ValueError, KeyError):
            continue

    return quarterly_rev, quarterly_ded



def _safe_sub(content, pattern, replacement, label, flags=0):
    """Replace pattern in content, raising if no match found."""
    new_content, count = re.subn(pattern, replacement, content, count=1, flags=flags)
    if count == 0:
        raise RuntimeError(
            f"refresh_data: failed to match {label} pattern in generate_json.py. "
            "File may have been manually edited into an unexpected format."
        )
    return new_content


def update_generate_script(revenue, deductions, disputes, cogs_ratios, quarterly_rev, quarterly_ded):
    """Update the constants in generate_json.py with fresh data.

    Creates a .bak backup before writing. Restores on failure.
    """
    backup_path = GENERATE_SCRIPT.with_suffix(".py.bak")
    original_content = GENERATE_SCRIPT.read_text()
    backup_path.write_text(original_content)

    try:
        content = original_content

        # Update COGS_RATIOS
        new_cogs = "COGS_RATIOS = {\n"
        for name, ratio in cogs_ratios.items():
            new_cogs += f'    "{name}": {ratio:.4f},\n'
        new_cogs += "}"
        content = _safe_sub(content, r"COGS_RATIOS = \{[^}]+\}", new_cogs, "COGS_RATIOS")

        # Update FISCAL_REVENUE
        new_rev = "FISCAL_REVENUE = {\n"
        for name, rev in revenue.items():
            new_rev += f'    "{name}": {rev:.2f},\n'
        new_rev += "}"
        content = _safe_sub(content, r"FISCAL_REVENUE = \{[^}]+\}", new_rev, "FISCAL_REVENUE")

        # Update DEDUCTIONS (multi-line nested dict)
        new_ded = "DEDUCTIONS = {\n"
        for channel, types in deductions.items():
            new_ded += f'    "{channel}": {{\n'
            for dtype, (amount, count) in types.items():
                new_ded += f'        "{dtype}": ({amount}, {count}),\n'
            new_ded += "    },\n"
        new_ded += "}"
        content = _safe_sub(content, r"DEDUCTIONS = \{.*?\n\}", new_ded, "DEDUCTIONS", flags=re.DOTALL)

        # Update DISPUTE_DATA
        new_disputes = "DISPUTE_DATA = {\n"
        for name, d in disputes.items():
            new_disputes += f'    "{name}": {{"disputes": {d["disputes"]}, "events": {d["events"]}, "hours": {d["hours"]:.2f}}},\n'
        new_disputes += '    "DTC": {"disputes": 0, "events": 0, "hours": 0},\n'
        new_disputes += "}"
        content = _safe_sub(content, r"DISPUTE_DATA = \{.*?\n\}", new_disputes, "DISPUTE_DATA", flags=re.DOTALL)

        # Update QUARTERLY_REVENUE
        new_qrev = "QUARTERLY_REVENUE = {\n"
        for q in sorted(quarterly_rev.keys()):
            channels = quarterly_rev[q]
            inner = ", ".join(f'"{n}": {v:.2f}' for n, v in channels.items())
            new_qrev += f'    "{q}": {{{inner}}},\n'
        new_qrev += "}"
        content = _safe_sub(content, r"QUARTERLY_REVENUE = \{.*?\n\}", new_qrev, "QUARTERLY_REVENUE", flags=re.DOTALL)

        # Update QUARTERLY_DEDUCTIONS
        new_qded = "QUARTERLY_DEDUCTIONS = {\n"
        for q in sorted(quarterly_ded.keys()):
            channels = quarterly_ded[q]
            inner = ", ".join(f'"{n}": {v:.2f}' for n, v in channels.items())
            new_qded += f'    "{q}": {{{inner}}},\n'
        new_qded += "}"
        content = _safe_sub(content, r"QUARTERLY_DEDUCTIONS = \{.*?\n\}", new_qded, "QUARTERLY_DEDUCTIONS", flags=re.DOTALL)

        GENERATE_SCRIPT.write_text(content)
        backup_path.unlink()

    except Exception:
        # Restore original on any failure
        GENERATE_SCRIPT.write_text(original_content)
        backup_path.unlink(missing_ok=True)
        raise


def snapshot_json():
    """Capture current JSON state for diff comparison."""
    result = {}
    for name in ["channels.json", "layers.json", "trends.json"]:
        path = DATA_DIR / name
        if path.exists():
            result[name] = json.loads(path.read_text())
    return result


def report_diff(before, after):
    """Report meaningful differences between JSON snapshots."""
    changed = False
    for name in ["channels.json", "layers.json", "trends.json"]:
        if before.get(name) != after.get(name):
            print(f"  CHANGED: {name}")
            changed = True
            if name == "channels.json" and name in before and name in after:
                for old, new in zip(before[name], after[name]):
                    if old["gross_revenue"] != new["gross_revenue"]:
                        delta = new["gross_revenue"] - old["gross_revenue"]
                        print(f"    {old['channel_name']}: revenue {'+' if delta > 0 else ''}{delta:,.2f}")
        else:
            print(f"  unchanged: {name}")
    return changed


def main():
    print("=" * 50)
    print("Channel Profitability — Data Refresh")
    print("=" * 50)
    print(f"\nFiscal year: {FISCAL_START} to {FISCAL_END}")
    print()

    # Snapshot current state
    print("[1/6] Capturing current JSON state...")
    before = snapshot_json()

    # Fetch from database
    print("[2/6] Querying revenue from cinderhaven-db...")
    revenue = fetch_revenue()
    if not revenue:
        print("ERROR: No revenue data returned. Check flyctl auth.", file=sys.stderr)
        sys.exit(1)
    print(f"  Found {len(revenue)} channels, total ${sum(revenue.values()):,.0f}")

    print("[3/6] Querying deductions and disputes...")
    deductions = fetch_deductions()
    disputes = fetch_disputes()
    print(f"  {len(deductions)} channels with deductions")
    print(f"  {sum(d['disputes'] for d in disputes.values())} total disputes")

    print("[4/6] Querying COGS ratios and quarterly data...")
    cogs_ratios = fetch_cogs_ratios()
    quarterly_rev, quarterly_ded = fetch_quarterly_data()
    print(f"  {len(quarterly_rev)} quarters of trend data")

    # DTC estimate (not in fct_orders — use 1/3 of 3-year mart total)
    if "DTC" not in revenue and "DTC" in cogs_ratios:
        dtc_sql = """
SELECT gross_revenue FROM public_marts.mart_channel_contribution
WHERE channel_name = 'DTC';
"""
        dtc_output = run_sql(dtc_sql)
        dtc_rows = parse_table(dtc_output)
        if dtc_rows:
            dtc_3yr = float(dtc_rows[0]["gross_revenue"])
            revenue["DTC"] = round(dtc_3yr / 3, 2)
            print(f"  DTC estimated: ${revenue['DTC']:,.0f} (1/3 of 3-year mart total)")

    # Update generate_json.py
    print("[5/6] Updating generate_json.py constants...")
    update_generate_script(revenue, deductions, disputes, cogs_ratios, quarterly_rev, quarterly_ded)

    # Regenerate JSON
    print("  Running generate_json.py...")
    result = subprocess.run(
        [sys.executable, str(GENERATE_SCRIPT)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"ERROR: generate_json.py failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    for line in result.stdout.strip().split("\n"):
        print(f"  {line}")

    # Compare
    after = snapshot_json()
    print("\n[6/6] Comparing JSON output...")
    changed = report_diff(before, after)

    # Validate prose
    print("\n--- Prose Validation ---")
    result = subprocess.run(
        [sys.executable, str(TEST_SCRIPT)],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print("WARNING: Prose validation FAILED. MDX prose needs updating.")
        print(result.stdout)
        sys.exit(1)

    print("\n" + "=" * 50)
    if changed:
        print("DATA DRIFT DETECTED — JSON files updated.")
        print("Review changes and update MDX prose if validation failed.")
    else:
        print("No data drift. All files match the database.")
    print("=" * 50)


if __name__ == "__main__":
    main()
