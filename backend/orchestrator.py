# Inputs: D1, provider clients, settings, worker queues, and mixin implementations for each tick phase.
# Outputs: Orchestrator with the existing public constructor, worker methods, status snapshot, and queue lifecycle.
# Explanation: Preserves backend.orchestrator.Orchestrator while delegating each bounded responsibility to a small module.
from .orchestrator_helpers import _json, _load, _now, _parse_json_object
from .orchestrator_core import OrchestratorCoreMixin
from .orchestrator_workers_research import ResearchWorkersMixin
from .orchestrator_workers_url import URLWorkersMixin
from .orchestrator_workers_outreach import OutreachWorkersMixin
from .orchestrator_workers_reply import ReplyWorkersMixin
from .orchestrator_workers_reply_tools import ReplyToolsMixin
from .orchestrator_tick_load import TickLoadMixin
from .orchestrator_tick_reconcile import TickReconcileMixin
from .orchestrator_tick_results import TickResultsMixin
from .orchestrator_tick_research_results import TickResearchResultsMixin
from .orchestrator_tick_url_results import TickURLResultsMixin
from .orchestrator_tick_outreach_results import TickOutreachResultsMixin
from .orchestrator_tick_reply_results import TickReplyResultsMixin
from .orchestrator_tick_plan import TickPlanMixin
from .orchestrator_tick_commit import TickCommitMixin

class Orchestrator(
    OrchestratorCoreMixin, TickLoadMixin, TickReconcileMixin, TickResultsMixin,
    TickResearchResultsMixin, TickURLResultsMixin, TickOutreachResultsMixin,
    TickReplyResultsMixin, TickPlanMixin, TickCommitMixin, ResearchWorkersMixin,
    URLWorkersMixin, OutreachWorkersMixin, ReplyWorkersMixin, ReplyToolsMixin,
):
    async def tick(self) -> None:
        state = await self._tick_load_state()
        self._tick_reconcile_state(state)
        self._tick_apply_finished_results(state)
        self._tick_plan_outreach(state)
        await self._tick_commit_state(state)
