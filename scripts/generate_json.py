"""
Generate channels.json, layers.json, and trends.json.
Revenue and COGS from Postgres (mart_channel_contribution) when available,
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

# === FISCAL YEAR DATA (Apr 2025 – Mar 2026) ===
# Revenue from fct_retailer_orders WHERE order_date >= '2025-04-01' AND < '2026-04-01'
# COGS computed using mart COGS ratios (industry-norm) applied to fiscal year revenue
# Deductions from fct_retailer_deductions WHERE deduction_date in same range
# DTC estimated as 1/3 of 3-year mart total (not in fct_retailer_orders)

# COGS ratios from mart_channel_contribution (realistic industry norms)
COGS_RATIOS = {
    "Walmart": 0.5871, "UNFI": 0.6026, "KeHE": 0.5965,
    "Whole Foods": 0.5308, "Costco": 0.5581, "DTC": 0.2677,
    "Green Basket Market": 0.5080, "Southside Grocers": 0.5088,
    "Prairie Provisions": 0.5073, "Mountain Pantry Co": 0.5099,
    "Harbor Fresh": 0.5088,
}

# Fiscal year revenue by channel
FISCAL_REVENUE = {
    "Walmart": 9726097.38, "UNFI": 3812244.36, "KeHE": 2608189.44,
    "Whole Foods": 2353212.00, "Costco": 2330023.50,
    "DTC": 1305223.00,  # estimated: 3,915,668 / 3
    "Southside Grocers": 511662.06, "Green Basket Market": 499933.74,
    "Prairie Provisions": 350986.32, "Mountain Pantry Co": 223895.82,
    "Harbor Fresh": 194193.30,
}

# Fiscal year deduction breakdowns (from fct_retailer_deductions, date-filtered)
DEDUCTIONS = {
    "Walmart": {
        "promo_billback": (836799.53, 555), "vague": (456045.68, 335),
        "short_ship": (154970.49, 606), "slotting": (18841.62, 2),
        "label_fine": (79033.00, 277), "spoilage": (160192.30, 124),
        "damaged": (20372.51, 22), "pallet_fine": (14247.56, 69), "late_delivery": (36797.22, 143),
    },
    "UNFI": {
        "promo_billback": (243298.79, 251), "vague": (171813.24, 143),
        "short_ship": (5237.90, 40), "slotting": (1008.28, 1),
        "label_fine": (8485.43, 19), "spoilage": (166715.07, 205),
        "damaged": (10843.67, 19), "pallet_fine": (91.86, 1), "late_delivery": (8250.00, 24),
    },
    "KeHE": {
        "promo_billback": (181090.40, 195), "vague": (127321.87, 101),
        "short_ship": (4110.78, 34), "slotting": (614.49, 1),
        "label_fine": (2869.09, 15), "spoilage": (98348.07, 139),
        "damaged": (4443.82, 10), "pallet_fine": (772.64, 5), "late_delivery": (926.30, 10),
    },
    "Whole Foods": {
        "promo_billback": (169853.76, 274), "vague": (235204.19, 179),
        "short_ship": (11542.65, 74), "slotting": (9659.06, 2),
        "label_fine": (7597.73, 45), "spoilage": (41385.56, 78),
        "damaged": (9150.49, 24), "pallet_fine": (3033.68, 20), "late_delivery": (7263.00, 99),
    },
    "Costco": {
        "promo_billback": (157997.84, 30), "vague": (9993.77, 15),
        "short_ship": (24619.95, 31), "slotting": (13747.95, 1),
        "label_fine": (2820.27, 13), "spoilage": (47347.87, 10),
        "damaged": (9090.70, 3), "pallet_fine": (387.80, 2), "late_delivery": (12226.53, 16),
    },
    "Green Basket Market": {
        "promo_billback": (30179.17, 73), "vague": (56312.48, 41),
        "short_ship": (2911.06, 19), "slotting": (1330.85, 1),
        "label_fine": (916.57, 8), "spoilage": (5128.75, 19),
        "damaged": (1039.25, 5), "pallet_fine": (597.90, 4), "late_delivery": (936.16, 20),
    },
    "Southside Grocers": {
        "promo_billback": (19272.54, 49), "vague": (54074.76, 31),
        "short_ship": (2458.84, 19), "slotting": (1588.02, 1),
        "label_fine": (2115.71, 13), "spoilage": (2904.77, 11),
        "damaged": (91.67, 1), "pallet_fine": (151.50, 1), "late_delivery": (403.11, 8),
    },
    "Prairie Provisions": {
        "promo_billback": (11677.75, 27), "vague": (25537.50, 24),
        "short_ship": (1450.52, 11), "slotting": (987.32, 1),
        "label_fine": (592.41, 4), "spoilage": (2948.24, 9),
        "damaged": (790.69, 3), "pallet_fine": (339.20, 2), "late_delivery": (577.57, 13),
    },
    "Mountain Pantry Co": {
        "promo_billback": (5743.61, 23), "vague": (24161.76, 24),
        "short_ship": (1597.65, 12), "slotting": (0, 0),
        "label_fine": (1404.67, 7), "spoilage": (1576.19, 6),
        "damaged": (491.34, 3), "pallet_fine": (190.43, 1), "late_delivery": (593.28, 15),
    },
    "Harbor Fresh": {
        "promo_billback": (4291.02, 13), "vague": (17433.38, 10),
        "short_ship": (751.19, 5), "slotting": (988.10, 1),
        "label_fine": (581.58, 4), "spoilage": (483.31, 3),
        "damaged": (0, 0), "pallet_fine": (364.16, 2), "late_delivery": (150.47, 5),
    },
}

# Disputes and operational overhead (fiscal year)
DISPUTE_DATA = {
    "Walmart": {"disputes": 1209, "events": 2133, "hours": 5175.94},
    "UNFI": {"disputes": 322, "events": 703, "hours": 1400.60},
    "Whole Foods": {"disputes": 239, "events": 795, "hours": 1024.34},
    "KeHE": {"disputes": 204, "events": 510, "hours": 851.38},
    "Green Basket Market": {"disputes": 60, "events": 190, "hours": 266.83},
    "Costco": {"disputes": 46, "events": 121, "hours": 191.59},
    "Southside Grocers": {"disputes": 34, "events": 134, "hours": 141.17},
    "Mountain Pantry Co": {"disputes": 21, "events": 91, "hours": 94.18},
    "Prairie Provisions": {"disputes": 20, "events": 94, "hours": 83.24},
    "Harbor Fresh": {"disputes": 8, "events": 43, "hours": 35.18},
    "DTC": {"disputes": 0, "events": 0, "hours": 0},
}

OVERHEAD_RATE = 35.00  # $/hr fully loaded
PROMO_COSTS_ANNUAL = {
    "Walmart": 1613.00, "UNFI": 444.00, "KeHE": 266.00,
    "Whole Foods": 1140.00, "Costco": 2220.00, "DTC": 0,
    "Green Basket Market": 538.00, "Southside Grocers": 538.00,
    "Prairie Provisions": 538.00, "Mountain Pantry Co": 538.00,
    "Harbor Fresh": 538.00,
}

CHANNEL_IDS = {
    "Walmart": "walmart", "UNFI": "unfi", "KeHE": "kehe",
    "Whole Foods": "whole_foods", "Costco": "costco", "DTC": "DTC",
    "Green Basket Market": "green_basket_market",
    "Southside Grocers": "southside_grocers",
    "Prairie Provisions": "prairie_provisions",
    "Mountain Pantry Co": "mountain_pantry_co",
    "Harbor Fresh": "harbor_fresh",
}

CHANNEL_TYPES = {
    "Walmart": "retailer", "UNFI": "distributor", "KeHE": "distributor",
    "Whole Foods": "retailer", "Costco": "retailer", "DTC": "DTC",
    "Green Basket Market": "retailer", "Southside Grocers": "retailer",
    "Prairie Provisions": "retailer", "Mountain Pantry Co": "retailer",
    "Harbor Fresh": "retailer",
}

# Channel order (by revenue descending)
CHANNEL_ORDER = [
    "Walmart", "UNFI", "KeHE", "Whole Foods", "Costco", "DTC",
    "Southside Grocers", "Green Basket Market", "Prairie Provisions",
    "Mountain Pantry Co", "Harbor Fresh",
]

TRADE_TYPES = ["promo_billback", "vague", "short_ship", "slotting"]
COMPLIANCE_TYPES = ["label_fine", "spoilage", "damaged", "pallet_fine", "late_delivery"]

TYPE_LABELS = {
    "promo_billback": "Promo Billback", "vague": "Unclassified",
    "short_ship": "Short Ship", "slotting": "Slotting Fees",
    "label_fine": "Label Fines", "spoilage": "Spoilage",
    "damaged": "Damaged Goods", "pallet_fine": "Pallet Fines",
    "late_delivery": "Late Delivery",
}

# === QUARTERLY DATA for trends (Q1 2025 through Q1 2026) ===
QUARTERLY_REVENUE = {
    "2025-01-01": {"Walmart": 2156344.86, "UNFI": 694306.56, "KeHE": 604224.96, "Whole Foods": 557391.48, "Costco": 409768.08, "Green Basket Market": 123493.08, "Southside Grocers": 84292.74, "Prairie Provisions": 51250.02, "Harbor Fresh": 39783.24, "Mountain Pantry Co": 33109.86},
    "2025-04-01": {"Walmart": 2236839.84, "UNFI": 936403.32, "KeHE": 720903.30, "Costco": 695264.82, "Whole Foods": 652835.64, "Green Basket Market": 119931.84, "Southside Grocers": 112769.16, "Prairie Provisions": 76799.46, "Mountain Pantry Co": 50787.84, "Harbor Fresh": 38879.82},
    "2025-07-01": {"Walmart": 2487026.10, "UNFI": 1068704.22, "Costco": 753563.58, "KeHE": 622640.76, "Whole Foods": 504766.68, "Southside Grocers": 107336.34, "Prairie Provisions": 101361.54, "Green Basket Market": 99415.44, "Mountain Pantry Co": 63952.08, "Harbor Fresh": 52529.34},
    "2025-10-01": {"Walmart": 2991514.02, "UNFI": 1124817.18, "KeHE": 696920.70, "Whole Foods": 687313.68, "Costco": 473088.84, "Southside Grocers": 180504.24, "Green Basket Market": 174685.92, "Prairie Provisions": 94248.90, "Mountain Pantry Co": 69150.54, "Harbor Fresh": 56051.22},
    "2026-01-01": {"Walmart": 2010717.42, "UNFI": 682319.64, "KeHE": 567724.68, "Whole Foods": 508296.00, "Costco": 408106.26, "Southside Grocers": 111052.32, "Green Basket Market": 105900.54, "Prairie Provisions": 78576.42, "Harbor Fresh": 46732.92, "Mountain Pantry Co": 40005.36},
}

QUARTERLY_DEDUCTIONS = {
    "2025-01-01": {"Walmart": 469168.28, "UNFI": 118979.89, "Whole Foods": 93780.18, "KeHE": 83549.25, "Costco": 76711.33, "Southside Grocers": 18582.65, "Green Basket Market": 18606.29, "Harbor Fresh": 11746.41, "Prairie Provisions": 2755.30, "Mountain Pantry Co": 5750.49},
    "2025-04-01": {"Walmart": 424417.13, "UNFI": 134301.21, "Whole Foods": 140907.53, "KeHE": 127103.23, "Costco": 39407.93, "Southside Grocers": 19977.43, "Green Basket Market": 26638.12, "Harbor Fresh": 8301.80, "Prairie Provisions": 8500.81, "Mountain Pantry Co": 7509.29},
    "2025-07-01": {"Walmart": 406723.83, "UNFI": 201729.49, "Whole Foods": 116914.28, "KeHE": 91922.16, "Costco": 81157.50, "Southside Grocers": 11646.41, "Green Basket Market": 22021.87, "Harbor Fresh": 3309.95, "Prairie Provisions": 18043.96, "Mountain Pantry Co": 11773.90},
    "2025-10-01": {"Walmart": 517654.75, "UNFI": 159995.85, "Whole Foods": 135413.19, "KeHE": 105839.99, "Costco": 101144.06, "Southside Grocers": 28886.26, "Green Basket Market": 27902.77, "Harbor Fresh": 10125.99, "Prairie Provisions": 7356.13, "Mountain Pantry Co": 9538.58},
    "2026-01-01": {"Walmart": 428504.20, "UNFI": 119717.69, "Whole Foods": 101455.12, "KeHE": 95632.08, "Costco": 56523.19, "Southside Grocers": 22550.82, "Green Basket Market": 22789.43, "Harbor Fresh": 3305.47, "Prairie Provisions": 11000.30, "Mountain Pantry Co": 6937.16},
}

QUARTER_LABELS = {
    "2025-01-01": "Q1 2025", "2025-04-01": "Q2 2025",
    "2025-07-01": "Q3 2025", "2025-10-01": "Q4 2025",
    "2026-01-01": "Q1 2026",
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
