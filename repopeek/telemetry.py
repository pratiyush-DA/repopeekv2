"""Telemetry, Savings & ROI Scoreboard Engine measuring tokens, files avoided, and cost saved."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from repopeek.models import SavingsMetrics


class TelemetryTracker:
    """Records context delivery events and computes counterfactual savings metrics."""

    def __init__(self, repopeek_dir: Path | str = ".repopeek"):
        self.repopeek_dir = Path(repopeek_dir).resolve()
        self.telemetry_dir = self.repopeek_dir / "telemetry"
        self.ledger_file = self.telemetry_dir / "savings.jsonl"
        self._ensure_storage()
        self._session_events: list[dict[str, Any]] = []

    def _ensure_storage(self) -> None:
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)

    def record_event(
        self,
        task: str,
        baseline_tokens: int,
        delivered_tokens: int,
        baseline_files: int,
        delivered_files: int,
        pricing_per_million: float = 3.0,
    ) -> dict[str, Any]:
        """Appends a new task savings event to the persistent ledger and active session memory."""
        tokens_saved = max(0, baseline_tokens - delivered_tokens)
        files_avoided = max(0, baseline_files - delivered_files)
        reduction_pct = round((tokens_saved / max(1, baseline_tokens)) * 100.0, 2)
        cost_saved_usd = round((tokens_saved / 1_000_000.0) * pricing_per_million, 4)

        event = {
            "timestamp": time.time(),
            "task": task,
            "baseline_tokens": baseline_tokens,
            "delivered_tokens": delivered_tokens,
            "tokens_saved": tokens_saved,
            "baseline_files": baseline_files,
            "delivered_files": delivered_files,
            "files_avoided": files_avoided,
            "reduction_pct": reduction_pct,
            "cost_saved_usd": cost_saved_usd,
        }

        self._session_events.append(event)
        try:
            with open(self.ledger_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except OSError:
            pass

        return event

    def get_summary(self, timeframe: str = "current_session") -> dict[str, Any]:
        """Aggregates metrics for the requested timeframe ('current_session' or 'all_time')."""
        events: list[dict[str, Any]] = []
        if timeframe == "current_session" or not self.ledger_file.exists():
            events = self._session_events
        else:
            try:
                with open(self.ledger_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            events.append(json.loads(line))
            except OSError:
                events = self._session_events

        if not events:
            return {
                "tasks_count": 0,
                "total_baseline_tokens": 0,
                "total_delivered_tokens": 0,
                "total_tokens_saved": 0,
                "total_files_avoided": 0,
                "total_cost_saved_usd": 0.0,
                "overall_reduction_pct": 0.0,
                "avg_pack_tokens": 0,
            }

        tasks_count = len(events)
        total_baseline = sum(e["baseline_tokens"] for e in events)
        total_delivered = sum(e["delivered_tokens"] for e in events)
        total_saved = sum(e["tokens_saved"] for e in events)
        total_avoided = sum(e["files_avoided"] for e in events)
        total_cost = sum(e["cost_saved_usd"] for e in events)
        overall_pct = round((total_saved / max(1, total_baseline)) * 100.0, 1)
        avg_delivered = total_delivered // max(1, tasks_count)

        return {
            "tasks_count": tasks_count,
            "total_baseline_tokens": total_baseline,
            "total_delivered_tokens": total_delivered,
            "total_tokens_saved": total_saved,
            "total_files_avoided": total_avoided,
            "total_cost_saved_usd": round(total_cost, 4),
            "overall_reduction_pct": overall_pct,
            "avg_pack_tokens": avg_delivered,
        }

    def render_ascii_card(self, event: dict[str, Any]) -> str:
        """Formats a single context delivery event as an ASCII efficiency scorecard."""
        task_str = (event.get("task") or "Engineering Task")[:55]
        return f"""+------------------------------------------------------------------------+
| REPOPEEK EFFICIENCY SCORECARD                                          |
| Task: {task_str:<55}  |
+------------------------------------------------------------------------+
| Context Delivered:   {event.get('delivered_files', 0):>2d} files | {event.get('delivered_tokens', 0):>6,d} tokens                         |
| Baseline Avoided:   {event.get('baseline_files', 0):>2d} files | {event.get('baseline_tokens', 0):>6,d} tokens                         |
| Tokens Saved:       {event.get('tokens_saved', 0):>6,d} tokens ({event.get('reduction_pct', 0.0):.1f}% reduction)              |
| Full Files Avoided: {event.get('files_avoided', 0):>2d} full files kept out of agent context            |
| Est. Cost Saved:    ${event.get('cost_saved_usd', 0.0):.4f} USD (based on $3.00/1M tokens)              |
+------------------------------------------------------------------------+"""

    def render_hud_markdown(self, summary: dict[str, Any]) -> str:
        """Renders cumulative session or all-time scoreboard in Markdown format."""
        return f"""# RepoPeek Context Efficiency & ROI Scoreboard

- **Total Agent Tasks Completed**: {summary['tasks_count']}
- **Cumulative Tokens Delivered**: {summary['total_delivered_tokens']:,} tokens
- **Counterfactual Full Baseline**: {summary['total_baseline_tokens']:,} tokens
- **Total Tokens Saved**: **{summary['total_tokens_saved']:,} tokens** ({summary['overall_reduction_pct']}% reduction)
- **Full Files Avoided**: **{summary['total_files_avoided']:,} files**
- **Net Dollar Cost Saved**: **${summary['total_cost_saved_usd']:.4f} USD**
- **Average Context Pack Size**: {summary['avg_pack_tokens']:,} tokens / task
"""


# Ponytail anti-hallucination verification self-test
if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        telemetry = TelemetryTracker(repopeek_dir=tmp_dir)
        evt = telemetry.record_event(
            task="Update invoice parser",
            baseline_tokens=50000,
            delivered_tokens=1500,
            baseline_files=15,
            delivered_files=3,
        )
        assert evt["tokens_saved"] == 48500
        assert evt["files_avoided"] == 12
        card = telemetry.render_ascii_card(evt)
        assert "REPOPEEK EFFICIENCY SCORECARD" in card

        summary = telemetry.get_summary()
        assert summary["tasks_count"] == 1
        assert summary["total_tokens_saved"] == 48500
        hud = telemetry.render_hud_markdown(summary)
        assert "Net Dollar Cost Saved" in hud
        print("repopeek.telemetry self-test passed!")
