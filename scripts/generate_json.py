"""
Generate channels.json, layers.json, and trends.json.
Revenue and COGS from Postgres fact tables when available,
falling back to snapshot values for offline use.
Run from project root: python scripts/generate_json.py
"""
import json
import os
from pathlib import Path

try:
    import psycopg2
    import psycopg2.extras
    _HAS_PG = True
except ImportError:
    _HAS_PG = False

# === SNAPSHOT DATA (full 2-year window, 2024-01-01 through 2025-12-31) ===
# Extracted from Postgres 2026-05-18. Used as offline fallback when Postgres
# is unavailable. Live path queries fact tables directly (no date filter).

COGS_RATIOS = {
    "UNFI": 0.0852, "DPI Northwest": 0.0756, "KeHE": 0.0846,
    "DTC": 0.0805,
    "Sprouts": 0.1494, "Whole Foods": 0.1406, "Regional Group": 0.1551,
    "Kroger": 0.1592, "Walmart": 0.1648, "Costco": 0.1687,
}

FISCAL_REVENUE = {
    "UNFI": 563417.88, "DPI Northwest": 553833.12, "KeHE": 483792.12,
    "DTC": 367185.13,
    "Sprouts": 349267.68, "Whole Foods": 339027.72, "Regional Group": 328431.12,
    "Kroger": 327646.68, "Walmart": 321690.00, "Costco": 310973.76,
}

DEDUCTIONS = {
    "UNFI": {
        "promo_billback": (1115.81, 16), "pricing_error": (1538.06, 29),
        "short_ship": (1020.59, 17), "damaged": (1600.98, 23),
        "late_delivery": (1297.74, 18),
    },
    "DPI Northwest": {
        "promo_billback": (1479.98, 20), "pricing_error": (1246.33, 18),
        "short_ship": (1068.37, 17), "damaged": (1031.33, 17),
        "late_delivery": (2117.88, 23),
    },
    "KeHE": {
        "promo_billback": (1756.35, 28), "pricing_error": (1837.94, 23),
        "short_ship": (1100.04, 17), "damaged": (1209.65, 15),
        "late_delivery": (1018.03, 20),
    },
    "Sprouts": {
        "promo_billback": (1207.25, 43), "pricing_error": (1118.19, 36),
        "short_ship": (963.54, 36), "slotting": (789.66, 38),
        "label_fine": (1002.37, 44), "spoilage": (712.49, 31),
        "damaged": (808.76, 31), "pallet_fine": (839.33, 41), "late_delivery": (851.77, 41),
    },
    "Whole Foods": {
        "promo_billback": (1072.84, 43), "pricing_error": (512.74, 28),
        "short_ship": (997.74, 46), "slotting": (724.76, 28),
        "label_fine": (637.13, 31), "spoilage": (1096.10, 42),
        "damaged": (738.58, 33), "pallet_fine": (936.98, 36), "late_delivery": (611.43, 25),
    },
    "Regional Group": {
        "promo_billback": (903.30, 40), "pricing_error": (864.93, 41),
        "short_ship": (927.07, 38), "slotting": (786.98, 35),
        "label_fine": (1068.92, 43), "spoilage": (737.92, 41),
        "damaged": (615.86, 31), "pallet_fine": (905.89, 35), "late_delivery": (1232.77, 46),
    },
    "Kroger": {
        "promo_billback": (717.56, 32), "pricing_error": (783.72, 38),
        "short_ship": (951.96, 41), "slotting": (876.56, 45),
        "label_fine": (655.16, 31), "spoilage": (1103.46, 48),
        "damaged": (1370.39, 57), "pallet_fine": (1122.94, 48), "late_delivery": (558.88, 33),
    },
    "Walmart": {
        "promo_billback": (624.27, 34), "pricing_error": (829.65, 35),
        "short_ship": (727.58, 37), "slotting": (671.91, 39),
        "label_fine": (825.69, 42), "spoilage": (656.21, 30),
        "damaged": (1139.32, 52), "pallet_fine": (971.63, 40), "late_delivery": (549.27, 28),
    },
    "Costco": {
        "promo_billback": (1159.50, 47), "pricing_error": (954.56, 36),
        "short_ship": (984.17, 44), "slotting": (1072.64, 44),
        "label_fine": (824.07, 35), "spoilage": (746.10, 44),
        "damaged": (708.57, 32), "pallet_fine": (1215.39, 50), "late_delivery": (503.33, 25),
    },
}

