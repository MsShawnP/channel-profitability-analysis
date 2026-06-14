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

# === SNAPSHOT DATA (full dataset, all dates) ===
# Extracted from Postgres 2026-06-13. Used as offline fallback when Postgres
# is unavailable. Live path queries fact tables directly (no date filter).

# Catalog-true ratios: SUM(units ordered x raw.sku_costs.cogs_per_unit) /
# invoiced revenue per channel, certified replica 2026-06-12. Distributors
# buy the same units at lower prices, so their COGS ratio is HIGHER than
# retail. The previous hand-entered ratios (7.6-16.9% wholesale) were ~3x
# low and inverted.
COGS_RATIOS = {
    "UNFI": 0.5349, "DPI Northwest": 0.5453, "KeHE": 0.5233,
    "DTC": 0.1740,
    "Sprouts": 0.4387, "Whole Foods": 0.4163, "Regional Group": 0.4634,
    "Kroger": 0.4637, "Walmart": 0.4818, "Costco": 0.5015,
}

FISCAL_REVENUE = {
    "UNFI": 9645587.52, "DPI Northwest": 5428616.16, "KeHE": 8864325.12,
    "DTC": 566125.33,
    "Sprouts": 8259744.72, "Whole Foods": 9832363.68, "Regional Group": 6080585.28,
    "Kroger": 10557622.80, "Walmart": 10789650.00, "Costco": 6608810.88,
}

DEDUCTIONS = {
    "UNFI": {
        "promo_billback": (24376.00, 155), "pricing_error": (30863.47, 193),
        "short_ship": (28502.62, 373), "damaged": (31234.08, 182),
        "late_delivery": (7314.02, 110),
    },
    "DPI Northwest": {
        "promo_billback": (13959.28, 98), "pricing_error": (12582.52, 94),
        "short_ship": (12192.12, 177), "damaged": (10765.70, 75),
        "late_delivery": (4301.58, 67),
    },
    "KeHE": {
        "promo_billback": (24720.73, 144), "pricing_error": (23005.35, 145),
        "short_ship": (27335.78, 342), "damaged": (24907.74, 155),
        "late_delivery": (7628.59, 113),
    },
    "Sprouts": {
        "promo_billback": (23189.33, 243), "pricing_error": (25973.04, 246),
        "short_ship": (34080.89, 1160), "slotting": (24824.62, 237),
        "label_fine": (24681.22, 253), "spoilage": (22940.62, 233),
        "damaged": (24226.48, 237), "pallet_fine": (23477.52, 249), "late_delivery": (1063.79, 30),
    },
    "Whole Foods": {
        "promo_billback": (28091.69, 274), "pricing_error": (30531.00, 272),
        "short_ship": (39164.30, 1287), "slotting": (27032.97, 262),
        "label_fine": (26632.49, 254), "spoilage": (27111.99, 264),
        "damaged": (32695.33, 296), "pallet_fine": (26214.92, 272), "late_delivery": (989.15, 26),
    },
    "Regional Group": {
        "promo_billback": (16491.49, 180), "pricing_error": (16543.22, 166),
        "short_ship": (20250.33, 702), "slotting": (18755.75, 179),
        "label_fine": (15523.65, 171), "spoilage": (16904.28, 183),
        "damaged": (16867.14, 175), "pallet_fine": (15422.35, 177),
    },
    "Kroger": {
        "promo_billback": (29274.87, 313), "pricing_error": (26708.14, 287),
        "short_ship": (64272.92, 2140), "slotting": (30382.15, 327),
        "label_fine": (29901.25, 317), "spoilage": (29269.37, 314),
        "damaged": (28400.02, 303), "pallet_fine": (29805.47, 311), "late_delivery": (1392.98, 43),
    },
    "Walmart": {
        "promo_billback": (27537.41, 315), "pricing_error": (29768.47, 333),
        "short_ship": (71894.73, 2515), "slotting": (30050.41, 329),
        "label_fine": (28360.03, 316), "spoilage": (33291.04, 346),
        "damaged": (32433.19, 340), "pallet_fine": (31049.82, 318), "late_delivery": (4475.16, 131),
    },
    "Costco": {
        "promo_billback": (20497.41, 225), "pricing_error": (18943.43, 210),
        "short_ship": (33595.43, 1159), "slotting": (18483.02, 212),
        "label_fine": (16992.60, 199), "spoilage": (19073.70, 233),
        "damaged": (18964.59, 207), "pallet_fine": (19385.33, 231),
    },
}

