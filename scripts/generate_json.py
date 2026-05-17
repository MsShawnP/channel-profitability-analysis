"""
Generate channels.json, layers.json, and trends.json from extracted database data.
Run from project root: python scripts/generate_json.py
"""
import json
from pathlib import Path

# === RAW DATA FROM mart_channel_contribution ===
# Ordered by gross_revenue DESC
MART_DATA = [
    {"channel_id": "walmart", "channel_name": "Walmart", "channel_type": "retailer",
     "gross_revenue": 29483483.94, "total_cogs": 17313349.14, "gross_margin": 12170134.80,
     "trade_deductions": 4166477.37, "quality_fines": 761705.63, "logistics_fines": 114773.66,
     "total_deductions": 5042956.66, "promo_costs": 4838.07, "operational_overhead": 551160.40,
     "disputes_filed": 3406, "total_deduction_events": 6123,
     "layer_1": 12170134.80, "layer_2": 7998819.36, "layer_3": 7122340.07, "layer_4": 6571179.67},
    {"channel_id": "unfi", "channel_name": "UNFI", "channel_type": "distributor",
     "gross_revenue": 10546700.10, "total_cogs": 6355374.06, "gross_margin": 4191326.04,
     "trade_deductions": 1238308.45, "quality_fines": 499469.20, "logistics_fines": 17750.00,
     "total_deductions": 1755527.65, "promo_costs": 1333.19, "operational_overhead": 152533.50,
     "disputes_filed": 901, "total_deduction_events": 1942,
     "layer_1": 4191326.04, "layer_2": 2951684.40, "layer_3": 2434465.20, "layer_4": 2281931.70},
    {"channel_id": "kehe", "channel_name": "KeHE", "channel_type": "distributor",
     "gross_revenue": 7847864.28, "total_cogs": 4681156.08, "gross_margin": 3166708.20,
     "trade_deductions": 859421.32, "quality_fines": 304961.58, "logistics_fines": 4502.12,
     "total_deductions": 1168885.02, "promo_costs": 798.14, "operational_overhead": 104364.75,
     "disputes_filed": 608, "total_deduction_events": 1449,
     "layer_1": 3166708.20, "layer_2": 2306488.74, "layer_3": 1997025.04, "layer_4": 1892660.29},
    {"channel_id": "whole_foods", "channel_name": "Whole Foods", "channel_type": "retailer",
     "gross_revenue": 7226400.24, "total_cogs": 3835456.26, "gross_margin": 3390943.98,
     "trade_deductions": 1112350.96, "quality_fines": 165338.22, "logistics_fines": 19846.26,
     "total_deductions": 1297535.44, "promo_costs": 3421.52, "operational_overhead": 122643.15,
     "disputes_filed": 642, "total_deduction_events": 2154,
     "layer_1": 3390943.98, "layer_2": 2275171.50, "layer_3": 2089987.02, "layer_4": 1967343.87},
    {"channel_id": "costco", "channel_name": "Costco", "channel_type": "retailer",
     "gross_revenue": 6135131.82, "total_cogs": 3424061.22, "gross_margin": 2711070.60,
     "trade_deductions": 618091.31, "quality_fines": 176013.68, "logistics_fines": 26548.54,
     "total_deductions": 820653.53, "promo_costs": 6659.28, "operational_overhead": 24082.80,
     "disputes_filed": 140, "total_deduction_events": 332,
     "layer_1": 2711070.60, "layer_2": 2086320.01, "layer_3": 1883757.79, "layer_4": 1859674.99},
    {"channel_id": "DTC", "channel_name": "DTC", "channel_type": "DTC",
     "gross_revenue": 3915668.20, "total_cogs": 1048419.01, "gross_margin": 2867249.19,
     "trade_deductions": 0, "quality_fines": 0, "logistics_fines": 0,
     "total_deductions": 0, "promo_costs": 0, "operational_overhead": 0,
     "disputes_filed": 0, "total_deduction_events": 0,
     "layer_1": 2867249.19, "layer_2": 2867249.19, "layer_3": 2867249.19, "layer_4": 2867249.19},
    {"channel_id": "green_basket_market", "channel_name": "Green Basket Market", "channel_type": "retailer",
     "gross_revenue": 1441118.88, "total_cogs": 732063.72, "gross_margin": 709055.16,
     "trade_deductions": 217850.83, "quality_fines": 19683.67, "logistics_fines": 2241.00,
     "total_deductions": 239775.50, "promo_costs": 1612.63, "operational_overhead": 29806.35,
     "disputes_filed": 156, "total_deduction_events": 487,
     "layer_1": 709055.16, "layer_2": 489591.70, "layer_3": 467667.03, "layer_4": 437860.68},
    {"channel_id": "southside_grocers", "channel_name": "Southside Grocers", "channel_type": "retailer",
     "gross_revenue": 1369598.04, "total_cogs": 696918.48, "gross_margin": 672679.56,
     "trade_deductions": 191138.69, "quality_fines": 17509.54, "logistics_fines": 890.20,
     "total_deductions": 209538.43, "promo_costs": 1612.63, "operational_overhead": 19844.65,
     "disputes_filed": 102, "total_deduction_events": 358,
     "layer_1": 672679.56, "layer_2": 479928.24, "layer_3": 461528.50, "layer_4": 441683.85},
    {"channel_id": "prairie_provisions", "channel_name": "Prairie Provisions", "channel_type": "retailer",
     "gross_revenue": 1037105.94, "total_cogs": 526140.54, "gross_margin": 510965.40,
     "trade_deductions": 126436.11, "quality_fines": 11875.09, "logistics_fines": 1174.46,
     "total_deductions": 139485.66, "promo_costs": 1612.63, "operational_overhead": 12190.85,
     "disputes_filed": 59, "total_deduction_events": 248,
     "layer_1": 510965.40, "layer_2": 382916.66, "layer_3": 369867.11, "layer_4": 357676.26},
    {"channel_id": "mountain_pantry_co", "channel_name": "Mountain Pantry Co", "channel_type": "retailer",
     "gross_revenue": 640250.46, "total_cogs": 326437.08, "gross_margin": 313813.38,
     "trade_deductions": 77705.18, "quality_fines": 9363.04, "logistics_fines": 1302.54,
     "total_deductions": 88370.76, "promo_costs": 1612.63, "operational_overhead": 11574.85,
     "disputes_filed": 52, "total_deduction_events": 236,
     "layer_1": 313813.38, "layer_2": 234495.57, "layer_3": 223829.99, "layer_4": 212255.14},
    {"channel_id": "harbor_fresh", "channel_name": "Harbor Fresh", "channel_type": "retailer",
     "gross_revenue": 569035.38, "total_cogs": 289507.20, "gross_margin": 279528.18,
     "trade_deductions": 72597.39, "quality_fines": 4336.06, "logistics_fines": 713.28,
     "total_deductions": 77646.73, "promo_costs": 1612.63, "operational_overhead": 8138.90,
     "disputes_filed": 39, "total_deduction_events": 167,
     "layer_1": 279528.18, "layer_2": 205318.16, "layer_3": 200268.82, "layer_4": 192129.92},
]

