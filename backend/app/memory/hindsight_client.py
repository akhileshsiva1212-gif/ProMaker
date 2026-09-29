"""
Unified memory client.
- Prefer real Hindsight when HINDSIGHT_BASE_URL + API_KEY are set.
- Otherwise use LocalMemoryStore (fully functional offline demo).
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config import get_settings
from app.memory.local_store import get_local_store
from app.memory.schema import (
    EvidenceState,
    MemoryType,
    MemoryUnit,
    ProductVersion,
    RecallResult,
    RetainRequest,
)

logger = logging.getLogger("promaker.memory")


class HindsightClient:
    """Thin adapter over real Hindsight HTTP API or local store."""

    def __init__(self):
        self.settings = get_settings()
        self.local = get_local_store()
        self._http: Optional[httpx.AsyncClient] = None

    @property
    def using_real(self) -> bool:
        return self.settings.use_real_hindsight

    async def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            headers = {}
            if self.settings.hindsight_api_key:
                headers["Authorization"] = f"Bearer {self.settings.hindsight_api_key}"
            self._http = httpx.AsyncClient(
                base_url=self.settings.hindsight_base_url.rstrip("/"),
                headers=headers,
                timeout=30.0,
            )
        return self._http

    async def retain(self, req: RetainRequest) -> MemoryUnit:
        # Always also keep a structured local copy for the UI timeline & evidence IDs
        unit = self.local.retain(req)

        if self.using_real:
            try:
                client = await self._client()
                # Real Hindsight expects free-form content; we send the story narrative
                content = unit.to_story_text()
                await client.post(
                    f"/v1/default/banks/{self.settings.hindsight_bank_id}/retain",
                    json={"content": content, "document_id": unit.id},
                )
            except Exception as e:
                logger.warning("Real Hindsight retain failed, local copy kept: %s", e)

        return unit

    async def retain_unit(self, unit: MemoryUnit) -> MemoryUnit:
        self.local.retain_unit(unit)
        if self.using_real:
            try:
                client = await self._client()
                await client.post(
                    f"/v1/default/banks/{self.settings.hindsight_bank_id}/retain",
                    json={"content": unit.to_story_text(), "document_id": unit.id},
                )
            except Exception as e:
                logger.warning("Real Hindsight retain_unit failed: %s", e)
        return unit

    async def recall(
        self,
        query: str,
        feature_area: Optional[str] = None,
        memory_types: Optional[list[MemoryType]] = None,
        product_version: Optional[ProductVersion] = None,
        top_k: int = 8,
    ) -> RecallResult:
        # Primary path: structured local recall (deterministic + explainable IDs)
        local_result = self.local.recall(
            query=query,
            feature_area=feature_area,
            memory_types=memory_types,
            product_version=product_version,
            top_k=top_k,
        )

        if self.using_real and local_result.evidence_state == EvidenceState.INSUFFICIENT:
            # Attempt enrichment from real Hindsight
            try:
                client = await self._client()
                resp = await client.post(
                    f"/v1/default/banks/{self.settings.hindsight_bank_id}/recall",
                    json={"query": query, "max_tokens": 4096},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    # Map free-form results into synthetic MemoryUnits if needed
                    # (for now we trust local structured memory as source of truth for IDs)
                    logger.info("Hindsight recall returned %s items", len(data.get("results", [])))
            except Exception as e:
                logger.warning("Real Hindsight recall failed: %s", e)

        return local_result

    def get(self, memory_id: str) -> Optional[MemoryUnit]:
        return self.local.get(memory_id)

    def list_timeline(self) -> list[MemoryUnit]:
        return self.local.list_timeline()

    def list_all(self) -> list[MemoryUnit]:
        return self.local.list_all()

    def count(self) -> int:
        return self.local.count()

    def clear(self) -> None:
        self.local.clear()


_client: Optional[HindsightClient] = None


def get_memory_client() -> HindsightClient:
    global _client
    if _client is None:
        _client = HindsightClient()
    return _client