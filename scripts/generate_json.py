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
# Extracted from Postgres 2026-05-22. Used as offline fallback when Postgres
# is unavailable. Live path queries fact tables directly (no date filter).

COGS_RATIOS = {
    "UNFI": 0.0852, "DPI Northwest": 0.0756, "KeHE": 0.0846,
    "DTC": 0.1741,
    "Sprouts": 0.1494, "Whole Foods": 0.1406, "Regional Group": 0.1551,
    "Kroger": 0.1592, "Walmart": 0.1648, "Costco": 0.1687,
}

FISCAL_REVENUE = {
    "UNFI": 10450336.32, "DPI Northwest": 5602560.48, "KeHE": 8405927.76,
    "DTC": 572510.27,
    "Sprouts": 8106459.60, "Whole Foods": 9705060.00, "Regional Group": 6075642.72,
    "Kroger": 10550521.68, "Walmart": 10894584.00, "Costco": 6467230.08,
}

DEDUCTIONS = {
    "UNFI": {
        "promo_billback": (28299.77, 188), "pricing_error": (27958.68, 173),
        "short_ship": (30716.69, 184), "damaged": (32656.85, 191),
        "late_delivery": (26295.48, 166),
    },
    "DPI Northwest": {
        "promo_billback": (13167.27, 83), "pricing_error": (18278.79, 117),
        "short_ship": (16644.98, 94), "damaged": (13288.84, 88),
        "late_delivery": (12959.84, 82),
    },
    "KeHE": {
        "promo_billback": (23856.40, 137), "pricing_error": (22711.33, 155),
        "short_ship": (21105.60, 131), "damaged": (21741.93, 144),
        "late_delivery": (27900.75, 161),
    },
    "Sprouts": {
        "promo_billback": (26076.71, 268), "pricing_error": (26161.47, 256),
        "short_ship": (23103.29, 230), "slotting": (26675.91, 266),
        "label_fine": (23496.94, 228), "spoilage": (23462.67, 239),
        "damaged": (22621.38, 230), "pallet_fine": (23168.62, 238), "late_delivery": (22181.71, 233),
    },
    "Whole Foods": {
        "promo_billback": (24508.63, 235), "pricing_error": (23777.81, 226),
        "short_ship": (26259.37, 266), "slotting": (27080.04, 266),
        "label_fine": (28492.83, 263), "spoilage": (29837.61, 276),
        "damaged": (28951.41, 243), "pallet_fine": (29092.92, 281), "late_delivery": (28453.72, 269),
    },
    "Regional Group": {
        "promo_billback": (16844.42, 184), "pricing_error": (14670.89, 160),
        "short_ship": (15840.38, 178), "slotting": (17457.95, 186),
        "label_fine": (15393.01, 167), "spoilage": (16468.22, 178),
        "damaged": (17552.71, 198), "pallet_fine": (16414.43, 179), "late_delivery": (18217.23, 184),
    },
    "Kroger": {
        "promo_billback": (25484.51, 290), "pricing_error": (28794.63, 322),
        "short_ship": (28839.58, 303), "slotting": (28396.85, 312),
        "label_fine": (29581.42, 316), "spoilage": (29956.72, 317),
        "damaged": (30879.45, 332), "pallet_fine": (29759.91, 298), "late_delivery": (31608.55, 335),
    },
    "Walmart": {
        "promo_billback": (29692.07, 324), "pricing_error": (32355.88, 344),
        "short_ship": (33971.93, 377), "slotting": (25739.41, 292),
        "label_fine": (29052.28, 327), "spoilage": (28771.96, 319),
        "damaged": (30202.97, 316), "pallet_fine": (29533.79, 323), "late_delivery": (29418.05, 306),
    },
    "Costco": {
        "promo_billback": (19679.80, 229), "pricing_error": (18559.07, 213),
        "short_ship": (16322.63, 200), "slotting": (18544.95, 209),
        "label_fine": (18721.02, 208), "spoilage": (20324.60, 221),
        "damaged": (17656.49, 217), "pallet_fine": (18244.18, 215), "late_delivery": (19348.69, 212),
    },
}

