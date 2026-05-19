"""Validate that hardcoded prose claims in MDX files match computed values from JSON data.

Run: python -m pytest tests/test_prose_data.py -v
Or:  python tests/test_prose_data.py (standalone, no pytest required)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "src" / "data"


def load_data():
    channels = json.loads((DATA / "channels.json").read_text())
    layers = json.loads((DATA / "layers.json").read_text())
    trends = json.loads((DATA / "trends.json").read_text())
    return channels, layers, trends


def get_channel(channels, name):
    return next(c for c in channels if c["channel_name"] == name)


def layer_value(layers, layer_id, channel_name):
    layer = layers[layer_id]
    return next(c["value"] for c in layer["channels"] if c["channel_name"] == channel_name)


def margin_pct(layers, channel_name):
    rev = layer_value(layers, 0, channel_name)
    net = layer_value(layers, 4, channel_name)
    return (net / rev) * 100


def sum_breakdown_type(layers, layer_id, dtype):
    total = 0
    for ch in layers[layer_id]["channels"]:
        for item in ch.get("breakdown", []):
            if item.get("type") == dtype:
                total += item["amount"]
    return total


def layer_diff(layers, from_id, to_id):
    """Sum of (from_layer - to_layer) across all channels."""
    return sum(
        layers[from_id]["channels"][i]["value"] - layers[to_id]["channels"][i]["value"]
        for i in range(len(layers[from_id]["channels"]))
    )


class Results:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def check(self, description, actual, expected, tolerance=0.02):
        """Check that actual is within tolerance of expected (relative)."""
        if expected == 0:
            ok = abs(actual) < 0.01
        else:
            ok = abs(actual - expected) / abs(expected) <= tolerance
        if ok:
            self.passed += 1
        else:
            self.failed += 1
            self.errors.append(
                "  FAIL: {} — expected {:.2f}, got {:.2f}".format(description, expected, actual)
            )

    def check_range(self, description, actual_min, actual_max, expected_min, expected_max, tolerance=0.5):
        """Check that a range claim is approximately correct."""
        ok = abs(actual_min - expected_min) <= tolerance and abs(actual_max - expected_max) <= tolerance
        if ok:
            self.passed += 1
        else:
            self.failed += 1
            self.errors.append(
                "  FAIL: {} — expected {:.1f}-{:.1f}, got {:.1f}-{:.1f}".format(
                    description, expected_min, expected_max, actual_min, actual_max
                )
            )


def validate_schema(channels, layers, trends):
    """Verify JSON files have the fields that TypeScript components expect."""
    errors = []

    # channels.json schema
    required_channel_fields = {"channel_name", "gross_revenue", "total_cogs",
                               "total_deductions", "disputes_filed", "total_deduction_events"}
    for ch in channels:
        missing = required_channel_fields - set(ch.keys())
        if missing:
            errors.append("channels.json: {} missing fields: {}".format(
                ch.get("channel_name", "?"), missing))

    # layers.json schema
    for layer in layers:
        if "id" not in layer or "channels" not in layer:
            errors.append("layers.json: layer missing 'id' or 'channels'")
            continue
        for ch in layer["channels"]:
            if "channel_name" not in ch or "value" not in ch:
                errors.append("layers.json layer {}: channel missing required fields".format(
                    layer["id"]))

    # trends.json schema
    for q in trends:
        if "quarter" not in q or "channels" not in q:
            errors.append("trends.json: quarter entry missing 'quarter' or 'channels'")
            continue
        for ch in q["channels"]:
            required = {"channel_name", "margin_pct", "revenue", "contribution"}
            missing = required - set(ch.keys())
            if missing:
                errors.append("trends.json {}: {} missing {}".format(
                    q["quarter"], ch.get("channel_name", "?"), missing))

    return errors


def run_validation():
    channels, layers, trends = load_data()
    r = Results()

    # --- Schema validation ---
    schema_errors = validate_schema(channels, layers, trends)
    for err in schema_errors:
        r.failed += 1
        r.errors.append("  FAIL: Schema — " + err)
    if not schema_errors:
        r.passed += 1

    # --- 01-headline.mdx claims ---
    total_rev = sum(c["gross_revenue"] for c in channels)

    # "The gap... ranges from 27% to 79%"
    all_margins = [margin_pct(layers, c["channel_name"]) for c in layers[0]["channels"]]
    all_erosion = [100 - m for m in all_margins]
    r.check_range("Erosion range 27%-79%", min(all_erosion), max(all_erosion), 27, 79)

    # "DTC retains 73 cents"
    dtc_margin = margin_pct(layers, "DTC")
    r.check("DTC retains 73 cents", dtc_margin, 73.0, tolerance=0.01)

    # "wholesale channels retain between 21 and 36 cents"
    wholesale_margins = [margin_pct(layers, c["channel_name"])
                         for c in layers[0]["channels"]
                         if c["channel_name"] != "DTC"]
    r.check_range("Wholesale retain 21-36 cents",
                  min(wholesale_margins), max(wholesale_margins), 21, 36, tolerance=1.0)

    # --- 03-deductions.mdx claims ---
    trade_total = layer_diff(layers, 1, 2)
    r.check("Trade deductions $3.1M", trade_total, 3_100_000, tolerance=0.03)

    promo_total = sum_breakdown_type(layers, 2, "promo_billback")
    r.check("Promo billbacks $1.7M", promo_total, 1_700_000, tolerance=0.03)

    vague_total = sum_breakdown_type(layers, 2, "vague")
    r.check("Unclassified $1.2M", vague_total, 1_200_000, tolerance=0.03)

    # Whole Foods trade deduction rate 18.1%
    wf_rev = get_channel(channels, "Whole Foods")["gross_revenue"]
    wf_gross_margin = layer_value(layers, 1, "Whole Foods")
    wf_after_trade = layer_value(layers, 2, "Whole Foods")
    wf_trade = wf_gross_margin - wf_after_trade
    wf_trade_rate = (wf_trade / wf_rev) * 100
    r.check("Whole Foods trade rate 18.1%", wf_trade_rate, 18.1, tolerance=0.01)

    # Walmart trade deduction rate 15.1%
    wm_rev = get_channel(channels, "Walmart")["gross_revenue"]
    wm_trade = layer_value(layers, 1, "Walmart") - layer_value(layers, 2, "Walmart")
    wm_trade_rate = (wm_trade / wm_rev) * 100
    r.check("Walmart trade rate 15.1%", wm_trade_rate, 15.1, tolerance=0.01)

    # --- 04-fines.mdx claims ---
    fines_total = layer_diff(layers, 2, 3)
    r.check("Compliance fines $778K", fines_total, 778_000, tolerance=0.01)

    spoilage_total = sum_breakdown_type(layers, 3, "spoilage")
    r.check("Spoilage $527K", spoilage_total, 527_000, tolerance=0.01)

    label_total = sum_breakdown_type(layers, 3, "label_fine")
    r.check("Label fines $106K", label_total, 106_000, tolerance=0.01)

    # UNFI spoilage $167K, 205 events
    unfi_spoilage = next(
        item for ch in layers[3]["channels"]
        if ch["channel_name"] == "UNFI"
        for item in ch.get("breakdown", [])
        if item.get("type") == "spoilage"
    )
    r.check("UNFI spoilage $167K", unfi_spoilage["amount"], 167_000, tolerance=0.01)

    # --- 05-operational.mdx claims ---
    overhead_total = layer_diff(layers, 3, 4)
    r.check("Operational overhead $324K", overhead_total, 324_000, tolerance=0.01)

    total_disputes = sum(c["disputes_filed"] for c in channels)
    r.check("Total disputes count", total_disputes, 2163, tolerance=0.0)

    # Walmart overhead $181K
    wm_overhead = layer_value(layers, 3, "Walmart") - layer_value(layers, 4, "Walmart")
    r.check("Walmart overhead $181K", wm_overhead, 181_000, tolerance=0.01)

    # Recovery claims: $359K recovered, 1.11:1 ratio (from verify_roi.py constants)
    recovery_total = 358894.66
    recovery_ratio = recovery_total / overhead_total
    r.check("Recovery $359K", recovery_total, 359_000, tolerance=0.01)
    r.check("Recovery ratio 1.11:1", recovery_ratio, 1.11, tolerance=0.01)

    r.check("Walmart disputes 1209", get_channel(channels, "Walmart")["disputes_filed"], 1209, tolerance=0.0)

    # --- 06-contribution.mdx claims ---
    r.check("Walmart margin 21.1%", margin_pct(layers, "Walmart"), 21.1, tolerance=0.005)
    r.check("UNFI margin 22.3%", margin_pct(layers, "UNFI"), 22.3, tolerance=0.005)
    r.check("KeHE margin 23.1%", margin_pct(layers, "KeHE"), 23.1, tolerance=0.005)
    r.check("DTC margin 73.2%", margin_pct(layers, "DTC"), 73.2, tolerance=0.005)
    r.check("Regional Group margin", margin_pct(layers, "Regional Group"), 35.5, tolerance=0.10)

    # "COGS consuming 51-59% of revenue" for retailers
    retailer_cogs_rates = []
    for ch in layers[0]["channels"]:
        if ch["channel_name"] != "DTC" and ch.get("channel_type") != "distributor":
            name = ch["channel_name"]
            cogs_ch = next(c for c in channels if c["channel_name"] == name)
            rate = (cogs_ch["total_cogs"] / cogs_ch["gross_revenue"]) * 100
            retailer_cogs_rates.append(rate)
    r.check_range("Retailer COGS 51-59%", min(retailer_cogs_rates), max(retailer_cogs_rates), 51, 59)

    # Distributors $6.4M revenue, $1.5M contribution
    dist_rev = sum(layer_value(layers, 0, n) for n in ["UNFI", "KeHE"])
    dist_contrib = sum(layer_value(layers, 4, n) for n in ["UNFI", "KeHE"])
    r.check("Distributors revenue $6.4M", dist_rev, 6_400_000, tolerance=0.01)
    r.check("Distributors contribution $1.5M", dist_contrib, 1_500_000, tolerance=0.05)

    # --- 07-allocation.mdx claims ---
    dtc_rev = layer_value(layers, 0, "DTC")
    r.check("DTC revenue $1.3M", dtc_rev, 1_300_000, tolerance=0.01)

    wm_vague = next(
        item["amount"] for ch in layers[2]["channels"]
        if ch["channel_name"] == "Walmart"
        for item in ch.get("breakdown", [])
        if item.get("type") == "vague"
    )
    r.check("Walmart vague deductions $456K", wm_vague, 456_000, tolerance=0.01)

    # --- 06-trends.mdx claims ---
    # Costco margins swing from 23% to 39%
    costco_margins = [
        next(c["margin_pct"] for c in q["channels"] if c["channel_name"] == "Costco")
        for q in trends
    ]
    r.check_range("Costco trend margin 23%-39%",
                  min(costco_margins), max(costco_margins), 23, 39, tolerance=1.0)

    return r


def test_prose_matches_data():
    """Pytest entry point: all prose claims must match computed data."""
    r = run_validation()
    if r.errors:
        msg = "\n".join(r.errors)
        raise AssertionError("{} checks failed:\n{}".format(r.failed, msg))


def main():
    print("=== Prose vs Data Validation ===\n")
    r = run_validation()

    if r.errors:
        print("FAILURES:")
        for e in r.errors:
            print(e)
        print()

    print("{} passed, {} failed".format(r.passed, r.failed))

    if r.failed > 0:
        sys.exit(1)
    else:
        print("\nAll prose claims match computed data.")
        sys.exit(0)


if __name__ == "__main__":
    main()
