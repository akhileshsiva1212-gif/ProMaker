"""LLM client with structured output support. Provider configurable via env."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional, Type, TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger("promaker.llm")
T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def __init__(self):
        self.settings = get_settings()
        kwargs: dict[str, Any] = {"api_key": self.settings.llm_api_key or "sk-placeholder"}
        if self.settings.llm_base_url:
            kwargs["base_url"] = self.settings.llm_base_url
        self.client = AsyncOpenAI(**kwargs)
        self.model = self.settings.llm_model

    @property
    def available(self) -> bool:
        return bool(self.settings.llm_api_key)

    async def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> str:
        if not self.available:
            raise RuntimeError("LLM_API_KEY is not configured")
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""

    async def complete_json(
        self,
        system: str,
        user: str,
        schema: Optional[Type[T]] = None,
        temperature: float = 0.15,
    ) -> dict[str, Any]:
        """Ask for JSON. Optionally validate against a Pydantic model."""
        system_json = (
            system
            + "\n\nYou MUST respond with valid JSON only. No markdown fences, no commentary."
        )
        raw = await self.complete(system_json, user, temperature=temperature)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            if raw.endswith("```"):
                raw = raw[: raw.rfind("```")]
        data = json.loads(raw)
        if schema:
            return schema.model_validate(data).model_dump()
        return data


_llm: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    global _llm
    if _llm is None:
        _llm = LLMClient()
    return _llm