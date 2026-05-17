"""Export channel contribution data to static JSON for Astro build.

Reads from mart_channel_contribution and fct_deductions in the
Cinderhaven Data Platform (Postgres). Produces two files:

  src/data/channels.json — channel metadata and revenue
  src/data/layers.json   — layered contribution breakdown per channel
                           with drill-down detail for callout cards
"""

from __future__ import annotations

import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import psycopg2
import psycopg2.extensions
import psycopg2.extras

DEC2FLOAT = psycopg2.extensions.new_type(
    psycopg2.extensions.DECIMAL.values,
    "DEC2FLOAT",
    lambda value, curs: float(value) if value is not None else None,
)
psycopg2.extensions.register_type(DEC2FLOAT)

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "src" / "data"


def connect():
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        password = os.environ.get("POSTGRES_PASSWORD")
        if not password:
            print(
                "Error: Set DATABASE_URL or POSTGRES_PASSWORD environment variable.",
                file=sys.stderr,
            )
            sys.exit(1)
        dsn = f"postgresql://postgres:{password}@localhost:5432/cinderhaven"
    return psycopg2.connect(dsn)


def query(conn, sql):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql)
        return cur.fetchall()


def build_channels(conn):
    rows = query(conn, """
        SELECT channel_id, channel_name, channel_type,
               gross_revenue, total_cogs, total_deductions,
               disputes_filed, total_deduction_events
        FROM public_marts.mart_channel_contribution
        ORDER BY gross_revenue DESC
    """)
    return [dict(r) for r in rows]


def build_deduction_breakdown(conn):
    """Per-channel breakdown of deductions by type for callout cards."""
    rows = query(conn, """
        SELECT d.retailer_id AS channel_id,
               r.retailer_name AS channel_name,
               d.deduction_type,
               count(*) AS event_count,
               sum(d.deduction_amount) AS total_amount
        FROM public_marts.fct_deductions d
        JOIN public_marts.dim_retailers r ON d.retailer_id = r.retailer_id
        GROUP BY d.retailer_id, r.retailer_name, d.deduction_type
        ORDER BY d.retailer_id, sum(d.deduction_amount) DESC
    """)

    by_channel = {}
    for r in rows:
        cid = r["channel_id"]
        if cid not in by_channel:
            by_channel[cid] = []
        by_channel[cid].append({
            "label": format_deduction_type(r["deduction_type"]),
            "type": r["deduction_type"],
            "amount": round(r["total_amount"], 2),
            "count": r["event_count"],
        })
    return by_channel


def format_deduction_type(t):
    return {
        "short_ship": "Short Ship",
        "promo_billback": "Promo Billback",
        "slotting": "Slotting Fees",
        "vague": "Unclassified",
        "label_fine": "Label Fines",
        "pallet_fine": "Pallet Fines",
        "spoilage": "Spoilage",
        "damaged": "Damaged Goods",
        "late_delivery": "Late Delivery",
    }.get(t, t)


