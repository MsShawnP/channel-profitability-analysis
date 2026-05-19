"""Verify dispute ROI math before incorporating into narrative."""

# Recovery totals from stg_retailer_disputes + stg_distributor_disputes,
# joined through deductions to get partner name. Full 2-year window.
# Extracted from Postgres 2026-05-18 (greenfield rebuild).
recoveries = {
    "Costco": 2274.37,
    "Kroger": 1479.62,
    "Sprouts": 1477.76,
    "Walmart": 1467.60,
    "Regional Group": 1208.79,
    "Whole Foods": 1058.28,
    "DPI Northwest": 1087.64,
    "KeHE": 502.39,
    "UNFI": 433.17,
}

# Dispute labor hours per channel (from stg_*_disputes.labor_hours)
hours = {
    "Costco": 331.8, "Walmart": 326.5, "Kroger": 299.4,
    "Regional Group": 292.6, "Sprouts": 257.4, "Whole Foods": 220.7,
    "KeHE": 56.3, "UNFI": 54.6, "DPI Northwest": 51.5,
}

OVERHEAD_RATE = 35.00
total_hours = sum(hours.values())
overhead = total_hours * OVERHEAD_RATE
total_recovered = sum(recoveries.values())
net_gain = total_recovered - overhead
roi_pct = (net_gain / overhead) * 100
recovery_ratio = total_recovered / overhead

print("=== Dispute ROI Verification ===")
print("Operational overhead: ${:,.2f}  ({:.0f} hrs × ${:.0f}/hr)".format(overhead, total_hours, OVERHEAD_RATE))
print("Total recovered:      ${:,.2f}".format(total_recovered))
print("Net gain:             ${:,.2f}".format(net_gain))
print()
print("Recovery/cost ratio:  {:.3f}x".format(recovery_ratio))
print("  (${:.2f} back per $1.00 spent on triage)".format(recovery_ratio))
print()
print("Standard ROI:         {:.1f}%".format(roi_pct))
print()
print("Per-channel recovery rates:")

for name in sorted(recoveries.keys(), key=lambda k: recoveries[k], reverse=True):
    ch_overhead = hours[name] * OVERHEAD_RATE
    ch_recovery = recoveries[name]
    ch_ratio = ch_recovery / ch_overhead if ch_overhead > 0 else 0
    print("  {:20s}: overhead ${:>9,.0f}  recovered ${:>9,.0f}  ratio {:.2f}x".format(
        name, ch_overhead, ch_recovery, ch_ratio))
