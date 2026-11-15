# Inputs: orchestrator dependencies, queue jobs, and completed worker results for the Ledgerwise backend.
# Outputs: bounded worker and orchestration methods that return data or append state for the single writer.
# Explanation: Implements one focused orchestrator responsibility; D1 queue writes remain in tick commit stages.
from __future__ import annotations
import json
from typing import Any
from .orchestrator_helpers import _json

class ReplyToolsMixin:
    async def _run_reply_tool_loop(self, response: dict[str, Any], job: dict[str, Any], tools: list[dict[str, Any]]) -> dict[str, Any]:
        tool_calls: list[dict[str, Any]] = []
        booking: dict[str, Any] | None = None
        available_start_times: set[str] = set()
        needs_human = False
        human_reason: str | None = None
        book_attempts = 0
        for _ in range(5):
            function_calls = response.get("function_calls", [])
            if not function_calls:
                break
            outputs = []
            for call in function_calls:
                name = str(call.get("name") or "")
                try:
                    args = json.loads(call.get("arguments") or "{}")
                except (TypeError, json.JSONDecodeError):
                    args = {}
                result: dict[str, Any]
                if name == "check_availability":
                    try:
                        slots = await self.calcom.check_availability()
                        available_start_times = {
                            str(slot.get("start") or slot.get("startTime") or slot.get("time"))
                            for slot in slots
                            if slot.get("start") or slot.get("startTime") or slot.get("time")
                        }
                        result = {"success": True, "slots": slots}
                    except Exception:
                        result = {"success": False, "error": "availability_unavailable"}
                elif name == "book_slot":
                    book_attempts += 1
                    start_time = str(args.get("start_time") or "")
                    if not start_time:
                        booked = {"success": False, "error": "missing_start_time"}
                    elif start_time not in available_start_times:
                        booked = {"success": False, "error": "slot_not_returned_by_availability_check"}
                    else:
                        try:
                            booked = await self.calcom.book_slot(
                                start_time=start_time,
                                email=str(job.get("contact_email") or ""),
                                name=str(job.get("contact_name") or ("Contact at " + str(job.get("domain") or "company"))),
                            )
                        except Exception:
                            booked = {"success": False, "error": "booking_unavailable"}
                    result = booked
                    if booked.get("success") and booked.get("uid"):
                        booking = {"uid": str(booked["uid"]), "scheduled_at": start_time}
                    elif booked.get("error") == "slot_taken" and book_attempts < 2:
                        try:
                            result["available_slots"] = await self.calcom.check_availability()
                            available_start_times = {
                                str(slot.get("start") or slot.get("startTime") or slot.get("time"))
                                for slot in result["available_slots"]
                                if slot.get("start") or slot.get("startTime") or slot.get("time")
                            }
                        except Exception:
                            result["available_slots"] = []
                            available_start_times = set()
                    elif not booked.get("success"):
                        result["booking_link"] = self.settings.calcom_public_booking_url or None
                elif name == "call_human":
                    needs_human = True
                    human_reason = str(args.get("reason") or "A human response was requested.")
                    result = {"success": True, "handoff": True}
                else:
                    result = {"success": False, "error": "unknown_tool"}
                tool_calls.append({"name": name, "args": args, "result": result})
                outputs.append({
                    "type": "function_call_output",
                    "call_id": str(call.get("call_id") or ""),
                    "output": _json(result),
                })
            response_id = response.get("response_id")
            if not response_id or not outputs:
                break
            response = await self.muse.generate(
                use_search=False,
                tools=tools,
                previous_response_id=str(response_id),
                input_override=outputs,
            )
        body = response.get("text", "").strip()
        needs_human = needs_human or "let me bring in a colleague" in body.lower()
        if not body:
            body = "Thanks for your message. Let me bring in a colleague to help with this."
            needs_human = True
            human_reason = human_reason or "The agent could not prepare a safe response."
        if len(body.split()) > self.settings.reply_max_words:
            body = "Thanks for your message. Let me bring in a colleague to help with this."
            needs_human = True
            human_reason = human_reason or "The generated reply exceeded the response limit."

        return {
            "body": body,
            "needs_human": needs_human,
            "human_reason": human_reason,
            "tool_calls": tool_calls,
            "booking": booking,
        }