def build_layers(conn, deduction_breakdown):
    """Build the progressive-reveal layer structure.

    Each layer has per-channel values and a breakdown of what was
    subtracted at that layer (for drill-down callout cards).
    """
    rows = query(conn, """
        SELECT channel_id, channel_name, channel_type,
               gross_revenue,
               total_cogs,
               layer_1_gross_margin,
               trade_deductions,
               promo_costs,
               layer_2_post_deductions,
               quality_fines,
               logistics_fines,
               layer_3_post_compliance,
               operational_overhead,
               layer_4_net_contribution
        FROM public_marts.mart_channel_contribution
        ORDER BY gross_revenue DESC
    """)

    layers = []

    # Layer 0: Revenue
    layers.append({
        "id": 0,
        "label": "Revenue",
        "subtitle": "What the CFO sees",
        "channels": [{
            "channel_name": r["channel_name"],
            "channel_type": r["channel_type"],
            "value": round(r["gross_revenue"], 2),
            "breakdown": [],
        } for r in rows],
    })

    # Layer 1: Gross Margin (revenue - COGS)
    layers.append({
        "id": 1,
        "label": "Gross Margin",
        "subtitle": "After cost of goods sold",
        "channels": [{
            "channel_name": r["channel_name"],
            "channel_type": r["channel_type"],
            "value": round(r["layer_1_gross_margin"], 2),
            "previous_value": round(r["gross_revenue"], 2),
            "breakdown": [{
                "label": "Cost of Goods Sold",
                "amount": round(r["total_cogs"], 2),
            }],
        } for r in rows],
    })

    # Layer 2: Post-Deductions (gross margin - trade deductions - promo)
    layers.append({
        "id": 2,
        "label": "After Trade Deductions",
        "subtitle": "Short ships, promo billbacks, slotting fees",
        "channels": [{
            "channel_name": r["channel_name"],
            "channel_type": r["channel_type"],
            "value": round(r["layer_2_post_deductions"], 2),
            "previous_value": round(r["layer_1_gross_margin"], 2),
            "breakdown": _trade_breakdown(r, deduction_breakdown),
        } for r in rows],
    })

    # Layer 3: Post-Compliance (minus quality + logistics fines)
    layers.append({
        "id": 3,
        "label": "After Compliance Fines",
        "subtitle": "Label fines, pallet fines, late delivery penalties",
        "channels": [{
            "channel_name": r["channel_name"],
            "channel_type": r["channel_type"],
            "value": round(r["layer_3_post_compliance"], 2),
            "previous_value": round(r["layer_2_post_deductions"], 2),
            "breakdown": _compliance_breakdown(r, deduction_breakdown),
        } for r in rows],
    })

    # Layer 4: Net Contribution (minus operational overhead)
    layers.append({
        "id": 4,
        "label": "Net Contribution",
        "subtitle": "After dispute triage and operational overhead",
        "channels": [{
            "channel_name": r["channel_name"],
            "channel_type": r["channel_type"],
            "value": round(r["layer_4_net_contribution"], 2),
            "previous_value": round(r["layer_3_post_compliance"], 2),
            "breakdown": [{
                "label": "Operational Overhead",
                "amount": round(r["operational_overhead"], 2),
            }] if r["operational_overhead"] > 0 else [],
        } for r in rows],
    })

    return layers


def _trade_breakdown(row, deduction_breakdown):
    """Extract trade-category deductions for a channel."""
    trade_types = {"short_ship", "promo_billback", "slotting", "vague"}
    items = deduction_breakdown.get(row["channel_id"], [])
    result = [i for i in items if i["type"] in trade_types]
    promo = row["promo_costs"]
    if promo and promo > 0:
        result.append({"label": "Promotional Costs", "amount": round(promo, 2)})
    return result


def _compliance_breakdown(row, deduction_breakdown):
    """Extract compliance-category deductions for a channel."""
    compliance_types = {"label_fine", "pallet_fine", "spoilage", "damaged", "late_delivery"}
    items = deduction_breakdown.get(row["channel_id"], [])
    return [i for i in items if i["type"] in compliance_types]


def main():
    conn = connect()

    channels = build_channels(conn)
    deduction_breakdown = build_deduction_breakdown(conn)
    layers = build_layers(conn, deduction_breakdown)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    channels_path = OUT_DIR / "channels.json"
    layers_path = OUT_DIR / "layers.json"

    with open(channels_path, "w") as f:
        json.dump(channels, f, indent=2)

    with open(layers_path, "w") as f:
        json.dump(layers, f, indent=2)

    # Validation summary
    total_revenue = sum(c["gross_revenue"] for c in channels)
    final_layer = layers[-1]
    total_contribution = sum(ch["value"] for ch in final_layer["channels"])

    print(f"Exported {len(channels)} channels, {len(layers)} layers")
    print(f"Total revenue: ${total_revenue:,.0f}")
    print(f"Net contribution: ${total_contribution:,.0f}")
    print(f"Files: {channels_path}, {layers_path}")

    conn.close()


if __name__ == "__main__":
    main()
