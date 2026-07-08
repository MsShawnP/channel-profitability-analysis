"""Validate that hardcoded prose claims in MDX files match computed values from JSON data.

All expected values are annual averages (FY2024–FY2026).

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

    # Erosion range across all channels
    all_margins = [margin_pct(layers, c["channel_name"]) for c in layers[0]["channels"]]
    all_erosion = [100 - m for m in all_margins]
    r.check_range("Erosion range 44%-56%", min(all_erosion), max(all_erosion), 44.4, 55.6)

    # "DTC retains 53 cents"
    dtc_margin = margin_pct(layers, "DTC")
    r.check("DTC retains 53 cents", dtc_margin, 52.84, tolerance=0.01)

    # Wholesale channel margins range
    wholesale_margins = [margin_pct(layers, c["channel_name"])
                         for c in layers[0]["channels"]
                         if c["channel_name"] != "DTC"]
    r.check_range("Wholesale margins 44-55%",
                  min(wholesale_margins), max(wholesale_margins), 44, 55.5, tolerance=1.0)

    # --- 03-deductions.mdx claims (annual) ---
    trade_total = layer_diff(layers, 1, 2)
    r.check("Trade deductions + promo ~$276K/yr", trade_total, 275_738, tolerance=0.03)

    promo_total = sum_breakdown_type(layers, 2, "promo_billback")
    r.check("Promo billbacks ~$69K/yr", promo_total, 69_200, tolerance=0.03)

    pricing_total = sum_breakdown_type(layers, 2, "pricing_error")
    r.check("Pricing errors ~$71K/yr", pricing_total, 71_100, tolerance=0.03)

    # Costco trade+promo rate ~1.5%
    costco_rev = get_channel(channels, "Costco")["gross_revenue"]
    costco_trade = layer_value(layers, 1, "Costco") - layer_value(layers, 2, "Costco")
    costco_trade_rate = (costco_trade / costco_rev) * 100
    r.check("Costco trade+promo rate ~1.1%", costco_trade_rate, 1.13, tolerance=0.15)

    # --- 04-fines.mdx claims (annual) ---
    fines_total = layer_diff(layers, 2, 3)
    r.check("Compliance fines ~$237K/yr", fines_total, 236_932, tolerance=0.03)

    damaged_total = sum_breakdown_type(layers, 3, "damaged")
    r.check("Damaged goods ~$72K/yr", damaged_total, 72_000, tolerance=0.03)

    late_total = sum_breakdown_type(layers, 3, "late_delivery")
    r.check("Late delivery ~$10.1K/yr", late_total, 10_069, tolerance=0.03)

    kroger_fines = layer_value(layers, 2, "Kroger") - layer_value(layers, 3, "Kroger")
    kroger_damaged = next(
        item["amount"] for ch in layers[3]["channels"]
        if ch["channel_name"] == "Kroger"
        for item in ch.get("breakdown", [])
        if item.get("type") == "damaged"
    )
    r.check("Kroger damaged ~$9.5K/yr", kroger_damaged, 9_467, tolerance=0.02)

    dpi_late = next(
        item["amount"] for ch in layers[3]["channels"]
        if ch["channel_name"] == "DPI Northwest"
        for item in ch.get("breakdown", [])
        if item.get("type") == "late_delivery"
    )
    r.check("DPI NW late delivery ~$1.9K/yr", dpi_late, 1_928, tolerance=0.03)

    # --- 05-operational.mdx claims (annual) ---
    overhead_total = layer_diff(layers, 3, 4)
    r.check("Operational overhead ~$141K/yr", overhead_total, 141_106, tolerance=0.01)

    total_disputes = sum(c["disputes_filed"] for c in channels)
    r.check("Total disputes (annual)", total_disputes, 2189, tolerance=0.01)

    costco_overhead = layer_value(layers, 3, "Costco") - layer_value(layers, 4, "Costco")
    r.check("Costco overhead ~$17.0K/yr", costco_overhead, 17_014, tolerance=0.01)
    r.check("Costco disputes (annual)", get_channel(channels, "Costco")["disputes_filed"], 264, tolerance=0.0)
    r.check("Costco events (annual)", get_channel(channels, "Costco")["total_deduction_events"], 675, tolerance=0.0)

    wm_overhead = layer_value(layers, 3, "Walmart") - layer_value(layers, 4, "Walmart")
    r.check("Walmart overhead ~$28.7K/yr", wm_overhead, 28_662, tolerance=0.02)
    r.check("Walmart disputes (annual)", get_channel(channels, "Walmart")["disputes_filed"], 442, tolerance=0.0)

    unfi_oh = layer_value(layers, 3, "UNFI") - layer_value(layers, 4, "UNFI")
    kehe_oh = layer_value(layers, 3, "KeHE") - layer_value(layers, 4, "KeHE")
    r.check("UNFI+KeHE overhead ~$12.6K/yr", unfi_oh + kehe_oh, 12_565, tolerance=0.02)

    # --- 07-contribution.mdx claims ---
    r.check("Walmart margin 48.8%", margin_pct(layers, "Walmart"), 48.77, tolerance=0.005)
    r.check("UNFI margin 45.2%", margin_pct(layers, "UNFI"), 45.24, tolerance=0.005)
    r.check("KeHE margin 46.5%", margin_pct(layers, "KeHE"), 46.54, tolerance=0.005)
    r.check("DTC margin 52.8%", margin_pct(layers, "DTC"), 52.84, tolerance=0.005)
    r.check("Regional Group margin 51.0%", margin_pct(layers, "Regional Group"), 50.96, tolerance=0.005)
    r.check("Costco margin 46.8%", margin_pct(layers, "Costco"), 46.82, tolerance=0.005)
    r.check("Whole Foods margin 55.6%", margin_pct(layers, "Whole Foods"), 55.55, tolerance=0.005)

    # Retailer COGS 14-17%
    retailer_cogs_rates = []
    for ch in layers[0]["channels"]:
        if ch.get("channel_type") == "retailer":
            name = ch["channel_name"]
            cogs_ch = next(c for c in channels if c["channel_name"] == name)
            rate = (cogs_ch["total_cogs"] / cogs_ch["gross_revenue"]) * 100
            retailer_cogs_rates.append(rate)
    r.check_range("Retailer COGS 42-50%", min(retailer_cogs_rates), max(retailer_cogs_rates), 41.5, 50.5)

    # All distributors: $8.0M/yr revenue, $3.6M/yr contribution
    dist_names = [c["channel_name"] for c in channels if c["channel_type"] == "distributor"]
    dist_rev = sum(layer_value(layers, 0, n) for n in dist_names)
    dist_contrib = sum(layer_value(layers, 4, n) for n in dist_names)
    r.check("Distributors revenue ~$8.0M/yr", dist_rev, 7_979_510, tolerance=0.01)
    r.check("Distributors contribution ~$3.6M/yr", dist_contrib, 3_611_482, tolerance=0.01)

    # --- 08-allocation.mdx claims (annual) ---
    dtc_rev = layer_value(layers, 0, "DTC")
    r.check("DTC revenue ~$189K/yr", dtc_rev, 188_708, tolerance=0.01)

    r.check("Walmart highest overhead ~$28.7K/yr", wm_overhead, 28_662, tolerance=0.01)

    # --- 06-trends.mdx claims ---
    # Costco margins range
    costco_margins = [
        next(c["margin_pct"] for c in q["channels"] if c["channel_name"] == "Costco")
        for q in trends
    ]
    r.check_range("Costco trend margin 46%-49%",
                  min(costco_margins), max(costco_margins), 46, 49.5, tolerance=0.5)

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