DISPUTE_DATA = {
    "Walmart": {"disputes": 1912, "events": 4943, "hours": 3586.21},
    "Kroger": {"disputes": 1717, "events": 4355, "hours": 3127.06},
    "Whole Foods": {"disputes": 1238, "events": 3207, "hours": 2217.38},
    "Sprouts": {"disputes": 1114, "events": 2888, "hours": 2058.90},
    "Costco": {"disputes": 1027, "events": 2676, "hours": 1859.57},
    "Regional Group": {"disputes": 748, "events": 1933, "hours": 1406.98},
    "UNFI": {"disputes": 406, "events": 1013, "hours": 738.01},
    "KeHE": {"disputes": 325, "events": 899, "hours": 608.66},
    "DPI Northwest": {"disputes": 195, "events": 511, "hours": 342.42},
    "DTC": {"disputes": 0, "events": 0, "hours": 0},
}

OVERHEAD_RATE = 35.00  # $/hr fully loaded
YEARS = 3  # FY2024–FY2026; snapshot constants are 3yr cumulative, JSON emits annual averages
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
    "DTC": "DTC",
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

# === QUARTERLY DATA for trends (Q1 2024 through Q4 2026) ===
QUARTERLY_REVENUE = {
    "2023-01-01": {"UNFI": 736379.76, "DPI Northwest": 330475.20, "KeHE": 604097.76, "DTC": 38036.80, "Sprouts": 530768.88, "Whole Foods": 631216.32, "Regional Group": 380916.48, "Kroger": 702533.76, "Walmart": 757692.00, "Costco": 429390.72},
    "2023-04-01": {"UNFI": 773676.72, "DPI Northwest": 487539.36, "KeHE": 599063.52, "DTC": 47071.02, "Sprouts": 666715.92, "Whole Foods": 833267.28, "Regional Group": 465517.20, "Kroger": 777931.44, "Walmart": 735012.00, "Costco": 529706.88},
    "2023-07-01": {"UNFI": 818175.60, "DPI Northwest": 439206.24, "KeHE": 598666.08, "DTC": 47151.09, "Sprouts": 620046.00, "Whole Foods": 734188.80, "Regional Group": 474628.32, "Kroger": 794873.04, "Walmart": 874746.00, "Costco": 524102.40},
    "2023-10-01": {"UNFI": 1083226.56, "DPI Northwest": 595752.96, "KeHE": 997982.88, "DTC": 57395.82, "Sprouts": 804500.64, "Whole Foods": 1086188.16, "Regional Group": 659103.84, "Kroger": 1158130.32, "Walmart": 1158528.00, "Costco": 693365.76},
    "2024-01-01": {"UNFI": 764571.60, "DPI Northwest": 337571.52, "KeHE": 640286.88, "DTC": 41793.19, "Sprouts": 604277.52, "Whole Foods": 660021.84, "Regional Group": 405015.60, "Kroger": 732306.96, "Walmart": 736404.00, "Costco": 414120.96},
    "2024-04-01": {"UNFI": 713710.56, "DPI Northwest": 453092.64, "KeHE": 716297.28, "DTC": 47414.13, "Sprouts": 627695.28, "Whole Foods": 781570.32, "Regional Group": 466826.40, "Kroger": 859376.88, "Walmart": 834786.00, "Costco": 530876.16},
    "2024-07-01": {"UNFI": 783793.20, "DPI Northwest": 500992.80, "KeHE": 702199.20, "DTC": 43143.72, "Sprouts": 666017.28, "Whole Foods": 826634.64, "Regional Group": 497460.72, "Kroger": 841364.88, "Walmart": 877194.00, "Costco": 533577.60},
    "2024-10-01": {"UNFI": 843865.92, "DPI Northwest": 545946.72, "KeHE": 947960.64, "DTC": 59159.58, "Sprouts": 940725.36, "Whole Foods": 1103853.36, "Regional Group": 649236.00, "Kroger": 1117475.76, "Walmart": 1229928.00, "Costco": 752290.56},
    "2025-01-01": {"UNFI": 639274.56, "DPI Northwest": 300680.16, "KeHE": 619940.16, "DTC": 37686.36, "Sprouts": 576412.08, "Whole Foods": 627978.96, "Regional Group": 406133.28, "Kroger": 784469.52, "Walmart": 689790.00, "Costco": 497306.88},
    "2025-04-01": {"UNFI": 704353.68, "DPI Northwest": 434718.24, "KeHE": 703010.64, "DTC": 43862.04, "Sprouts": 713106.48, "Whole Foods": 765715.44, "Regional Group": 491775.36, "Kroger": 859692.96, "Walmart": 838830.00, "Costco": 501287.04},
    "2025-07-01": {"UNFI": 808690.32, "DPI Northwest": 410625.60, "KeHE": 744493.44, "DTC": 41697.18, "Sprouts": 666447.84, "Whole Foods": 751898.64, "Regional Group": 457241.76, "Kroger": 763318.80, "Walmart": 813822.00, "Costco": 470718.72},
    "2025-10-01": {"UNFI": 957223.44, "DPI Northwest": 579406.08, "KeHE": 953955.36, "DTC": 59426.50, "Sprouts": 825065.52, "Whole Foods": 1010808.96, "Regional Group": 711400.32, "Kroger": 1143063.60, "Walmart": 1220400.00, "Costco": 706959.36},
    "2026-01-01": {"UNFI": 18645.60, "DPI Northwest": 12608.64, "KeHE": 36371.28, "DTC": 2287.90, "Sprouts": 17965.92, "Whole Foods": 19020.96, "Regional Group": 15330.00, "Kroger": 23084.88, "Walmart": 22518.00, "Costco": 25107.84},
}

