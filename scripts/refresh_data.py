"""Single-command data refresh: query DB, update constants, regenerate JSON, validate.

Usage: python scripts/refresh_data.py

Connects to cinderhaven-db on Fly.io via flyctl, extracts data,
updates generate_json.py constants, regenerates all JSON files, and runs the
prose validation test. Reports any data drift.

Requires: flyctl authenticated and on PATH.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
GENERATE_SCRIPT = SCRIPTS / "generate_json.py"
DATA_DIR = ROOT / "src" / "data"
TEST_SCRIPT = ROOT / "tests" / "test_prose_data.py"

APP = "cinderhaven-db"


def run_sql(sql):
    """Run SQL against cinderhaven-db via flyctl stdin pipe."""
    cmd = ["flyctl", "postgres", "connect", "-a", APP]
    full_sql = "\\pset pager off\n\\pset footer off\n\\c cinderhaven\n" + sql
    result = subprocess.run(
        cmd, input=full_sql, capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        print(f"ERROR: flyctl failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def parse_table(output):
    """Parse psql tabular output into list of dicts."""
    lines = output.strip().split("\n")
    data_lines = []
    headers = None
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("Pager") or stripped.startswith("You are now"):
            continue
        if set(stripped) <= {"-", "+", " "}:
            continue
        if stripped.startswith("(") and stripped.endswith("rows)"):
            continue
        if "\x1b" in line or "[?" in line:
            clean = re.sub(r'\x1b\[[^a-zA-Z]*[a-zA-Z]|\[\?[0-9]+[hl]', '', line).strip()
            if not clean or set(clean) <= {"-", "+", " "}:
                continue
            stripped = clean
        if "|" not in stripped:
            continue
        if headers is None:
            headers = [h.strip() for h in stripped.split("|")]
        else:
            values = [v.strip() for v in stripped.split("|")]
            if len(values) == len(headers):
                data_lines.append(dict(zip(headers, values)))
    return data_lines


def fetch_revenue():
    """Fetch total revenue by channel (all dates, no filter)."""
    sql = """
SELECT channel, revenue FROM (
    SELECT dr.retailer_name AS channel,
           ROUND(SUM(fo.total_value)::numeric, 2) AS revenue
    FROM public_marts.fct_retailer_orders fo
    JOIN public_marts.dim_retailers dr ON dr.retailer_id = fo.retailer_id
    GROUP BY dr.retailer_name
    UNION ALL
    SELECT dd.distributor_name AS channel,
           ROUND(SUM(fo.total_value)::numeric, 2) AS revenue
    FROM public_marts.fct_distributor_orders fo
    JOIN public_marts.dim_distributors dd ON dd.distributor_id = fo.distributor_id
    GROUP BY dd.distributor_name
    UNION ALL
    SELECT 'DTC' AS channel,
           ROUND(SUM(fo.gross_revenue)::numeric, 2) AS revenue
    FROM public_marts.fct_dtc_orders fo
) combined ORDER BY revenue DESC;
"""
    rows = parse_table(run_sql(sql))
    return {r["channel"]: float(r["revenue"]) for r in rows if r.get("channel")}


def fetch_deductions():
    """Fetch deductions by channel and type (retailer + distributor)."""
    sql = """
SELECT channel, deduction_type, event_count, total_amount FROM (
    SELECT dr.retailer_name AS channel,
           fd.deduction_type,
           COUNT(*)::int AS event_count,
           ROUND(SUM(fd.deduction_amount)::numeric, 2) AS total_amount
    FROM public_marts.fct_retailer_deductions fd
    JOIN public_marts.dim_retailers dr ON dr.retailer_id = fd.retailer_id
    GROUP BY dr.retailer_name, fd.deduction_type
    UNION ALL
    SELECT dd.distributor_name AS channel,
           fd.deduction_type,
           COUNT(*)::int AS event_count,
           ROUND(SUM(fd.deduction_amount)::numeric, 2) AS total_amount
    FROM public_marts.fct_distributor_deductions fd
    JOIN public_marts.dim_distributors dd ON dd.distributor_id = fd.distributor_id
    GROUP BY dd.distributor_name, fd.deduction_type
) combined ORDER BY channel, total_amount DESC;
"""
    rows = parse_table(run_sql(sql))
    result = {}
    for r in rows:
        try:
            name = r["channel"]
            dtype = r["deduction_type"]
            amount = float(r["total_amount"])
            count = int(r["event_count"])
            result.setdefault(name, {})[dtype] = (amount, count)
        except (ValueError, KeyError):
            continue
    return result


def fetch_disputes():
    """Fetch dispute data by channel from retailer deductions with dispute_id."""
    sql = """