# === DEDUCTION BREAKDOWNS by channel and type ===
# Trade deductions: promo_billback, vague, short_ship, slotting
# Compliance fines: label_fine, spoilage, damaged, pallet_fine, late_delivery
DEDUCTIONS = {
    "Walmart": {
        "promo_billback": (2487720.50, 1616), "vague": (1177764.02, 944),
        "short_ship": (452260.06, 1729), "slotting": (48732.79, 5),
        "label_fine": (229555.40, 771), "spoilage": (426302.99, 340),
        "damaged": (65182.05, 75), "pallet_fine": (40665.19, 197), "late_delivery": (114773.66, 446),
    },
    "UNFI": {
        "promo_billback": (738880.84, 751), "vague": (481674.54, 380),
        "short_ship": (14375.49, 111), "slotting": (3377.58, 3),
        "label_fine": (21213.73, 41), "spoilage": (446191.21, 545),
        "damaged": (30711.30, 50), "pallet_fine": (1352.96, 9), "late_delivery": (17750.00, 52),
    },
    "KeHE": {
        "promo_billback": (523950.62, 578), "vague": (319506.59, 248),
        "short_ship": (14172.79, 106), "slotting": (1791.32, 3),
        "label_fine": (9802.91, 45), "spoilage": (277116.81, 377),
        "damaged": (15618.16, 34), "pallet_fine": (2423.70, 15), "late_delivery": (4502.12, 43),
    },
    "Whole Foods": {
        "promo_billback": (475587.24, 786), "vague": (574347.41, 452),
        "short_ship": (30008.22, 193), "slotting": (32408.09, 6),
        "label_fine": (19509.24, 121), "spoilage": (115723.27, 221),
        "damaged": (21810.01, 58), "pallet_fine": (8295.70, 55), "late_delivery": (19846.26, 262),
    },
    "Costco": {
        "promo_billback": (459339.06, 90), "vague": (31723.08, 30),
        "short_ship": (62680.22, 82), "slotting": (64348.95, 4),
        "label_fine": (41984.69, 46), "spoilage": (103179.49, 25),
        "damaged": (29206.76, 10), "pallet_fine": (1642.74, 10), "late_delivery": (26548.54, 35),
    },
    "Green Basket Market": {
        "promo_billback": (76855.96, 201), "vague": (130342.39, 98),
        "short_ship": (6163.97, 44), "slotting": (4488.51, 4),
        "label_fine": (4595.68, 31), "spoilage": (10836.55, 39),
        "damaged": (2780.13, 13), "pallet_fine": (1471.31, 11), "late_delivery": (2241.00, 46),
    },
    "Southside Grocers": {
        "promo_billback": (49388.67, 122), "vague": (130173.92, 86),
        "short_ship": (6500.74, 51), "slotting": (5075.36, 3),
        "label_fine": (5461.83, 32), "spoilage": (10004.20, 33),
        "damaged": (792.36, 6), "pallet_fine": (1251.15, 8), "late_delivery": (890.20, 17),
    },
    "Prairie Provisions": {
        "promo_billback": (30665.18, 75), "vague": (89848.68, 72),
        "short_ship": (4398.73, 32), "slotting": (1523.52, 2),
        "label_fine": (1660.46, 11), "spoilage": (8229.20, 23),
        "damaged": (1436.83, 5), "pallet_fine": (548.60, 3), "late_delivery": (1174.46, 25),
    },
    "Mountain Pantry Co": {
        "promo_billback": (19034.82, 62), "vague": (52715.73, 48),
        "short_ship": (4674.03, 35), "slotting": (1280.60, 2),
        "label_fine": (3287.62, 18), "spoilage": (3886.26, 16),
        "damaged": (1493.92, 11), "pallet_fine": (695.24, 4), "late_delivery": (1302.54, 40),
    },
    "Harbor Fresh": {
        "promo_billback": (16122.82, 55), "vague": (52581.44, 42),
        "short_ship": (2238.00, 18), "slotting": (1655.13, 2),
        "label_fine": (1529.08, 10), "spoilage": (1749.12, 11),
        "damaged": (693.70, 5), "pallet_fine": (364.16, 2), "late_delivery": (713.28, 22),
    },
}

