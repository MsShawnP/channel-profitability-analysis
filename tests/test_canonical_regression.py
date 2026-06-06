"""Cinderhaven canonical data regression tests.

Verifies the baked JSON data artifacts match the Cinderhaven data contract.

Canonical contract (target):
    - 50 SKUs, 5 product lines, 6 retailers
    - Retailers: Walmart, Costco, Whole Foods, Sprouts, Kroger, Regional Group

This repo's scope:
    - 10 channels (6 retailers + 3 distributors + DTC) -- channel-level P&L view.
    - Channel-level tool; SKU-level counts live in other repos.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "data"


@pytest.fixture(scope="module")
def channels():
    return json.loads((DATA_DIR / "channels.json").read_text())


@pytest.fixture(scope="module")
def layers():
    return json.loads((DATA_DIR / "layers.json").read_text())


@pytest.fixture(scope="module")
def trends():
    return json.loads((DATA_DIR / "trends.json").read_text())


class TestCinderhavenCanonicalRegression:
    """Guard-rails for the baked Cinderhaven channel dataset."""

    # ------------------------------------------------------------------
    # Channel counts
    # ------------------------------------------------------------------

    def test_channel_count(self, channels):
        """10 channels: 6 retailers + 3 distributors + DTC."""
        assert len(channels) == 10, f"Expected 10 channels, got {len(channels)}"

    def test_retailer_count(self, channels):
        retailers = [c for c in channels if c["channel_type"] == "retailer"]
        assert len(retailers) == 6, f"Expected 6 retailers, got {len(retailers)}"

    def test_distributor_count(self, channels):
        distributors = [c for c in channels if c["channel_type"] == "distributor"]
        assert len(distributors) == 3, f"Expected 3 distributors, got {len(distributors)}"

    # ------------------------------------------------------------------
    # Canonical 6 retailers present
    # ------------------------------------------------------------------

    def test_canonical_retailers_present(self, channels):
        """All 6 contract retailers must appear."""
        names = {c["channel_name"] for c in channels}
        for retailer in ("Walmart", "Costco", "Whole Foods", "Sprouts", "Kroger", "Regional Group"):
            assert retailer in names, f"Canonical retailer {retailer!r} missing"

    # ------------------------------------------------------------------
    # Revenue sanity
    # ------------------------------------------------------------------

    def test_total_revenue_range(self, channels):
        """Total gross revenue should be ~$76.8M (reasonable range: $70M-$85M)."""
        total = sum(c["gross_revenue"] for c in channels)
        assert 70_000_000 < total < 85_000_000, (
            f"Total revenue ${total:,.0f} outside expected range"
        )

    def test_every_channel_has_positive_revenue(self, channels):
        for c in channels:
            assert c["gross_revenue"] > 0, (
                f"{c['channel_name']} has non-positive revenue"
            )

    # ------------------------------------------------------------------
    # Data file existence
    # ------------------------------------------------------------------

    def test_data_files_exist(self):
        for name in ("channels.json", "layers.json", "trends.json"):
            path = DATA_DIR / name
            assert path.exists(), f"Data file missing: {path}"

    # ------------------------------------------------------------------
    # Layers structure
    # ------------------------------------------------------------------

    def test_layers_count(self, layers):
        """5 layers: Revenue, After COGS, After Deductions, After Fines, Net."""
        assert len(layers) == 5, f"Expected 5 layers, got {len(layers)}"

    def test_layers_have_all_channels(self, layers, channels):
        """Each layer must have entries for all 10 channels."""
        channel_names = {c["channel_name"] for c in channels}
        for layer in layers:
            layer_channels = {c["channel_name"] for c in layer["channels"]}
            missing = channel_names - layer_channels
            assert not missing, (
                f"Layer {layer['id']} missing channels: {missing}"
            )

    # ------------------------------------------------------------------
    # Trends structure
    # ------------------------------------------------------------------

    def test_trends_quarterly(self, trends):
        """Trends data should cover at least 4 quarters."""
        assert len(trends) >= 4, f"Expected >= 4 quarters, got {len(trends)}"
