"""Verify dispute ROI math before incorporating into narrative."""

overhead = 324255.75  # total hours * $35/hr from generate_json.py

# Recovery totals from fct_payments, fiscal year Apr 2025 - Mar 2026
recoveries = {
    "Walmart": 214502.59,
    "UNFI": 43815.91,
    "Whole Foods": 26458.11,
    "KeHE": 40577.43,
    "Costco": 21856.19,
    "Southside Grocers": 4228.99,
    "Green Basket Market": 4417.18,
    "Prairie Provisions": 1048.73,
    "Mountain Pantry Co": 1066.38,
    "Harbor Fresh": 923.15,
}

total_recovered = sum(recoveries.values())
net_gain = total_recovered - overhead
roi_pct = (net_gain / overhead) * 100
recovery_ratio = total_recovered / overhead

print("=== Dispute ROI Verification ===")
print("Operational overhead: ${:,.2f}".format(overhead))
print("Total recovered:      ${:,.2f}".format(total_recovered))
print("Net gain:             ${:,.2f}".format(net_gain))
print()
print("Recovery/cost ratio:  {:.3f}x".format(recovery_ratio))
print("  (${:.2f} back per $1.00 spent on triage)".format(recovery_ratio))
print()
print("Standard ROI:         {:.1f}%".format(roi_pct))
print("  (net gain / cost -- NOT the 111% I initially claimed)")
print()
print("Per-channel recovery rates:")
# Match overhead per channel from generate_json.py dispute hours
hours = {
    "Walmart": 5175.94, "UNFI": 1400.60, "KeHE": 851.38,
    "Whole Foods": 1024.34, "Costco": 191.59,
    "Southside Grocers": 141.17, "Green Basket Market": 266.83,
    "Prairie Provisions": 83.24, "Mountain Pantry Co": 94.18,
    "Harbor Fresh": 35.18,
}

for name in sorted(recoveries.keys(), key=lambda k: recoveries[k], reverse=True):
    ch_overhead = hours[name] * 35
    ch_recovery = recoveries[name]
    ch_ratio = ch_recovery / ch_overhead if ch_overhead > 0 else 0
    print("  {:20s}: overhead ${:>9,.0f}  recovered ${:>9,.0f}  ratio {:.2f}x".format(
        name, ch_overhead, ch_recovery, ch_ratio))