# === QUARTERLY REVENUE (from fct_orders joined with dim_retailers) ===
QUARTERLY_REVENUE = {
    "2025-01-01": {"Walmart": 2156344.86, "UNFI": 694306.56, "KeHE": 604224.96, "Whole Foods": 557391.48, "Costco": 409768.08, "Green Basket Market": 123493.08, "Southside Grocers": 84292.74, "Prairie Provisions": 51250.02, "Harbor Fresh": 39783.24, "Mountain Pantry Co": 33109.86},
    "2025-04-01": {"Walmart": 2236839.84, "UNFI": 936403.32, "KeHE": 720903.30, "Costco": 695264.82, "Whole Foods": 652835.64, "Green Basket Market": 119931.84, "Southside Grocers": 112769.16, "Prairie Provisions": 76799.46, "Mountain Pantry Co": 50787.84, "Harbor Fresh": 38879.82},
    "2025-07-01": {"Walmart": 2487026.10, "UNFI": 1068704.22, "Costco": 753563.58, "KeHE": 622640.76, "Whole Foods": 504766.68, "Southside Grocers": 107336.34, "Prairie Provisions": 101361.54, "Green Basket Market": 99415.44, "Mountain Pantry Co": 63952.08, "Harbor Fresh": 52529.34},
    "2025-10-01": {"Walmart": 2991514.02, "UNFI": 1124817.18, "KeHE": 696920.70, "Whole Foods": 687313.68, "Costco": 473088.84, "Southside Grocers": 180504.24, "Green Basket Market": 174685.92, "Prairie Provisions": 94248.90, "Mountain Pantry Co": 69150.54, "Harbor Fresh": 56051.22},
    "2026-01-01": {"Walmart": 2010717.42, "UNFI": 682319.64, "KeHE": 567724.68, "Whole Foods": 508296.00, "Costco": 408106.26, "Southside Grocers": 111052.32, "Green Basket Market": 105900.54, "Prairie Provisions": 78576.42, "Harbor Fresh": 46732.92, "Mountain Pantry Co": 40005.36},
}

