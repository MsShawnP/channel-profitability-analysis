"""Client-mode CLI for channel-profitability-analysis.

Takes a client's channel P&L and builds the five-layer contribution waterfall
per channel — revenue -> gross margin -> after trade deductions -> after
compliance fines -> net contribution — with **fines explicitly subtracted** (the
whole point: fines must never vanish from net contribution). Validated, never
committed, never deployed. The demo React app is untouched.

Usage:
    python client_mode.py --config engagement.yml --input client-data/channels.csv \
        --out client-output [--final]
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from lailara_engagement import (
    ColumnSpec,
    PreflightSpec,
    build_provenance,
    load_config,
    read_table,
    run_preflight,
    validation_status_label,
    write_report,
)
from lailara_engagement import palette as P
from lailara_engagement.provenance import Provenance

TOOL = "channel-profitability-analysis"
TOOL_VERSION = "1.0"


def _spec() -> PreflightSpec:
    return PreflightSpec(
        tool=TOOL, version=TOOL_VERSION,
        columns=[
            ColumnSpec(name="channel_name", dtype="string", required=True, unique=True,
                       description="channel/customer name", spec_ref="INPUT-SPEC §1"),
            ColumnSpec(name="channel_type", dtype="string", required=True,
                       description="retailer / distributor / DTC", spec_ref="INPUT-SPEC §1"),
            ColumnSpec(name="revenue", dtype="number", required=True, not_negative=True,
                       description="gross revenue", spec_ref="INPUT-SPEC §1"),
            ColumnSpec(name="cogs", dtype="number", required=True, not_negative=True,
                       description="cost of goods sold", spec_ref="INPUT-SPEC §1"),
            ColumnSpec(name="deductions", dtype="number", required=True, not_negative=True,
                       description="trade deductions", spec_ref="INPUT-SPEC §1"),
            ColumnSpec(name="fines", dtype="number", required=True, not_negative=True,
                       description="compliance fines (MUST be subtracted from net)", spec_ref="INPUT-SPEC §1"),
            ColumnSpec(name="overhead", dtype="number", required=True, not_negative=True,
                       description="operational / dispute overhead", spec_ref="INPUT-SPEC §1"),
        ],
    )


def _num(v) -> float:
    try:
        return float(str(v).strip())
    except (ValueError, TypeError):
        return 0.0


def run(config_path: str, input_path: str, out_dir: str, *, final: bool = False) -> dict:
    config = load_config(config_path)
    read = read_table(input_path)
    spec = _spec()
    report = run_preflight(read, spec, config)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    provenance = build_provenance(
        tool=TOOL, tool_version=TOOL_VERSION, inputs=[read], config=config,
        validation_status=validation_status_label(report.status, report.n_warnings))
    if not report.passed:
        paths = write_report(report, config, str(out), provenance=provenance,
                             draft=not final, basename="data-readiness-report",
                             title="Channel P&L Data Readiness Report")
        return {"status": "blocked", "readiness_report": paths["html"]}

    m = report.column_mapping
    frame = read.frame

    def col(name):
        return frame[m[name]]

    rows = []
    tot = {"revenue": 0.0, "cogs": 0.0, "deductions": 0.0, "fines": 0.0, "overhead": 0.0, "net": 0.0}
    for i in range(len(frame)):
        rev = _num(col("revenue").iloc[i]); cogs = _num(col("cogs").iloc[i])
        ded = _num(col("deductions").iloc[i]); fine = _num(col("fines").iloc[i])
        oh = _num(col("overhead").iloc[i])
        gross = rev - cogs
        after_ded = gross - ded
        after_fines = after_ded - fine
        net = after_fines - oh
        rows.append({
            "channel_name": str(col("channel_name").iloc[i]).strip(),
            "channel_type": str(col("channel_type").iloc[i]).strip(),
            "revenue": round(rev, 2), "gross_margin": round(gross, 2),
            "after_deductions": round(after_ded, 2), "after_fines": round(after_fines, 2),
            "net_contribution": round(net, 2),
            "fines": round(fine, 2),
            "net_margin_pct": round(net / rev, 4) if rev else 0,
        })
        for k, v in (("revenue", rev), ("cogs", cogs), ("deductions", ded),
                     ("fines", fine), ("overhead", oh), ("net", net)):
            tot[k] += v

    rows.sort(key=lambda r: r["net_contribution"], reverse=True)
    window_months = int(config.basis.get("window_months") or 0) or None
    summary = {
        "window": {"months": window_months, "label": config.basis.get("window_label", ""),
                   "basis": config.basis.get("margin", "contribution")},
        "channels": rows,
        "totals": {k: round(v, 2) for k, v in tot.items()},
        "fines_subtracted": round(tot["fines"], 2),
        "net_contribution": round(tot["net"], 2),
    }
    json_dir = out / "json"; json_dir.mkdir(parents=True, exist_ok=True)
    (json_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report_path = out / "channel-profitability-summary.html"
    report_path.write_text(_summary_html(config, summary, provenance, draft=not final), encoding="utf-8")
    return {"status": "ok", "channels": len(rows),
            "net_contribution": round(tot["net"], 2), "fines_subtracted": round(tot["fines"], 2),
            "report": str(report_path), "summary_json": str(json_dir / "summary.json"),
            "n_warnings": report.n_warnings}


def _d(v):
    return f"${v:,.0f}"


def _summary_html(config, s, provenance: Provenance, *, draft: bool) -> str:
    esc = html.escape
    wm = s["window"].get("months"); wl = s["window"].get("label") or ""
    win = (f"{wm} months" + (f" ({esc(wl)})" if wl else "")) if wm else "full window"
    basis = esc(s["window"].get("basis") or "contribution")
    rows = "".join(
        f"<tr><td>{esc(r['channel_name'])}</td><td>{esc(r['channel_type'])}</td>"
        f"<td class=num>{_d(r['revenue'])}</td><td class=num>{_d(r['after_deductions'])}</td>"
        f"<td class=num>{_d(r['fines'])}</td><td class=num>{_d(r['net_contribution'])}</td>"
        f"<td class=num>{r['net_margin_pct']*100:.1f}%</td></tr>"
        for r in s["channels"])
    t = s["totals"]
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>Channel Profitability — {esc(config.client_name)}</title><style>{_css(draft)}</style></head>
<body class="{' ll-draft' if draft else ''}"><main class=ll-page>
<header class=ll-header>
  <div class=ll-eyebrow>Lailara LLC · Channel Profitability</div>
  <h1 class=ll-title>Contribution by Channel</h1>
  <div class=ll-client>
    <div><span class=ll-k>Client</span> {esc(config.client_name)}</div>
    <div><span class=ll-k>Engagement</span> {esc(config.engagement_id)}</div>
    <div><span class=ll-k>As of</span> {esc(config.as_of_date.isoformat())}</div>
    <div><span class=ll-k>Basis · window</span> {basis} · {win}</div>
  </div>
</header>
<section class=ll-banner>
  <div class=ll-score>{_d(s['net_contribution'])} net contribution</div>
  <div>after subtracting {_d(s['fines_subtracted'])} in compliance fines
       · {len(s['channels'])} channels over {win}</div>
</section>
<section class=ll-section>
  <h2 class=ll-h2>Five-layer waterfall by channel</h2>
  <table class=ll-table><thead><tr><th>Channel</th><th>Type</th><th>Revenue</th>
  <th>After deductions</th><th>Fines</th><th>Net contribution</th><th>Net margin</th></tr></thead>
  <tbody>{rows}</tbody></table>
  <p class=ll-note>Net contribution = revenue − COGS − trade deductions − <strong>compliance
  fines</strong> − operational overhead. Fines are subtracted explicitly in every view;
  they never vanish from the net. Basis: {basis}; window: {win}.</p>
</section>
{provenance.to_html()}
</main></body></html>"""


