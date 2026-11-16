# Inputs: orchestrator dependencies, queue jobs, and completed worker results for the Ledgerwise backend.
# Outputs: bounded worker and orchestration methods that return data or append state for the single writer.
# Explanation: Implements one focused orchestrator responsibility; D1 queue writes remain in tick commit stages.
from __future__ import annotations
import asyncio
import time
from contextvars import ContextVar
from typing import Any
from .config import Settings
from .db import D1Client
from .integrations import ApolloClient, CalComClient, MuseClient, ResendClient

class OrchestratorCoreMixin:
    def __init__(
        self,
        db: D1Client,
        settings: Settings,
        muse: MuseClient,
        resend: ResendClient,
        apollo: ApolloClient,
        calcom: CalComClient,
    ):
        self.db = db
        self.settings = settings
        self.muse = muse
        self._usage_context: ContextVar[dict[str, Any]] = ContextVar("ledgerwise_usage_context", default={})
        self.usage_pending: list[dict[str, Any]] = []
        self.muse.set_usage_callback(self._record_model_usage)
        self.resend = resend
        self.apollo = apollo
        self.calcom = calcom
        self.finished: list[dict[str, Any]] = []
        self.inflight: set[asyncio.Task] = set()
        self.message_waiters: dict[int, asyncio.Future] = {}
        self.tick_count = 0
        self.snapshot: dict[str, Any] = {
            "run": None,
            "counts": {},
            "progress": {"search_jobs": 0},
            "tokens": {"in": 0, "out": 0},
            "searches": 0,
        }
        self._llm_sem = asyncio.Semaphore(settings.llm_concurrency)
        self._http_sem = asyncio.Semaphore(settings.http_concurrency)
        self._draft_sem = asyncio.Semaphore(settings.draft_concurrency)
        self._send_sem = asyncio.Semaphore(settings.send_concurrency)
        self._reply_sem = asyncio.Semaphore(settings.reply_concurrency)
        self._host_locks: dict[str, asyncio.Lock] = {}
        self._host_last_request: dict[str, float] = {}

    def _record_model_usage(self, usage: dict[str, Any]) -> None:
        context = self._usage_context.get()
        self.usage_pending.append({
            "model": str(usage.get("model") or self.settings.muse_model),
            "module": str(context.get("module") or "unattributed"),
            "operation": str(context.get("operation") or "generate"),
            "company_id": context.get("company_id"),
            "run_id": context.get("run_id"),
            "input_tokens": int(usage.get("input_tokens", 0) or 0),
            "output_tokens": int(usage.get("output_tokens", 0) or 0),
            "reasoning_tokens": int(usage.get("reasoning_tokens", 0) or 0),
        })

    async def run_forever(self) -> None:
        while True:
            started = time.monotonic()
            try:
                await self.tick()
            except Exception:
                await asyncio.sleep(min(2.0, self.settings.tick_seconds))
            delay = max(0.0, self.settings.tick_seconds - (time.monotonic() - started))
            await asyncio.sleep(delay)

    def _dispatch(self, coroutine, name: str, failure_result: dict[str, Any] | None = None) -> None:
        frame = getattr(coroutine, "cr_frame", None)
        local_values = frame.f_locals if frame else {}
        worker_name = frame.f_code.co_name if frame else ""
        job = local_values.get("job") or {}
        company = local_values.get("company") or {}
        run = local_values.get("run") or {}
        usage_modules = {
            "_search_worker": ("research", "search"),
            "_enrichment_worker": ("research", "enrichment"),
            "_draft_worker": ("outreach", "draft"),
            "_reply_worker": ("conversations", "reply"),
        }
        module, operation = usage_modules.get(worker_name, ("unattributed", worker_name or "worker"))
        context = {
            "module": module,
            "operation": operation,
            "company_id": job.get("company_id") or company.get("id"),
            "run_id": job.get("run_id") or run.get("id"),
        }
        token = self._usage_context.set(context)
        try:
            task = asyncio.create_task(coroutine, name=name)
        finally:
            self._usage_context.reset(token)
        self.inflight.add(task)

        def completed(done: asyncio.Task) -> None:
            self.inflight.discard(done)
            try:
                self.finished.append(done.result())
            except Exception as exc:
                failure = dict(failure_result or {})
                failure.setdefault("kind", "worker_error")
                failure["error"] = str(exc)
                if isinstance(failure.get("result"), dict):
                    failure["result"] = {**failure["result"], "worker_error": True, "error": str(exc)}
                else:
                    failure["result"] = {"worker_error": True, "error": str(exc)}
                self.finished.append(failure)

        task.add_done_callback(completed)

    async def _resolve_waiters(self, completions: list[tuple[int, str]]) -> None:
        for message_id, status in completions:
            future = self.message_waiters.pop(message_id, None)
            if future and not future.done():
                future.set_result(status)

    def register_message_waiter(self, message_id: int) -> asyncio.Future:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.message_waiters[message_id] = future
        return future

    def release_message_waiter(self, message_id: int, future: asyncio.Future) -> None:
        if self.message_waiters.get(message_id) is future:
            self.message_waiters.pop(message_id, None)