QUARTERLY_DEDUCTIONS = {
    "2023-01-01": {"UNFI": 5447.46, "KeHE": 3724.40, "DPI Northwest": 2143.41, "Sprouts": 7099.12, "Whole Foods": 7333.10, "Regional Group": 3602.07, "Kroger": 9011.60, "Walmart": 11640.48, "Costco": 7102.46},
    "2023-04-01": {"UNFI": 10611.39, "KeHE": 6827.02, "DPI Northwest": 3502.62, "Sprouts": 17142.60, "Whole Foods": 16829.51, "Regional Group": 10746.80, "Kroger": 18609.37, "Walmart": 21349.20, "Costco": 13126.94},
    "2023-07-01": {"UNFI": 10611.71, "KeHE": 8570.57, "DPI Northwest": 5036.45, "Sprouts": 15146.24, "Whole Foods": 21046.43, "Regional Group": 11219.41, "Kroger": 22079.49, "Walmart": 22117.61, "Costco": 11941.49},
    "2023-10-01": {"UNFI": 12655.31, "KeHE": 13485.31, "DPI Northwest": 5525.62, "Sprouts": 20016.47, "Whole Foods": 21875.63, "Regional Group": 13459.12, "Kroger": 27284.68, "Walmart": 28218.81, "Costco": 17759.85},
    "2024-01-01": {"UNFI": 15381.64, "KeHE": 9771.78, "DPI Northwest": 5811.08, "Sprouts": 18402.39, "Whole Foods": 24240.22, "Regional Group": 12686.93, "Kroger": 26863.13, "Walmart": 26604.90, "Costco": 13224.59},
    "2024-04-01": {"UNFI": 10338.94, "KeHE": 8694.30, "DPI Northwest": 4041.98, "Sprouts": 16062.90, "Whole Foods": 18153.79, "Regional Group": 9594.31, "Kroger": 22169.15, "Walmart": 25909.12, "Costco": 13040.76},
    "2024-07-01": {"UNFI": 10294.44, "KeHE": 8973.80, "DPI Northwest": 3436.18, "Sprouts": 17889.49, "Whole Foods": 22117.01, "Regional Group": 11450.68, "Kroger": 21403.16, "Walmart": 22416.36, "Costco": 15139.47},
    "2024-10-01": {"UNFI": 8953.63, "KeHE": 10011.09, "DPI Northwest": 8429.99, "Sprouts": 20189.47, "Whole Foods": 23846.84, "Regional Group": 13583.03, "Kroger": 23680.18, "Walmart": 30297.26, "Costco": 14218.89},
    "2025-01-01": {"UNFI": 8826.22, "KeHE": 11061.55, "DPI Northwest": 3502.24, "Sprouts": 19478.48, "Whole Foods": 19187.65, "Regional Group": 15130.71, "Kroger": 27769.83, "Walmart": 26524.77, "Costco": 17449.75},
    "2025-04-01": {"UNFI": 8075.80, "KeHE": 8913.31, "DPI Northwest": 3857.31, "Sprouts": 16901.08, "Whole Foods": 18934.56, "Regional Group": 9780.97, "Kroger": 21531.21, "Walmart": 21935.87, "Costco": 12883.91},
    "2025-07-01": {"UNFI": 8190.04, "KeHE": 8050.50, "DPI Northwest": 3847.73, "Sprouts": 16737.16, "Whole Foods": 21645.01, "Regional Group": 11270.85, "Kroger": 23463.80, "Walmart": 21785.53, "Costco": 14708.27},
    "2025-10-01": {"UNFI": 12093.89, "KeHE": 8664.94, "DPI Northwest": 4398.03, "Sprouts": 18960.81, "Whole Foods": 21947.92, "Regional Group": 13714.33, "Kroger": 25283.86, "Walmart": 29446.72, "Costco": 15161.51},
    "2026-01-01": {"UNFI": 809.72, "KeHE": 849.62, "DPI Northwest": 268.56, "DTC": 0, "Sprouts": 431.30, "Whole Foods": 1306.17, "Regional Group": 519.00, "Kroger": 257.71, "Walmart": 613.63, "Costco": 177.62},
}