DISPUTE_DATA = {
    "Walmart": {"disputes": 1143, "events": 2928, "hours": 2361.4},
    "Kroger": {"disputes": 1099, "events": 2825, "hours": 2255.8},
    "Whole Foods": {"disputes": 945, "events": 2325, "hours": 2038.8},
    "Sprouts": {"disputes": 862, "events": 2188, "hours": 1909.1},
    "Costco": {"disputes": 743, "events": 1924, "hours": 1597.3},
    "Regional Group": {"disputes": 597, "events": 1614, "hours": 1231.1},
    "UNFI": {"disputes": 315, "events": 902, "hours": 497.4},
    "KeHE": {"disputes": 268, "events": 728, "hours": 442.6},
    "DPI Northwest": {"disputes": 169, "events": 464, "hours": 270.5},
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
    "2024-01-01": {"UNFI": 740038.56, "DPI Northwest": 337883.04, "KeHE": 604097.76, "DTC": 38338.66, "Sprouts": 537777.84, "Whole Foods": 642028.56, "Regional Group": 388449.12, "Kroger": 710033.76, "Walmart": 763554.00, "Costco": 433693.44},
    "2024-04-01": {"UNFI": 773337.60, "DPI Northwest": 480131.52, "KeHE": 599990.88, "DTC": 47597.63, "Sprouts": 671741.76, "Whole Foods": 828656.40, "Regional Group": 458830.56, "Kroger": 775925.52, "Walmart": 734754.00, "Costco": 531711.36},
    "2024-07-01": {"UNFI": 820043.04, "DPI Northwest": 439206.24, "KeHE": 601840.08, "DTC": 46882.85, "Sprouts": 614320.08, "Whole Foods": 734439.36, "Regional Group": 474634.56, "Kroger": 796722.48, "Walmart": 884832.00, "Costco": 520974.72},
    "2024-10-01": {"UNFI": 1158884.16, "DPI Northwest": 583191.84, "KeHE": 864382.32, "DTC": 61057.42, "Sprouts": 882586.08, "Whole Foods": 990607.20, "Regional Group": 593567.04, "Kroger": 1084892.88, "Walmart": 1158972.00, "Costco": 712874.88},
    "2025-01-01": {"UNFI": 803893.92, "DPI Northwest": 367007.52, "KeHE": 622286.16, "DTC": 39586.25, "Sprouts": 594437.04, "Whole Foods": 618673.68, "Regional Group": 431552.40, "Kroger": 728585.76, "Walmart": 746304.00, "Costco": 452695.68},
    "2025-04-01": {"UNFI": 789677.52, "DPI Northwest": 463061.28, "KeHE": 592820.40, "DTC": 48098.82, "Sprouts": 681847.20, "Whole Foods": 728794.80, "Regional Group": 500438.16, "Kroger": 891440.40, "Walmart": 852426.00, "Costco": 537264.00},
    "2025-07-01": {"UNFI": 842655.36, "DPI Northwest": 491182.56, "KeHE": 696657.12, "DTC": 45839.43, "Sprouts": 670198.08, "Whole Foods": 842059.68, "Regional Group": 515454.24, "Kroger": 841389.12, "Walmart": 946008.00, "Costco": 502686.72},
    "2025-10-01": {"UNFI": 1296819.36, "DPI Northwest": 636086.88, "KeHE": 924224.64, "DTC": 56054.77, "Sprouts": 884634.96, "Whole Foods": 1069252.32, "Regional Group": 647198.64, "Kroger": 1154401.44, "Walmart": 1109310.00, "Costco": 647331.84},
    "2026-01-01": {"UNFI": 706168.56, "DPI Northwest": 327534.24, "KeHE": 504550.08, "DTC": 35748.25, "Sprouts": 551670.24, "Whole Foods": 580649.28, "Regional Group": 425413.92, "Kroger": 706677.84, "Walmart": 747438.00, "Costco": 426055.68},
    "2026-04-01": {"UNFI": 808723.68, "DPI Northwest": 440045.76, "KeHE": 702839.52, "DTC": 42778.60, "Sprouts": 529746.00, "Whole Foods": 791415.36, "Regional Group": 460960.32, "Kroger": 796644.96, "Walmart": 811806.00, "Costco": 518204.16},
    "2026-07-01": {"UNFI": 708474.24, "DPI Northwest": 475247.52, "KeHE": 708315.36, "DTC": 45076.15, "Sprouts": 671315.04, "Whole Foods": 805232.88, "Regional Group": 525874.56, "Kroger": 852390.48, "Walmart": 934014.00, "Costco": 454170.24},
    "2026-10-01": {"UNFI": 980221.20, "DPI Northwest": 547789.44, "KeHE": 962036.64, "DTC": 63895.48, "Sprouts": 797519.28, "Whole Foods": 1041038.40, "Regional Group": 639624.48, "Kroger": 1179229.92, "Walmart": 1176924.00, "Costco": 706170.24},
    "2027-01-01": {"UNFI": 21399.12, "DPI Northwest": 14192.64, "KeHE": 21886.80, "DTC": 1555.96, "Sprouts": 18666.00, "Whole Foods": 32212.08, "Regional Group": 13644.72, "Kroger": 32187.12, "Walmart": 28242.00, "Costco": 23397.12},
}