DISPUTE_DATA = {
    "Costco": {"disputes": 159, "events": 357, "hours": 683.7},
    "Kroger": {"disputes": 149, "events": 373, "hours": 640.7},
    "Walmart": {"disputes": 144, "events": 337, "hours": 619.2},
    "Regional Group": {"disputes": 139, "events": 350, "hours": 598.0},
    "Sprouts": {"disputes": 121, "events": 341, "hours": 520.3},
    "Whole Foods": {"disputes": 99, "events": 312, "hours": 425.7},
    "KeHE": {"disputes": 35, "events": 103, "hours": 150.5},
    "UNFI": {"disputes": 32, "events": 103, "hours": 137.6},
    "DPI Northwest": {"disputes": 32, "events": 95, "hours": 137.6},
    "DTC": {"disputes": 0, "events": 0, "hours": 0},
}

OVERHEAD_RATE = 35.00  # $/hr fully loaded
PROMO_COSTS_ANNUAL = {
    "UNFI": 444.00, "DPI Northwest": 266.00, "KeHE": 266.00,
    "DTC": 0,
    "Sprouts": 538.00, "Whole Foods": 1140.00, "Regional Group": 538.00,
    "Kroger": 538.00, "Walmart": 1613.00, "Costco": 2220.00,
}

CHANNEL_IDS = {
    "UNFI": "unfi", "DPI Northwest": "dpi_northwest", "KeHE": "kehe",
    "DTC": "DTC",
    "Sprouts": "sprouts", "Whole Foods": "whole_foods",
    "Regional Group": "regional_group",
    "Kroger": "kroger", "Walmart": "walmart", "Costco": "costco",
}

CHANNEL_TYPES = {
    "UNFI": "distributor", "DPI Northwest": "distributor", "KeHE": "distributor",
    "DTC": "dtc",
    "Sprouts": "retailer", "Whole Foods": "retailer",
    "Regional Group": "retailer",
    "Kroger": "retailer", "Walmart": "retailer", "Costco": "retailer",
}

CHANNEL_ORDER = [
    "UNFI", "DPI Northwest", "KeHE", "DTC",
    "Sprouts", "Whole Foods", "Regional Group",
    "Kroger", "Walmart", "Costco",
]

TRADE_TYPES = ["promo_billback", "pricing_error", "short_ship", "slotting"]
COMPLIANCE_TYPES = ["label_fine", "spoilage", "damaged", "pallet_fine", "late_delivery"]

TYPE_LABELS = {
    "promo_billback": "Promo Billback", "pricing_error": "Pricing Error",
    "short_ship": "Short Ship", "slotting": "Slotting Fees",
    "label_fine": "Label Fines", "spoilage": "Spoilage",
    "damaged": "Damaged Goods", "pallet_fine": "Pallet Fines",
    "late_delivery": "Late Delivery",
}