def _css(draft: bool) -> str:
    draft_css = (
        ".ll-draft::before{content:'DRAFT';position:fixed;top:50%;left:50%;"
        "transform:translate(-50%,-50%) rotate(-32deg);font-family:var(--s);"
        "font-size:22vw;font-weight:700;color:rgba(204,16,10,.06);z-index:0;"
        "pointer-events:none;white-space:nowrap}" if draft else ""
    )
    return f"""
:root{{--s:{P.LL_SERIF};--f:{P.LL_SANS}}}*{{box-sizing:border-box}}
body{{margin:0;background:{P.LL_CANVAS};color:{P.LL_TEXT};font-family:var(--f);line-height:1.6}}
.ll-page{{position:relative;z-index:1;max-width:{P.LL_MAX_WIDTH};margin:0 auto;padding:48px 24px}}
.ll-header{{border-bottom:1px solid {P.LL_GRIDLINE};padding-bottom:24px;margin-bottom:24px}}
.ll-eyebrow{{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:{P.LL_RED};font-weight:600}}
.ll-title{{font-family:var(--s);font-weight:700;color:{P.LL_INK};font-size:34px;margin:8px 0 16px}}
.ll-client{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px 24px;font-size:14px}}
.ll-k{{display:block;color:{P.LL_TEXT_SEC};font-size:11px;text-transform:uppercase;letter-spacing:.04em}}
.ll-banner{{border-radius:2px;padding:16px 20px;margin-bottom:32px;background:{P.LL_HK_SURFACE};color:{P.LL_HK_DARK}}}
.ll-score{{font-family:var(--s);font-weight:700;font-size:22px}}
.ll-section{{margin:0 0 32px}}
.ll-h2{{font-family:var(--s);font-weight:700;color:{P.LL_INK};font-size:22px;
margin:0 0 12px;padding-bottom:6px;border-bottom:1px solid {P.LL_GRIDLINE}}}
.ll-note{{font-size:13px;color:{P.LL_TEXT_SEC};margin-top:8px}}
.ll-table{{width:100%;border-collapse:collapse;font-size:14px}}
.ll-table th{{text-align:left;background:{P.LL_CHICAGO};color:#fff;padding:8px 12px}}
.ll-table td{{padding:8px 12px;border-bottom:1px solid {P.LL_GRIDLINE}}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}
.ll-provenance{{margin-top:40px;background:{P.LL_CARD_BG};color:{P.LL_CARD_TEXT};
padding:20px 24px;border-radius:2px;font-size:13px}}
.ll-prov-title{{font-family:var(--s);font-weight:700;font-size:16px;margin-bottom:8px}}
.ll-provenance div{{margin-bottom:4px;color:{P.LL_CARD_SUBTITLE}}}
.ll-provenance strong{{color:{P.LL_CARD_TEXT}}}
.ll-prov-inputs{{width:100%;border-collapse:collapse;margin-top:8px}}
.ll-prov-inputs th{{text-align:left;border-bottom:1px solid rgba(255,255,255,.12);padding:4px 8px;color:{P.LL_CARD_MUTED}}}
.ll-prov-inputs td{{padding:4px 8px;border-bottom:1px solid rgba(255,255,255,.08);color:{P.LL_CARD_SUBTITLE}}}
.ll-prov-brand{{margin-top:12px;font-family:var(--s);color:{P.LL_CARD_MUTED}}}
{draft_css}
@media print{{body{{background:#fff}}}}
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="channel-profitability client mode")
    ap.add_argument("--config", required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", default="client-output")
    ap.add_argument("--final", action="store_true")
    args = ap.parse_args(argv)
    result = run(args.config, args.input, args.out, final=args.final)
    if result["status"] == "blocked":
        print(f"BLOCKED — data not ready. See {result['readiness_report']}")
        return 3
    print(f"net contribution {_d(result['net_contribution'])} after {_d(result['fines_subtracted'])} "
          f"fines subtracted, across {result['channels']} channels")
    print(f"report -> {result['report']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