# === QUARTERLY DEDUCTIONS (from fct_deductions) ===
QUARTERLY_DEDUCTIONS = {
    "2025-01-01": {"Walmart": 469168.28, "UNFI": 118979.89, "Whole Foods": 93780.18, "KeHE": 83549.25, "Costco": 76711.33, "Southside Grocers": 18582.65, "Green Basket Market": 18606.29, "Harbor Fresh": 11746.41, "Prairie Provisions": 2755.30, "Mountain Pantry Co": 5750.49},
    "2025-04-01": {"Walmart": 424417.13, "UNFI": 134301.21, "Whole Foods": 140907.53, "KeHE": 127103.23, "Costco": 39407.93, "Southside Grocers": 19977.43, "Green Basket Market": 26638.12, "Harbor Fresh": 8301.80, "Prairie Provisions": 8500.81, "Mountain Pantry Co": 7509.29},
    "2025-07-01": {"Walmart": 406723.83, "UNFI": 201729.49, "Whole Foods": 116914.28, "KeHE": 91922.16, "Costco": 81157.50, "Southside Grocers": 11646.41, "Green Basket Market": 22021.87, "Harbor Fresh": 3309.95, "Prairie Provisions": 18043.96, "Mountain Pantry Co": 11773.90},
    "2025-10-01": {"Walmart": 517654.75, "UNFI": 159995.85, "Whole Foods": 135413.19, "KeHE": 105839.99, "Costco": 101144.06, "Southside Grocers": 28886.26, "Green Basket Market": 27902.77, "Harbor Fresh": 10125.99, "Prairie Provisions": 7356.13, "Mountain Pantry Co": 9538.58},
    "2026-01-01": {"Walmart": 428504.20, "UNFI": 119717.69, "Whole Foods": 101455.12, "KeHE": 95632.08, "Costco": 56523.19, "Southside Grocers": 22550.82, "Green Basket Market": 22789.43, "Harbor Fresh": 3305.47, "Prairie Provisions": 11000.30, "Mountain Pantry Co": 6937.16},
}

QUARTER_LABELS = {
    "2025-01-01": "Q1 2025",
    "2025-04-01": "Q2 2025",
    "2025-07-01": "Q3 2025",
    "2025-10-01": "Q4 2025",
    "2026-01-01": "Q1 2026",
}

TRADE_TYPES = {"promo_billback", "vague", "short_ship", "slotting"}
COMPLIANCE_TYPES = {"label_fine", "spoilage", "damaged", "pallet_fine", "late_delivery"}

TYPE_LABELS = {
    "promo_billback": "Promo Billback",
    "vague": "Unclassified",
    "short_ship": "Short Ship",
    "slotting": "Slotting Fees",
    "label_fine": "Label Fines",
    "spoilage": "Spoilage",
    "damaged": "Damaged Goods",
    "pallet_fine": "Pallet Fines",
    "late_delivery": "Late Delivery",
}


def generate_channels():
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
        for ch in MART_DATA
    ]


