# Inputs: orchestrator dependencies, queue jobs, and completed worker results for the Ledgerwise backend.
# Outputs: bounded worker and orchestration methods that return data or append state for the single writer.
# Explanation: Implements one focused orchestrator responsibility; D1 queue writes remain in tick commit stages.
from __future__ import annotations
from typing import Any
from .integrations import normalize_domain
from .orchestrator_helpers import _json, _parse_json_object

class ResearchWorkersMixin:
    async def _search_worker(self, job: dict[str, Any], run: dict[str, Any] | None, domains: list[str]) -> dict[str, Any]:
        async with self._llm_sem:
            prompt = (
                "Search the live web for organizations matching this ideal-customer selection. "
                f"Return JSON only: {{\"domains\":[\"example.com\"]}}. Find up to {int(job['n'])} "
                "unique company domains. Exclude these already used domains: "
                + _json(domains) + ". Selection: " + str((run or {}).get("selection", ""))
            )
            response = await self.muse.generate(prompt, use_search=True)
        data = _parse_json_object(response["text"]) or {}
        domains = []
        for value in data.get("domains", []):
            try:
                domains.append(normalize_domain(str(value)))
            except ValueError:
                continue
        return {
            "kind": "search",
            "queue_id": job["job_id"],
            "result": {
                "run_id": job["run_id"], "domains": list(dict.fromkeys(domains)),
                "input_tokens": response["input_tokens"], "output_tokens": response["output_tokens"],
            },
        }

    async def _enrichment_worker(self, job: dict[str, Any], company: dict[str, Any], run: dict[str, Any] | None) -> dict[str, Any]:
        async with self._llm_sem:
            prompt = (
                "Research this company using live web search. Return JSON only with company_id, domain, "
                "integer score 0..10, reasons (1-5 items each text/source_url/quote), and source_urls (max 5). "
                "Quotes must be verbatim evidence. Never invent facts. "
                f"company_id={company['id']} domain={company['domain']}. Selection={(run or {}).get('selection','')}"
            )
            response = await self.muse.generate(prompt, use_search=True)
        data = _parse_json_object(response["text"]) or {}
        try:
            domain = normalize_domain(str(data.get("domain", "")))
            reasons = data.get("reasons")
            urls = data.get("source_urls")
            valid = (
                int(data.get("company_id")) == int(company["id"])
                and domain == normalize_domain(str(company["domain"]))
                and type(data.get("score")) is int and 0 <= data["score"] <= 10
                and isinstance(reasons, list) and 1 <= len(reasons) <= 5
                and all(isinstance(r, dict) and all(str(r.get(k, "")).strip() for k in ("text", "source_url", "quote")) for r in reasons)
                and isinstance(urls, list)
            )
        except (TypeError, ValueError):
            valid = False
            reasons, urls = [], []
        valid_urls = []
        if valid:
            for url in urls[: self.settings.max_source_urls]:
                if isinstance(url, str) and url.startswith(("https://", "http://")):
                    valid_urls.append(url)
        valid = valid and bool(valid_urls)
        return {
            "kind": "enrichment", "company_id": int(company["id"]),
            "result": {
                "valid": valid, "score": data.get("score"), "reasons": reasons or [],
                "source_urls": valid_urls, "input_tokens": response["input_tokens"],
                "output_tokens": response["output_tokens"],
            },
        }