QUARTERLY_DEDUCTIONS = {
    "2024-01-01": {"UNFI": 6015.40, "KeHE": 5471.28, "DPI Northwest": 2526.64, "Sprouts": 7486.57, "Whole Foods": 10722.08, "Regional Group": 4019.01, "Kroger": 11484.64, "Walmart": 11580.06, "Costco": 4807.11},
    "2024-04-01": {"UNFI": 12916.17, "KeHE": 10630.81, "DPI Northwest": 6617.83, "Sprouts": 16885.52, "Whole Foods": 20518.17, "Regional Group": 10410.60, "Kroger": 18383.05, "Walmart": 21547.53, "Costco": 13278.67},
    "2024-07-01": {"UNFI": 11219.99, "KeHE": 8570.47, "DPI Northwest": 8664.28, "Sprouts": 16759.33, "Whole Foods": 21015.36, "Regional Group": 12601.80, "Kroger": 23011.24, "Walmart": 21754.29, "Costco": 10737.12},
    "2024-10-01": {"UNFI": 14384.02, "KeHE": 10382.72, "DPI Northwest": 9291.60, "Sprouts": 20829.44, "Whole Foods": 19825.13, "Regional Group": 14958.76, "Kroger": 27611.10, "Walmart": 27763.83, "Costco": 15566.04},
    "2025-01-01": {"UNFI": 18045.26, "KeHE": 9835.88, "DPI Northwest": 4612.08, "Sprouts": 20990.19, "Whole Foods": 21606.86, "Regional Group": 13592.55, "Kroger": 23193.19, "Walmart": 25482.92, "Costco": 16174.82},
    "2025-04-01": {"UNFI": 12456.01, "KeHE": 8357.20, "DPI Northwest": 6024.18, "Sprouts": 22608.91, "Whole Foods": 18793.65, "Regional Group": 13604.39, "Kroger": 22828.44, "Walmart": 18081.78, "Costco": 15332.12},
    "2025-07-01": {"UNFI": 9688.02, "KeHE": 10549.09, "DPI Northwest": 7319.38, "Sprouts": 16522.66, "Whole Foods": 21958.74, "Regional Group": 13884.05, "Kroger": 22186.70, "Walmart": 22874.51, "Costco": 12132.89},
    "2025-10-01": {"UNFI": 12273.23, "KeHE": 13659.71, "DPI Northwest": 4148.39, "Sprouts": 18725.14, "Whole Foods": 23697.00, "Regional Group": 14178.28, "Kroger": 23931.30, "Walmart": 27688.39, "Costco": 20131.86},
    "2026-01-01": {"UNFI": 16293.22, "KeHE": 9162.30, "DPI Northwest": 5913.25, "Sprouts": 18301.33, "Whole Foods": 21394.37, "Regional Group": 13050.76, "Kroger": 24643.55, "Walmart": 23716.52, "Costco": 13132.65},
    "2026-04-01": {"UNFI": 10002.84, "KeHE": 9237.43, "DPI Northwest": 4910.64, "Sprouts": 18305.46, "Whole Foods": 18262.34, "Regional Group": 12617.70, "Kroger": 19903.34, "Walmart": 18357.65, "Costco": 12529.18},
    "2026-07-01": {"UNFI": 8997.35, "KeHE": 9342.50, "DPI Northwest": 7181.19, "Sprouts": 17421.43, "Whole Foods": 25119.22, "Regional Group": 12512.88, "Kroger": 21367.60, "Walmart": 23822.39, "Costco": 15560.92},
    "2026-10-01": {"UNFI": 13410.14, "KeHE": 11748.08, "DPI Northwest": 6958.50, "Sprouts": 21790.33, "Whole Foods": 23074.70, "Regional Group": 12802.80, "Kroger": 23838.43, "Walmart": 25783.86, "Costco": 17605.83},
    "2027-01-01": {"UNFI": 225.82, "DPI Northwest": 171.76, "KeHE": 368.54, "DTC": 0, "Sprouts": 322.39, "Whole Foods": 466.72, "Regional Group": 625.66, "Kroger": 919.04, "Walmart": 284.61, "Costco": 412.22},
}

QUARTER_LABELS = {
    "2024-01-01": "Q1 2024", "2024-04-01": "Q2 2024",
    "2024-07-01": "Q3 2024", "2024-10-01": "Q4 2024",
    "2025-01-01": "Q1 2025", "2025-04-01": "Q2 2025",
    "2025-07-01": "Q3 2025", "2025-10-01": "Q4 2025",
    "2026-01-01": "Q1 2026", "2026-04-01": "Q2 2026",
    "2026-07-01": "Q3 2026", "2026-10-01": "Q4 2026",
    "2027-01-01": "Q1 2027",
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