def generate_layers():
    layers = []

    # Layer 0: Revenue
    layers.append({
        "id": 0,
        "label": "Revenue",
        "subtitle": "What the CFO sees",
        "channels": [
            {"channel_name": ch["channel_name"], "channel_type": ch["channel_type"],
             "value": ch["gross_revenue"], "breakdown": []}
            for ch in MART_DATA
        ]
    })

    # Layer 1: Gross Margin
    layers.append({
        "id": 1,
        "label": "Gross Margin",
        "subtitle": "After cost of goods sold",
        "channels": [
            {"channel_name": ch["channel_name"], "channel_type": ch["channel_type"],
             "value": ch["layer_1"], "previous_value": ch["gross_revenue"],
             "breakdown": [{"label": "Cost of Goods Sold", "amount": ch["total_cogs"]}]}
            for ch in MART_DATA
        ]
    })

    # Layer 2: After Trade Deductions
    layer2_channels = []
    for ch in MART_DATA:
        name = ch["channel_name"]
        breakdown = []
        if name in DEDUCTIONS:
            for dtype in ["promo_billback", "vague", "short_ship", "slotting"]:
                if dtype in DEDUCTIONS[name] and DEDUCTIONS[name][dtype][0] > 0:
                    amount, count = DEDUCTIONS[name][dtype]
                    breakdown.append({
                        "label": TYPE_LABELS[dtype], "type": dtype,
                        "amount": amount, "count": count
                    })
            breakdown.sort(key=lambda x: x["amount"], reverse=True)
        if ch["promo_costs"] > 0:
            breakdown.append({"label": "Promotional Costs", "amount": ch["promo_costs"]})
        layer2_channels.append({
            "channel_name": name, "channel_type": ch["channel_type"],
            "value": ch["layer_2"], "previous_value": ch["layer_1"],
            "breakdown": breakdown
        })
    layers.append({
        "id": 2,
        "label": "After Trade Deductions",
        "subtitle": "Short ships, promo billbacks, slotting fees",
        "channels": layer2_channels
    })

    # Layer 3: After Compliance Fines
    layer3_channels = []
    for ch in MART_DATA:
        name = ch["channel_name"]
        breakdown = []
        if name in DEDUCTIONS:
            for dtype in ["label_fine", "spoilage", "damaged", "pallet_fine", "late_delivery"]:
                if dtype in DEDUCTIONS[name] and DEDUCTIONS[name][dtype][0] > 0:
                    amount, count = DEDUCTIONS[name][dtype]
                    breakdown.append({
                        "label": TYPE_LABELS[dtype], "type": dtype,
                        "amount": amount, "count": count
                    })
            breakdown.sort(key=lambda x: x["amount"], reverse=True)
        layer3_channels.append({
            "channel_name": name, "channel_type": ch["channel_type"],
            "value": ch["layer_3"], "previous_value": ch["layer_2"],
            "breakdown": breakdown
        })
    layers.append({
        "id": 3,
        "label": "After Compliance Fines",
        "subtitle": "Label fines, pallet fines, late delivery penalties",
        "channels": layer3_channels
    })

    # Layer 4: Net Contribution
    layers.append({
        "id": 4,
        "label": "Net Contribution",
        "subtitle": "What the channel actually earns",
        "channels": [
            {"channel_name": ch["channel_name"], "channel_type": ch["channel_type"],
             "value": ch["layer_4"], "previous_value": ch["layer_3"],
             "breakdown": [{"label": "Operational Overhead", "amount": ch["operational_overhead"]}]
             if ch["operational_overhead"] > 0 else []}
            for ch in MART_DATA
        ]
    })

    return layers


def generate_trends():
    """Generate quarterly trends using mart COGS ratios applied to quarterly revenue."""
    cogs_ratios = {ch["channel_name"]: ch["total_cogs"] / ch["gross_revenue"] for ch in MART_DATA}

    all_channels = [ch["channel_name"] for ch in MART_DATA]
    channel_types = {ch["channel_name"]: ch["channel_type"] for ch in MART_DATA}

    trends = []
    for quarter_key in sorted(QUARTERLY_REVENUE.keys()):
        quarter_label = QUARTER_LABELS[quarter_key]
        quarter_data = []

        for channel in all_channels:
            revenue = QUARTERLY_REVENUE[quarter_key].get(channel, 0)
            deductions = QUARTERLY_DEDUCTIONS[quarter_key].get(channel, 0)
            cogs = round(revenue * cogs_ratios[channel], 2)
            contribution = round(revenue - cogs - deductions, 2)
            margin_pct = round((contribution / revenue) * 100, 1) if revenue > 0 else 0

            quarter_data.append({
                "channel_name": channel,
                "channel_type": channel_types[channel],
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

    channels = generate_channels()
    with open(out_dir / "channels.json", "w") as f:
        json.dump(channels, f, indent=2)
    print(f"channels.json: {len(channels)} channels")

    layers = generate_layers()
    with open(out_dir / "layers.json", "w") as f:
        json.dump(layers, f, indent=2)
    print(f"layers.json: {len(layers)} layers")

    trends = generate_trends()
    with open(out_dir / "trends.json", "w") as f:
        json.dump(trends, f, indent=2)
    print(f"trends.json: {len(trends)} quarters")

    total_revenue = sum(ch["gross_revenue"] for ch in MART_DATA)
    print(f"\nTotal revenue: ${total_revenue:,.2f}")
    print(f"(Update CLAUDE.md: ~${total_revenue/1e6:.0f}M)")


if __name__ == "__main__":
    main()
