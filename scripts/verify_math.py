"""Verify internal math consistency of all JSON data files."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
channels = json.loads((ROOT / "src/data/channels.json").read_text())
layers = json.loads((ROOT / "src/data/layers.json").read_text())
trends = json.loads((ROOT / "src/data/trends.json").read_text())

errors = 0


def check(label, actual, expected, tolerance=0.02):
    global errors
    if abs(actual - expected) > tolerance:
        print(f"  FAIL: {label}: got {actual}, expected {expected}")
        errors += 1
    else:
        print(f"  OK:   {label}")


total_rev = sum(c["gross_revenue"] for c in channels)
print("Total revenue: ${:,.2f}".format(total_rev))

net_layer = layers[4]
total_contrib = sum(c["value"] for c in net_layer["channels"])
print("Total net contribution: ${:,.2f}".format(total_contrib))
print("Overall margin: {:.1f}%".format((total_contrib / total_rev) * 100))

# Layer consistency: each layer's value should equal previous_value minus breakdown amounts
print("\nLayer consistency checks:")
for layer_idx in range(1, 5):
    layer = layers[layer_idx]
    for ch in layer["channels"]:
        name = ch["channel_name"]
        prev = ch.get("previous_value", 0)
        breakdown_total = sum(item["amount"] for item in ch.get("breakdown", []))
        expected_value = round(prev - breakdown_total, 2)
        check(f"Layer {layer_idx} {name}", ch["value"], expected_value)

# Cross-file: channels.json revenue matches layers[0]
print("\nCross-file revenue checks:")
for ch_data in channels:
    name = ch_data["channel_name"]
    layer0_ch = next(c for c in layers[0]["channels"] if c["channel_name"] == name)
    check(f"{name} revenue", ch_data["gross_revenue"], layer0_ch["value"])

# Cross-file: channels.json COGS matches layers[1] breakdown
print("\nCross-file COGS checks:")
for ch_data in channels:
    name = ch_data["channel_name"]
    layer1_ch = next(c for c in layers[1]["channels"] if c["channel_name"] == name)
    cogs_from_layer = layer1_ch["breakdown"][0]["amount"] if layer1_ch["breakdown"] else 0
    check(f"{name} COGS", ch_data["total_cogs"], cogs_from_layer)

# Channel margins
print("\nChannel margins:")
for rev_ch in layers[0]["channels"]:
    name = rev_ch["channel_name"]
    net_ch = next(c for c in net_layer["channels"] if c["channel_name"] == name)
    margin = (net_ch["value"] / rev_ch["value"]) * 100
    print("  {:20s}: {:.1f}%".format(name, margin))

# Aggregate deduction totals from layer breakdowns
print("\nAggregate totals from layers:")
trade_total = sum(
    sum(item["amount"] for item in ch.get("breakdown", []))
    for ch in layers[2]["channels"]
)
print("  Trade deductions + promo: ${:,.2f}".format(trade_total))

fines_total = sum(
    sum(item["amount"] for item in ch.get("breakdown", []))
    for ch in layers[3]["channels"]
)
print("  Compliance fines: ${:,.2f}".format(fines_total))

overhead_total = sum(
    sum(item["amount"] for item in ch.get("breakdown", []))
    for ch in layers[4]["channels"]
)
print("  Operational overhead: ${:,.2f}".format(overhead_total))

# Trend data: margin_pct should equal (contribution/revenue)*100
print("\nTrend margin checks (sample quarters):")
for q in trends:
    for ch in q["channels"]:
        if ch["revenue"] > 0:
            expected_margin = round((ch["contribution"] / ch["revenue"]) * 100, 1)
            check(f"{q['quarter']} {ch['channel_name']} margin", ch["margin_pct"], expected_margin, tolerance=0.15)

print(f"\n{'=' * 40}")
if errors > 0:
    print(f"FAILED: {errors} checks did not pass")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
