# Inputs: tick state, completed worker results, queue snapshots, and usage events from the orchestrator.
# Outputs: updated tick state, committed queue transitions, refreshed status, and dispatched work.
# Explanation: Implements one bounded phase of the single-writer orchestration cycle.
from __future__ import annotations
from typing import Any

class TickResultsMixin:
    def _tick_apply_finished_results(self, state: dict[str, Any]) -> None:
        finished, self.finished = self.finished, []
        for item in finished:
            kind = item.get("kind")
            if kind == "search":
                self._apply_search_result(state, item)
            elif kind == "enrichment":
                self._apply_enrichment_result(state, item)
            elif kind == "url_check":
                self._apply_url_result(state, item)
            elif kind == "apollo":
                self._apply_apollo_result(state, item)
            elif kind == "draft":
                self._apply_draft_result(state, item)
            elif kind == "send":
                self._apply_send_result(state, item)
            elif kind == "reply":
                self._apply_reply_result(state, item)