QUARTER_LABELS = {
    "2023-01-01": "Q1 2023", "2023-04-01": "Q2 2023",
    "2023-07-01": "Q3 2023", "2023-10-01": "Q4 2023",
    "2024-01-01": "Q1 2024", "2024-04-01": "Q2 2024",
    "2024-07-01": "Q3 2024", "2024-10-01": "Q4 2024",
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
    """Compute all derived values for each channel (annual averages)."""
    channels = []
    for name in CHANNEL_ORDER:
        revenue = round(FISCAL_REVENUE[name] / YEARS, 2)
        cogs = round(revenue * COGS_RATIOS[name], 2)
        gross_margin = round(revenue - cogs, 2)

        deductions = DEDUCTIONS.get(name, {})
        trade_ded = round(sum(deductions.get(t, (0, 0))[0] for t in TRADE_TYPES) / YEARS, 2)
        quality_fines = round(sum(deductions.get(t, (0, 0))[0] for t in ["label_fine", "spoilage", "damaged", "pallet_fine"]) / YEARS, 2)
        logistics_fines = round(deductions.get("late_delivery", (0, 0))[0] / YEARS, 2)
        total_deductions = round(trade_ded + quality_fines + logistics_fines, 2)

        promo = PROMO_COSTS_ANNUAL.get(name, 0)
        dispute = DISPUTE_DATA.get(name, {"disputes": 0, "events": 0, "hours": 0})
        disputes_annual = round(dispute["disputes"] / YEARS)
        events_annual = round(dispute["events"] / YEARS)
        hours_annual = round(dispute["hours"] / YEARS, 1)
        overhead = round(hours_annual * OVERHEAD_RATE, 2)

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
            "disputes_filed": disputes_annual,
            "total_deduction_events": events_annual,
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
                                      "amount": round(amount / YEARS, 2),
                                      "count": round(count / YEARS)})
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
                                      "amount": round(amount / YEARS, 2),
                                      "count": round(count / YEARS)})
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
    print(f"\nChannel profitability — annual averages, FY2024–FY2026 ({source}):")
    print(f"  Total revenue/yr: ${total_revenue:,.2f}")
    print(f"  Total contribution/yr: ${total_contribution:,.2f}")
    print(f"  Overall margin: {(total_contribution/total_revenue)*100:.1f}%")

    for ch in channel_data:
        margin = (ch["layer_4"] / ch["gross_revenue"]) * 100
        print(f"  {ch['channel_name']:20s}: ${ch['gross_revenue']:>12,.2f} -> ${ch['layer_4']:>10,.2f} ({margin:.1f}%)")


if __name__ == "__main__":
    main()
