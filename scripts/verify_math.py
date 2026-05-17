"""Verify internal math consistency of all JSON data files."""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
channels = json.loads((ROOT / "src/data/channels.json").read_text())
layers = json.loads((ROOT / "src/data/layers.json").read_text())
trends = json.loads((ROOT / "src/data/trends.json").read_text())

total_rev = sum(c["gross_revenue"] for c in channels)
print("Total revenue: ${:,.2f}".format(total_rev))

net_layer = layers[4]
total_contrib = sum(c["value"] for c in net_layer["channels"])
print("Total net contribution: ${:,.2f}".format(total_contrib))
print("Overall margin: {:.1f}%".format((total_contrib / total_rev) * 100))

print("\nChannel margins:")
rev_layer = layers[0]
for rev_ch in rev_layer["channels"]:
    name = rev_ch["channel_name"]
    net_ch = next(c for c in net_layer["channels"] if c["channel_name"] == name)
    margin = (net_ch["value"] / rev_ch["value"]) * 100
    print("  {:20s}: {:.1f}%".format(name, margin))

trade_total = sum(
    layers[1]["channels"][i]["value"] - layers[2]["channels"][i]["value"]
    for i in range(len(channels))
)
print("\nTrade deductions: ${:,.2f}".format(trade_total))

fines_total = sum(
    layers[2]["channels"][i]["value"] - layers[3]["channels"][i]["value"]
    for i in range(len(channels))
)
print("Compliance fines: ${:,.2f}".format(fines_total))

overhead_total = sum(
    layers[3]["channels"][i]["value"] - layers[4]["channels"][i]["value"]
    for i in range(len(channels))
)
print("Operational overhead: ${:,.2f}".format(overhead_total))

print("\nDTC in quarterly trends:")
for q in trends:
    dtc = next((c for c in q["channels"] if c["channel_name"] == "DTC"), None)
    if dtc:
        print("  {}: rev=${:,.0f} margin={}%".format(q["quarter"], dtc["revenue"], dtc["margin_pct"]))

print("\nKey prose claim checks:")
wf_rev = next(c for c in channels if c["channel_name"] == "Whole Foods")["gross_revenue"]
wf_trade = layers[1]["channels"][3]["value"] - layers[2]["channels"][3]["value"]
print("  Whole Foods trade ded rate: {:.1f}% (prose says 18.1%)".format((wf_trade / wf_rev) * 100))

wm_trade = layers[1]["channels"][0]["value"] - layers[2]["channels"][0]["value"]
print("  Walmart trade ded rate: {:.1f}% (prose says 15.1%)".format((wm_trade / channels[0]["gross_revenue"]) * 100))

# Spoilage total
spoilage_total = 0
for ch in layers[3]["channels"]:
    for item in ch.get("breakdown", []):
        if item.get("type") == "spoilage":
            spoilage_total += item["amount"]
print("  Spoilage total: ${:,.0f} (prose says $527K)".format(spoilage_total))

# Label fines total
label_total = 0
for ch in layers[3]["channels"]:
    for item in ch.get("breakdown", []):
        if item.get("type") == "label_fine":
            label_total += item["amount"]
print("  Label fines total: ${:,.0f} (prose says $106K)".format(label_total))

# Vague total
vague_total = 0
for ch in layers[2]["channels"]:
    for item in ch.get("breakdown", []):
        if item.get("type") == "vague":
            vague_total += item["amount"]
print("  Unclassified total: ${:,.0f} (prose says $1.2M)".format(vague_total))

# Promo billback total
promo_total = 0
for ch in layers[2]["channels"]:
    for item in ch.get("breakdown", []):
        if item.get("type") == "promo_billback":
            promo_total += item["amount"]
print("  Promo billbacks total: ${:,.0f} (prose says $1.7M)".format(promo_total))
