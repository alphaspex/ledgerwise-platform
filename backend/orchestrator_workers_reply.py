# Inputs: orchestrator dependencies, queue jobs, and completed worker results for the Ledgerwise backend.
# Outputs: bounded worker and orchestration methods that return data or append state for the single writer.
# Explanation: Implements one focused orchestrator responsibility; D1 queue writes remain in tick commit stages.
from __future__ import annotations
import re
from typing import Any
from .orchestrator_helpers import _json, _load

class ReplyWorkersMixin:
    async def _reply_worker(self, job: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
        async with self._reply_sem:
            inbound = str(job.get("message_body") or "")
            stop = bool(re.search(r"\b(stop|unsubscribe|not interested|remove me|don't contact|do not contact)\b", inbound, re.I))
            if stop or job.get("do_not_contact"):
                return {"kind": "reply", "queue_id": int(job["queue_id"]), "company_id": int(job["company_id"]), "result": {"stop": True}}
            if job.get("thread_state") in {"human_taken_over", "needs_human", "closed"}:
                return {"kind": "reply", "queue_id": int(job["queue_id"]), "company_id": int(job["company_id"]), "result": {"cancelled": True}}
            prospect_messages = [row for row in history if row.get("sender_type") == "prospect"]
            if prospect_messages and int(prospect_messages[-1]["id"]) != int(job.get("message_id") or 0):
                return {"kind": "reply", "queue_id": int(job["queue_id"]), "company_id": int(job["company_id"]), "result": {"cancelled": True}}
            safe_history = [
                {"sender": row.get("sender_type"), "body": row.get("body")}
                for row in history[-self.settings.reply_context_window:]
            ]
            tools = [
                {
                    "type": "function",
                    "name": "check_availability",
                    "description": "Check available Ledgerwise meeting slots for the next two weeks. Use before offering or booking a time.",
                    "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
                },
                {
                    "type": "function",
                    "name": "book_slot",
                    "description": "Book one available meeting slot for this prospect. Only use a slot returned by check_availability.",
                    "parameters": {
                        "type": "object",
                        "properties": {"start_time": {"type": "string", "description": "Exact ISO date-time returned by check_availability"}},
                        "required": ["start_time"],
                        "additionalProperties": False,
                    },
                },
                {
                    "type": "function",
                    "name": "call_human",
                    "description": "Escalate the conversation to a human when the answer is uncertain or the prospect asks for a person.",
                    "parameters": {
                        "type": "object",
                        "properties": {"reason": {"type": "string"}},
                        "required": ["reason"],
                        "additionalProperties": False,
                    },
                },
            ]
            prompt = (
                "Reply to the prospect as Ledgerwise's AI assistant. Be honest that you are an AI if asked. "
                "Never quote prices. Every factual claim must be supported by verified company memory or research. "
                "Do not invent details. Use check_availability before offering a meeting time; use book_slot only "
                "with an exact returned slot. If a slot was taken, check availability again and retry one time only. "
                "If booking still fails, share the configured public booking link when available. If unsure or asked "
                "for a person, call call_human and provide one brief handoff sentence. Do not reply to stop signals. "
                f"Maximum {self.settings.reply_max_words} words. Contact role: {job.get('contact_role')}. "
                f"Verified memory: {_json(_load(job.get('memory'), {'facts': []}))}. "
                f"Conversation: {_json(safe_history)}. Latest prospect message: {inbound}"
            )
            response = await self.muse.generate(prompt, use_search=False, tools=tools)
            result = await self._run_reply_tool_loop(response, job, tools)
            return {
                "kind": "reply",
                "queue_id": int(job["queue_id"]),
                "company_id": int(job["company_id"]),
                "result": result,
            }
        
