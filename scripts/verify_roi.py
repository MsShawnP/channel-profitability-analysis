"""Verify dispute ROI math from JSON data (not hardcoded values)."""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
layers = json.loads((ROOT / "src/data/layers.json").read_text())

OVERHEAD_RATE = 35.00

print("=== Dispute ROI Verification ===\n")

total_overhead = 0
channel_data = []

for ch in layers[4]["channels"]:
    overhead = sum(item["amount"] for item in ch.get("breakdown", []))
    total_overhead += overhead
    channel_data.append({"name": ch["channel_name"], "overhead": overhead})

print(f"Total operational overhead: ${total_overhead:,.2f}")
total_hours = total_overhead / OVERHEAD_RATE
print(f"Total dispute hours: {total_hours:,.1f} ({total_hours:,.1f} hrs × ${OVERHEAD_RATE:.0f}/hr)")

print("\nPer-channel overhead:")
for ch in sorted(channel_data, key=lambda x: x["overhead"], reverse=True):
    if ch["overhead"] > 0:
        hours = ch["overhead"] / OVERHEAD_RATE
        print(f"  {ch['name']:20s}: ${ch['overhead']:>10,.2f}  ({hours:,.1f} hrs)")

print(f"\nTotal overhead as % of revenue:")
total_rev = sum(c["value"] for c in layers[0]["channels"])
print(f"  ${total_overhead:,.2f} / ${total_rev:,.2f} = {(total_overhead/total_rev)*100:.2f}%")
