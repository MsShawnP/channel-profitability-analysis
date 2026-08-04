"""Demo golden lock — channel-profitability-analysis.

Byte-locks the three committed demo JSON the React app renders and pins the
figures the 07-31 audit cared about — above all the P1 the audit flagged: fines
must actually be subtracted in the cost waterfall (they were "vanishing" in
filtered views before). The layer stack's "After Compliance Fines" layer sits
below "After Trade Deductions" by the fines total; if that stops being true, this
fails.

If a SHA or a figure moves, STOP: a golden moved.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data"

GOLDEN_SHA256 = {
    "channels.json": "7818b63f60b78299",
    "layers.json": "19692f0801b22e2d",
    "trends.json": "0369a6601804b354",
}


@pytest.fixture(scope="module")
def layers():
    return json.loads((DATA / "layers.json").read_text())


@pytest.mark.parametrize("name", sorted(GOLDEN_SHA256))
def test_demo_data_sha256_prefix(name):
    digest = hashlib.sha256((DATA / name).read_bytes()).hexdigest()[:16]
    assert digest == GOLDEN_SHA256[name], (
        f"{name} changed (sha256[:16] {digest} != golden {GOLDEN_SHA256[name]}) "
        "— a demo golden moved; STOP and report."
    )


def _layer_total(layers, i):
    return round(sum(c["value"] for c in layers[i]["channels"]), 2)


def test_fines_are_subtracted_in_the_waterfall(layers):
    # THE P1: fines must reduce contribution. Layer 3 "After Compliance Fines"
    # sits below layer 2 "After Trade Deductions" by the fines total (~$237K,
    # the audit's ~$249K). If fines "vanish" again, l2 == l3 and this fails.
    assert layers[2]["label"] == "After Trade Deductions"
    assert layers[3]["label"] == "After Compliance Fines"
    after_deductions = _layer_total(layers, 2)
    after_fines = _layer_total(layers, 3)
    fines = round(after_deductions - after_fines, 2)
    assert after_deductions == 13002171.15
    assert after_fines == 12765239.37
    assert fines == 236931.78
    assert fines > 0                      # fines actually subtracted, not vanished


def test_net_contribution_after_fines_and_overhead(layers):
    assert layers[4]["label"] == "Net Contribution"
    net = _layer_total(layers, 4)
    assert net == 12624133.37
    # net is strictly below after-fines (overhead also subtracted)
    assert net < _layer_total(layers, 3)


def test_headline_annual_average_revenue():
    channels = json.loads((DATA / "channels.json").read_text())
    total = round(sum(c["gross_revenue"] for c in channels), 2)
    assert total == 25544477.16     # ~$25.5M/yr annual average (the headline basis)


def test_default_view_matches_headline_basis():
    # Standardized: the default landing view uses the annual-average basis so it
    # matches the headline narrative (both read channels.json) — not FY2025 in
    # the chart while the headline cites the annual average.
    app = (ROOT / "src" / "components" / "App.tsx").read_text(encoding="utf-8")
    assert "const DEFAULT_TIME_FILTER = 'full'" in app
    cm = (ROOT / "src" / "lib" / "computeMetrics.ts").read_text(encoding="utf-8")
    # the layer stack subtracts fines explicitly (the P1 fix, in source)
    assert "d.contribution - d.fines" in cm
