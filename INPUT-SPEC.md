# INPUT-SPEC — channel-profitability-analysis (client mode)

What to hand the tool in a client engagement. One channel P&L file (one row per
sales channel), CSV or XLSX. Derived from the fields the engine consumes
(`src/lib/computeMetrics.ts`, `layers.json`), not the README.

## Required columns

Each channel's P&L is decomposed into the five-layer contribution waterfall:
revenue → gross margin → after trade deductions → **after compliance fines** →
net contribution. **Fines are required**, not optional — the whole point of the
analysis is that fines are subtracted from net contribution and never vanish.

| Canonical | Type | Used for |
|---|---|---|
| `channel_name` | string (unique) | Channel/customer name. §1 |
| `channel_type` | string | `retailer` / `distributor` / `DTC`. §1 |
| `revenue` | number ≥ 0 | Gross revenue (waterfall start). §1 |
| `cogs` | number ≥ 0 | Cost of goods sold → gross margin. §1 |
| `deductions` | number ≥ 0 | Trade deductions (short ships, promo billbacks, slotting). §1 |
| `fines` | number ≥ 0 | Compliance fines (label/pallet/late-delivery). Subtracted from net. §1 |
| `overhead` | number ≥ 0 | Operational / dispute-resolution overhead → net contribution. §1 |

`net contribution = revenue − COGS − deductions − fines − overhead`, per channel.

## Basis & window (engagement.yml)

```yaml
as_of_date: "2026-01-31"          # analysis anchor; NEVER today's date
basis:
  margin: "contribution"          # printed on the output
  window_months: 36               # window length
  window_label: "annual average, 2023–2025"   # printed beside the figures
```

## Run

```bash
pip install -e ../engagement-template/lib
python client_mode.py --config engagement.yml --input client-data/channels.csv \
    --out client-output [--final]
```

Output to `client-output/` (gitignored): a branded, provenance-footed,
DRAFT-watermarked `channel-profitability-summary.html` (the five-layer waterfall
per channel with fines explicitly subtracted, net contribution, net margin — each
with its basis and window) + `json/summary.json`; or a Data Readiness Report if a
required column (including `fines`) is missing. The demo Astro app is never edited.
