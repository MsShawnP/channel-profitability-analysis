"""Client-mode tests for channel-profitability-analysis.

Adversarial fixtures per checklist §6: clean run (fines subtracted from net —
the P1 discipline), missing required column (blocked), negative value, duplicate
channel, empty file, and the --final watermark. Fictional-placeholder identity.

Skipped if lailara_engagement isn't installed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("lailara_engagement")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import client_mode  # noqa: E402

from lailara_engagement.errors import ReadError  # noqa: E402

_CONFIG = """
client: {name: Meridian Farms}
engagement: {id: MER-2026-08}
as_of_date: "2026-01-31"
demo: true
basis: {margin: contribution, window_months: 36, window_label: "2023-2025"}
columns:
  channel_name: channel_name
  channel_type: channel_type
  revenue: revenue
  cogs: cogs
  deductions: deductions
  fines: fines
  overhead: overhead
"""

# 2 channels; net = rev - cogs - deductions - fines - overhead
_CLEAN = (
    "channel_name,channel_type,revenue,cogs,deductions,fines,overhead\n"
    "Harborline Markets,retailer,1000000,500000,50000,20000,10000\n"   # net 420000
    "Cedarwood Dist,distributor,600000,400000,30000,5000,5000\n"        # net 160000
)


def _cfg(tmp_path):
    p = tmp_path / "engagement.yml"
    p.write_text(_CONFIG, encoding="utf-8")
    return str(p)


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_clean_run_fines_subtracted(tmp_path):
    src = _write(tmp_path, "ch.csv", _CLEAN)
    result = client_mode.run(_cfg(tmp_path), src, str(tmp_path / "out"))
    assert result["status"] == "ok"
    assert result["channels"] == 2
    assert result["net_contribution"] == 580000.0        # 420000 + 160000
    assert result["fines_subtracted"] == 25000.0         # 20000 + 5000

    s = json.load(open(result["summary_json"], encoding="utf-8"))
    top = s["channels"][0]                                 # sorted by net desc
    assert top["channel_name"] == "Harborline Markets"
    # after_fines strictly below after_deductions (fines actually subtracted)
    assert top["after_fines"] == top["after_deductions"] - top["fines"]
    assert top["net_contribution"] == 420000.0

    html = open(result["report"], encoding="utf-8").read()
    assert "Meridian Farms" in html and "SHA-256" in html and "DRAFT" in html
    assert "compliance fines" in html.lower()
    assert "36 months" in html


def test_window_label_tracks_config_not_hardcoded(tmp_path):
    """The rendered window ('N months (label)') must come from
    basis.window_months / window_label, not a hardcoded default. The clean-run
    test asserts only the demo's own '36 months' — a positive-only check a
    hardcoded '36' would also pass, the gap that let trade-spend quote 26 weeks
    of data as 'trailing 52 weeks'.

    Both halves: feed a distinctive window and assert it tracks, AND assert the
    demo default is absent. (margin left as-is: 'contribution' also appears in
    the fixed 'net contribution' headline, so it is not a clean absence marker.)"""
    cfg = tmp_path / "engagement.yml"
    cfg.write_text(_CONFIG.replace("window_months: 36", "window_months: 41")
                          .replace('window_label: "2023-2025"', 'window_label: "FY2024-FY2026"'),
                   encoding="utf-8")
    src = _write(tmp_path, "ch.csv", _CLEAN)
    result = client_mode.run(str(cfg), src, str(tmp_path / "out"))
    assert result["status"] == "ok"
    html = open(result["report"], encoding="utf-8").read()
    assert "41 months (FY2024-FY2026)" in html
    assert "36 months" not in html                       # demo default must not survive
    assert "2023-2025" not in html


def test_missing_required_column_blocks(tmp_path):
    # no fines column -> blocked (fines are required; they must never be optional)
    src = _write(tmp_path, "bad.csv",
                 "channel_name,channel_type,revenue,cogs,deductions,overhead\nA,retailer,100,50,10,5\n")
    result = client_mode.run(_cfg(tmp_path), src, str(tmp_path / "out"))
    assert result["status"] == "blocked"
    assert "fines" in open(result["readiness_report"], encoding="utf-8").read().lower()


def test_negative_value_flagged(tmp_path):
    src = _write(tmp_path, "n.csv",
                 "channel_name,channel_type,revenue,cogs,deductions,fines,overhead\n"
                 "A,retailer,-100,50,10,5,5\nB,retailer,100,50,10,5,5\n")
    result = client_mode.run(_cfg(tmp_path), src, str(tmp_path / "out"))
    assert result["n_warnings"] >= 1


def test_duplicate_channel_blocks(tmp_path):
    src = _write(tmp_path, "dup.csv",
                 "channel_name,channel_type,revenue,cogs,deductions,fines,overhead\n"
                 "A,retailer,100,50,10,5,5\nA,retailer,200,60,10,5,5\n")
    result = client_mode.run(_cfg(tmp_path), src, str(tmp_path / "out"))
    assert result["status"] == "blocked"
    assert "duplicat" in open(result["readiness_report"], encoding="utf-8").read().lower()


def test_empty_file_raises(tmp_path):
    src = _write(tmp_path, "e.csv", "")
    with pytest.raises(ReadError):
        client_mode.run(_cfg(tmp_path), src, str(tmp_path / "out"))


def test_final_drops_watermark(tmp_path):
    src = _write(tmp_path, "ch.csv", _CLEAN)
    result = client_mode.run(_cfg(tmp_path), src, str(tmp_path / "out"), final=True)
    assert "ll-draft" not in open(result["report"], encoding="utf-8").read()