# === QUARTERLY DATA for trends (Q1 2024 through Q4 2025) ===
QUARTERLY_REVENUE = {
    "2024-01-01": {"UNFI": 50915.52, "DPI Northwest": 53710.08, "KeHE": 36310.56, "DTC": 39383.52, "Sprouts": 34157.94, "Whole Foods": 37085.76, "Regional Group": 33409.02, "Kroger": 31269.12, "Walmart": 34407.00, "Costco": 26399.52},
    "2024-04-01": {"UNFI": 63253.32, "DPI Northwest": 56982.60, "KeHE": 50223.72, "DTC": 44925.81, "Sprouts": 41547.24, "Whole Foods": 36764.76, "Regional Group": 35828.82, "Kroger": 42865.92, "Walmart": 33840.00, "Costco": 39300.48},
    "2024-07-01": {"UNFI": 63368.64, "DPI Northwest": 75498.12, "KeHE": 63789.12, "DTC": 43806.31, "Sprouts": 47728.92, "Whole Foods": 41478.30, "Regional Group": 37332.36, "Kroger": 35529.18, "Walmart": 44493.00, "Costco": 34996.32},
    "2024-10-01": {"UNFI": 100437.60, "DPI Northwest": 107164.92, "KeHE": 64865.52, "DTC": 58637.79, "Sprouts": 57955.26, "Whole Foods": 47878.32, "Regional Group": 49797.78, "Kroger": 48695.70, "Walmart": 49933.50, "Costco": 54047.52},
    "2025-01-01": {"UNFI": 51715.56, "DPI Northwest": 44808.36, "KeHE": 75135.48, "DTC": 38253.40, "Sprouts": 34795.92, "Whole Foods": 36352.56, "Regional Group": 35033.52, "Kroger": 37436.82, "Walmart": 30003.00, "Costco": 30064.32},
    "2025-04-01": {"UNFI": 67766.52, "DPI Northwest": 84031.92, "KeHE": 58658.28, "DTC": 43323.88, "Sprouts": 44048.58, "Whole Foods": 40770.48, "Regional Group": 40848.54, "Kroger": 40408.38, "Walmart": 34366.50, "Costco": 40350.24},
    "2025-07-01": {"UNFI": 68193.00, "DPI Northwest": 55084.68, "KeHE": 62687.88, "DTC": 43480.59, "Sprouts": 34502.28, "Whole Foods": 39763.98, "Regional Group": 44520.30, "Kroger": 40326.96, "Walmart": 43381.50, "Costco": 34691.04},
    "2025-10-01": {"UNFI": 97767.72, "DPI Northwest": 76552.44, "KeHE": 72121.56, "DTC": 55373.83, "Sprouts": 54531.54, "Whole Foods": 58933.56, "Regional Group": 51660.78, "Kroger": 51114.60, "Walmart": 51265.50, "Costco": 51124.32},
}

QUARTERLY_DEDUCTIONS = {
    "2024-01-01": {"UNFI": 707.15, "KeHE": 313.84, "DPI Northwest": 119.44, "Sprouts": 479.61, "Whole Foods": 373.38, "Regional Group": 564.06, "Kroger": 509.27, "Walmart": 473.78, "Costco": 446.20},
    "2024-04-01": {"UNFI": 1055.61, "KeHE": 541.76, "DPI Northwest": 68.32, "Sprouts": 978.52, "Whole Foods": 1131.57, "Regional Group": 926.64, "Kroger": 788.04, "Walmart": 939.77, "Costco": 1436.57},
    "2024-07-01": {"UNFI": 1096.05, "KeHE": 855.98, "DPI Northwest": 917.46, "Sprouts": 1057.71, "Whole Foods": 836.35, "Regional Group": 1020.39, "Kroger": 864.00, "Walmart": 915.46, "Costco": 776.12},
    "2024-10-01": {"UNFI": 455.05, "KeHE": 814.72, "DPI Northwest": 2282.72, "Sprouts": 1292.23, "Whole Foods": 616.89, "Regional Group": 1093.44, "Kroger": 1313.80, "Walmart": 1093.16, "Costco": 1236.72},
    "2025-01-01": {"UNFI": 652.17, "KeHE": 1196.33, "DPI Northwest": 758.79, "Sprouts": 1400.09, "Whole Foods": 1060.26, "Regional Group": 664.40, "Kroger": 1063.25, "Walmart": 760.93, "Costco": 974.34},
    "2025-04-01": {"UNFI": 1346.16, "KeHE": 800.28, "DPI Northwest": 1315.08, "Sprouts": 1188.24, "Whole Foods": 1203.92, "Regional Group": 1172.28, "Kroger": 1418.02, "Walmart": 986.33, "Costco": 1080.47},
    "2025-07-01": {"UNFI": 775.95, "KeHE": 832.60, "DPI Northwest": 904.90, "Sprouts": 772.88, "Whole Foods": 1059.04, "Regional Group": 1239.90, "Kroger": 1136.41, "Walmart": 781.07, "Costco": 1213.85},
    "2025-10-01": {"UNFI": 485.04, "KeHE": 1566.50, "DPI Northwest": 577.18, "Sprouts": 1124.08, "Whole Foods": 1046.89, "Regional Group": 1362.53, "Kroger": 1047.84, "Walmart": 1045.03, "Costco": 1004.06},
}

