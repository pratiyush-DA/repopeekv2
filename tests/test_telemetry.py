"""Unit tests for Telemetry, Savings & ROI Scoreboard Engine."""
from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from repopeek.telemetry import TelemetryTracker


def test_telemetry_recording_and_aggregation():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tracker = TelemetryTracker(repopeek_dir=tmp_dir)

        # Record first task
        evt1 = tracker.record_event(
            task="Task 1: Update auth controller",
            baseline_tokens=40000,
            delivered_tokens=1200,
            baseline_files=12,
            delivered_files=2,
        )
        assert evt1["tokens_saved"] == 38800
        assert evt1["files_avoided"] == 10
        assert evt1["reduction_pct"] > 90.0

        # Record second task
        evt2 = tracker.record_event(
            task="Task 2: Fix database migration",
            baseline_tokens=60000,
            delivered_tokens=2000,
            baseline_files=15,
            delivered_files=3,
        )
        assert evt2["tokens_saved"] == 58000

        # Summary verification
        summary = tracker.get_summary(timeframe="current_session")
        assert summary["tasks_count"] == 2
        assert summary["total_tokens_saved"] == 96800
        assert summary["total_files_avoided"] == 22
        assert summary["total_cost_saved_usd"] > 0.20


def test_render_ascii_card():
    tracker = TelemetryTracker()
    event = {
        "task": "Refactor billing service",
        "delivered_files": 3,
        "delivered_tokens": 1450,
        "baseline_files": 18,
        "baseline_tokens": 52000,
        "tokens_saved": 50550,
        "reduction_pct": 97.2,
        "files_avoided": 15,
        "cost_saved_usd": 0.1517,
    }
    card = tracker.render_ascii_card(event)
    assert "REPOPEEK EFFICIENCY SCORECARD" in card
    assert "50,550" in card
    assert "15 full files" in card


def test_render_hud_markdown():
    tracker = TelemetryTracker()
    summary = {
        "tasks_count": 5,
        "total_delivered_tokens": 7500,
        "total_baseline_tokens": 250000,
        "total_tokens_saved": 242500,
        "total_files_avoided": 65,
        "total_cost_saved_usd": 0.7275,
        "overall_reduction_pct": 97.0,
        "avg_pack_tokens": 1500,
    }
    hud = tracker.render_hud_markdown(summary)
    assert "# RepoPeek Context Efficiency & ROI Scoreboard" in hud
    assert "242,500 tokens" in hud
    assert "$0.7275 USD" in hud