SELECT channel, disputes, events, total_hours FROM (
    SELECT dr.retailer_name AS channel,
           COUNT(DISTINCT fd.dispute_id)::int AS disputes,
           COUNT(*)::int AS events,
           ROUND(SUM(fd.dispute_labor_hours)::numeric, 1) AS total_hours
    FROM public_marts.fct_retailer_deductions fd
    JOIN public_marts.dim_retailers dr ON dr.retailer_id = fd.retailer_id
    WHERE fd.dispute_id IS NOT NULL
    GROUP BY dr.retailer_name
    UNION ALL
    SELECT dd.distributor_name AS channel,
           COUNT(DISTINCT fd.dispute_id)::int AS disputes,
           COUNT(*)::int AS events,
           ROUND(SUM(fd.dispute_labor_hours)::numeric, 1) AS total_hours
    FROM public_marts.fct_distributor_deductions fd
    JOIN public_marts.dim_distributors dd ON dd.distributor_id = fd.distributor_id
    WHERE fd.dispute_id IS NOT NULL
    GROUP BY dd.distributor_name
) combined ORDER BY total_hours DESC;
"""
    rows = parse_table(run_sql(sql))
    result = {}
    for r in rows:
        try:
            result[r["channel"]] = {
                "disputes": int(r["disputes"]),
                "events": int(r["events"]),
                "hours": float(r["total_hours"]),
            }
        except (ValueError, KeyError):
            continue
    return result


def fetch_quarterly_data():
    """Fetch quarterly revenue and deductions for trends."""
    rev_sql = """
SELECT q, channel, revenue FROM (
    SELECT DATE_TRUNC('quarter', fo.po_date)::date AS q,
           dr.retailer_name AS channel,
           ROUND(SUM(fo.total_value)::numeric, 2) AS revenue
    FROM public_marts.fct_retailer_orders fo
    JOIN public_marts.dim_retailers dr ON dr.retailer_id = fo.retailer_id
    GROUP BY q, dr.retailer_name
    UNION ALL
    SELECT DATE_TRUNC('quarter', fo.po_date)::date AS q,
           dd.distributor_name AS channel,
           ROUND(SUM(fo.total_value)::numeric, 2) AS revenue
    FROM public_marts.fct_distributor_orders fo
    JOIN public_marts.dim_distributors dd ON dd.distributor_id = fo.distributor_id
    GROUP BY q, dd.distributor_name
    UNION ALL
    SELECT DATE_TRUNC('quarter', fo.created_at)::date AS q,
           'DTC' AS channel,
           ROUND(SUM(fo.gross_revenue)::numeric, 2) AS revenue
    FROM public_marts.fct_dtc_orders fo
    GROUP BY q
) combined ORDER BY q, channel;
"""
    rev_rows = parse_table(run_sql(rev_sql))
    quarterly_rev = {}
    for r in rev_rows:
        try:
            q = r["q"]
            quarterly_rev.setdefault(q, {})[r["channel"]] = float(r["revenue"])
        except (ValueError, KeyError):
            continue

    ded_sql = """
SELECT q, channel, deductions FROM (
    SELECT DATE_TRUNC('quarter', fd.deduction_date)::date AS q,
           dr.retailer_name AS channel,
           ROUND(SUM(fd.deduction_amount)::numeric, 2) AS deductions
    FROM public_marts.fct_retailer_deductions fd
    JOIN public_marts.dim_retailers dr ON dr.retailer_id = fd.retailer_id
    GROUP BY q, dr.retailer_name
    UNION ALL
    SELECT DATE_TRUNC('quarter', fd.deduction_date)::date AS q,
           dd.distributor_name AS channel,
           ROUND(SUM(fd.deduction_amount)::numeric, 2) AS deductions
    FROM public_marts.fct_distributor_deductions fd
    JOIN public_marts.dim_distributors dd ON dd.distributor_id = fd.distributor_id
    GROUP BY q, dd.distributor_name
) combined ORDER BY q, channel;
"""
    ded_rows = parse_table(run_sql(ded_sql))
    quarterly_ded = {}
    for r in ded_rows:
        try:
            q = r["q"]
            quarterly_ded.setdefault(q, {})[r["channel"]] = float(r["deductions"])
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


def update_generate_script(revenue, deductions, disputes, quarterly_rev, quarterly_ded):
    """Update the constants in generate_json.py with fresh data.

    Creates a .bak backup before writing. Restores on failure.
    """
    backup_path = GENERATE_SCRIPT.with_suffix(".py.bak")
    original_content = GENERATE_SCRIPT.read_text()
    backup_path.write_text(original_content)

    try:
        content = original_content

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
            new_disputes += f'    "{name}": {{"disputes": {d["disputes"]}, "events": {d["events"]}, "hours": {d["hours"]}}},\n'
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
    print()

    print("[1/6] Capturing current JSON state...")
    before = snapshot_json()

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

    print("[4/6] Querying quarterly data...")
    quarterly_rev, quarterly_ded = fetch_quarterly_data()
    print(f"  {len(quarterly_rev)} quarters of revenue data")
    print(f"  {len(quarterly_ded)} quarters of deduction data")

    print("[5/6] Updating generate_json.py constants...")
    update_generate_script(revenue, deductions, disputes, quarterly_rev, quarterly_ded)

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

    after = snapshot_json()
    print("\n[6/6] Comparing JSON output...")
    changed = report_diff(before, after)

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