QUARTER_LABELS = {
    "2024-01-01": "Q1 2024", "2024-04-01": "Q2 2024",
    "2024-07-01": "Q3 2024", "2024-10-01": "Q4 2024",
    "2025-01-01": "Q1 2025", "2025-04-01": "Q2 2025",
    "2025-07-01": "Q3 2025", "2025-10-01": "Q4 2025",
}


def _pg_connect():
    if not _HAS_PG:
        return None
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        pw = os.environ.get("POSTGRES_PASSWORD")
        if not pw:
            return None
        dsn = f"postgresql://postgres:REDACTED@localhost:5432/cinderhaven"
    try:
        return psycopg2.connect(dsn)
    except Exception:
        return None


def fetch_live_channel_data():
    """Fetch per-channel revenue from fact tables (retailer + distributor + DTC)."""
    conn = _pg_connect()
    if conn is None:
        return None, None
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT retailer, revenue FROM (
                    SELECT dr.retailer_name AS retailer,
                           SUM(fo.total_value)::float AS revenue
                    FROM public_marts.fct_retailer_orders fo
                    JOIN public_marts.dim_retailers dr
                         ON dr.retailer_id = fo.retailer_id
                    GROUP BY dr.retailer_name
                    UNION ALL
                    SELECT dd.distributor_name AS retailer,
                           SUM(fo.total_value)::float AS revenue
                    FROM public_marts.fct_distributor_orders fo
                    JOIN public_marts.dim_distributors dd
                         ON dd.distributor_id = fo.distributor_id
                    GROUP BY dd.distributor_name
                    UNION ALL
                    SELECT 'DTC' AS retailer,
                           SUM(fo.gross_revenue)::float AS revenue
                    FROM public_marts.fct_dtc_orders fo
                ) combined ORDER BY revenue DESC
            """)
            rows = cur.fetchall()
        revenue = {r["retailer"]: round(r["revenue"], 2) for r in rows}
        return revenue, None
    except Exception:
        return None, None
    finally:
        conn.close()


def compute_channel_data():
    """Compute all derived values for each channel."""
    channels = []
    for name in CHANNEL_ORDER:
        revenue = FISCAL_REVENUE[name]
        cogs = round(revenue * COGS_RATIOS[name], 2)
        gross_margin = round(revenue - cogs, 2)

        # Sum trade deductions
        deductions = DEDUCTIONS.get(name, {})
        trade_ded = sum(deductions.get(t, (0, 0))[0] for t in TRADE_TYPES)
        quality_fines = sum(deductions.get(t, (0, 0))[0] for t in ["label_fine", "spoilage", "damaged", "pallet_fine"])
        logistics_fines = deductions.get("late_delivery", (0, 0))[0]
        total_deductions = trade_ded + quality_fines + logistics_fines

        promo = PROMO_COSTS_ANNUAL.get(name, 0)
        dispute = DISPUTE_DATA.get(name, {"disputes": 0, "events": 0, "hours": 0})
        overhead = round(dispute["hours"] * OVERHEAD_RATE, 2)

        layer_1 = gross_margin
        layer_2 = round(layer_1 - trade_ded - promo, 2)
        layer_3 = round(layer_2 - quality_fines - logistics_fines, 2)
        layer_4 = round(layer_3 - overhead, 2)

        channels.append({
            "channel_id": CHANNEL_IDS[name],
            "channel_name": name,
            "channel_type": CHANNEL_TYPES[name],
            "gross_revenue": revenue,
            "total_cogs": cogs,
            "gross_margin": gross_margin,
            "trade_deductions": round(trade_ded, 2),
            "quality_fines": round(quality_fines, 2),
            "logistics_fines": round(logistics_fines, 2),
            "total_deductions": round(total_deductions, 2),
            "promo_costs": promo,
            "operational_overhead": overhead,
            "disputes_filed": dispute["disputes"],
            "total_deduction_events": dispute["events"],
            "layer_1": layer_1,
            "layer_2": layer_2,
            "layer_3": layer_3,
            "layer_4": layer_4,
        })
    return channels


def generate_channels(channel_data):
    return [
        {
            "channel_id": ch["channel_id"],
            "channel_name": ch["channel_name"],
            "channel_type": ch["channel_type"],
            "gross_revenue": ch["gross_revenue"],
            "total_cogs": ch["total_cogs"],
            "total_deductions": ch["total_deductions"],
            "disputes_filed": ch["disputes_filed"],
            "total_deduction_events": ch["total_deduction_events"],
        }
        for ch in channel_data
    ]


def generate_layers(channel_data):
    layers = []

    layers.append({
        "id": 0, "label": "Revenue", "subtitle": "What the CFO sees",
        "channels": [
            {"channel_name": ch["channel_name"], "channel_type": ch["channel_type"],
             "value": ch["gross_revenue"], "breakdown": []}
            for ch in channel_data
        ]
    })

    layers.append({
        "id": 1, "label": "Gross Margin", "subtitle": "After cost of goods sold",
        "channels": [
            {"channel_name": ch["channel_name"], "channel_type": ch["channel_type"],
             "value": ch["layer_1"], "previous_value": ch["gross_revenue"],
             "breakdown": [{"label": "Cost of Goods Sold", "amount": ch["total_cogs"]}]}
            for ch in channel_data
        ]
    })

    # Layer 2: After Trade Deductions
    layer2_channels = []
    for ch in channel_data:
        name = ch["channel_name"]
        breakdown = []
        if name in DEDUCTIONS:
            for dtype in TRADE_TYPES:
                amount, count = DEDUCTIONS[name].get(dtype, (0, 0))
                if amount > 0:
                    breakdown.append({"label": TYPE_LABELS[dtype], "type": dtype,
                                      "amount": amount, "count": count})
            breakdown.sort(key=lambda x: x["amount"], reverse=True)
        if ch["promo_costs"] > 0:
            breakdown.append({"label": "Promotional Costs", "amount": ch["promo_costs"]})
        layer2_channels.append({
            "channel_name": name, "channel_type": ch["channel_type"],
            "value": ch["layer_2"], "previous_value": ch["layer_1"],
            "breakdown": breakdown
        })
    layers.append({
        "id": 2, "label": "After Trade Deductions",
        "subtitle": "Short ships, promo billbacks, slotting fees",
        "channels": layer2_channels
    })

    # Layer 3: After Compliance Fines
    layer3_channels = []
    for ch in channel_data:
        name = ch["channel_name"]
        breakdown = []
        if name in DEDUCTIONS:
            for dtype in COMPLIANCE_TYPES:
                amount, count = DEDUCTIONS[name].get(dtype, (0, 0))
                if amount > 0:
                    breakdown.append({"label": TYPE_LABELS[dtype], "type": dtype,
                                      "amount": amount, "count": count})
            breakdown.sort(key=lambda x: x["amount"], reverse=True)
        layer3_channels.append({
            "channel_name": name, "channel_type": ch["channel_type"],
            "value": ch["layer_3"], "previous_value": ch["layer_2"],
            "breakdown": breakdown
        })
    layers.append({
        "id": 3, "label": "After Compliance Fines",
        "subtitle": "Label fines, pallet fines, late delivery penalties",
        "channels": layer3_channels
    })

    layers.append({
        "id": 4, "label": "Net Contribution",
        "subtitle": "What the channel actually earns",
        "channels": [
            {"channel_name": ch["channel_name"], "channel_type": ch["channel_type"],
             "value": ch["layer_4"], "previous_value": ch["layer_3"],
             "breakdown": [{"label": "Operational Overhead", "amount": ch["operational_overhead"]}]
             if ch["operational_overhead"] > 0 else []}
            for ch in channel_data
        ]
    })

    return layers


def generate_trends():
    """Generate quarterly trends using mart COGS ratios applied to quarterly revenue."""
    trends = []
    for quarter_key in sorted(QUARTERLY_REVENUE.keys()):
        quarter_label = QUARTER_LABELS[quarter_key]
        quarter_data = []

        for name in CHANNEL_ORDER:
            revenue = QUARTERLY_REVENUE[quarter_key].get(name, 0)
            deductions = QUARTERLY_DEDUCTIONS[quarter_key].get(name, 0)
            cogs = round(revenue * COGS_RATIOS[name], 2)
            contribution = round(revenue - cogs - deductions, 2)
            margin_pct = round((contribution / revenue) * 100, 1) if revenue > 0 else 0

            quarter_data.append({
                "channel_name": name,
                "channel_type": CHANNEL_TYPES[name],
                "revenue": round(revenue, 2),
                "cogs": cogs,
                "deductions": round(deductions, 2),
                "contribution": contribution,
                "margin_pct": margin_pct,
            })

        trends.append({"quarter": quarter_label, "channels": quarter_data})

    return trends


def main():
    out_dir = Path(__file__).parent.parent / "src" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    live_rev, _ = fetch_live_channel_data()
    if live_rev:
        matched = 0
        for name in CHANNEL_ORDER:
            if name in live_rev:
                FISCAL_REVENUE[name] = live_rev[name]
                matched += 1
        print(f"Revenue: live from Postgres ({matched}/{len(CHANNEL_ORDER)} channels matched)")
    else:
        print("Revenue: using hardcoded snapshot (Postgres unavailable)")

    channel_data = compute_channel_data()

    channels = generate_channels(channel_data)
    with open(out_dir / "channels.json", "w") as f:
        json.dump(channels, f, indent=2)
    print(f"channels.json: {len(channels)} channels")

    layers = generate_layers(channel_data)
    with open(out_dir / "layers.json", "w") as f:
        json.dump(layers, f, indent=2)
    print(f"layers.json: {len(layers)} layers")

    trends = generate_trends()
    with open(out_dir / "trends.json", "w") as f:
        json.dump(trends, f, indent=2)
    print(f"trends.json: {len(trends)} quarters")

    total_revenue = sum(ch["gross_revenue"] for ch in channel_data)
    total_contribution = sum(ch["layer_4"] for ch in channel_data)
    source = "live Postgres" if live_rev else "hardcoded snapshot"
    print(f"\nChannel profitability ({source}):")
    print(f"  Total revenue: ${total_revenue:,.2f}")
    print(f"  Total contribution: ${total_contribution:,.2f}")
    print(f"  Overall margin: {(total_contribution/total_revenue)*100:.1f}%")

    for ch in channel_data:
        margin = (ch["layer_4"] / ch["gross_revenue"]) * 100
        print(f"  {ch['channel_name']:20s}: ${ch['gross_revenue']:>12,.2f} -> ${ch['layer_4']:>10,.2f} ({margin:.1f}%)")


if __name__ == "__main__":
    main()
