"""Parse free-form V2 proposal text into discrete change items."""

from __future__ import annotations

import re
import uuid
from typing import Optional

from app.agent.llm import get_llm


FEATURE_KEYWORDS = {
    "onboarding": ["onboard", "tutorial", "setup wizard", "activation", "getting started", "first-run"],
    "checkout": ["checkout", "payment", "subscribe", "billing", "purchase", "pricing flow"],
    "search": ["search", "find", "sidebar", "navigation", "menu", "discover"],
    "recommendations": ["recommend", "suggestion", "ai-powered", "personaliz", "smart suggestion"],
}


def detect_feature_area(text: str) -> Optional[str]:
    lower = text.lower()
    for area, keys in FEATURE_KEYWORDS.items():
        if any(k in lower for k in keys):
            return area
    return None


def parse_proposal_heuristic(text: str) -> list[dict]:
    """Split proposal into changes without LLM (fast, reliable fallback)."""
    # Split on newlines, bullets, numbers
    lines = re.split(r"[\n\r]+", text.strip())
    changes = []
    for line in lines:
        cleaned = re.sub(r"^[\s\-\*\d\.\)\(]+", "", line).strip()
        if len(cleaned) < 8:
            continue
        # Skip pure headers
        if cleaned.lower() in ("product v2", "proposed changes", "changes", "v2 proposal"):
            continue
        changes.append(
            {
                "change_id": f"C-{uuid.uuid4().hex[:6].upper()}",
                "text": cleaned,
                "feature_area": detect_feature_area(cleaned),
            }
        )
    if not changes and text.strip():
        changes.append(
            {
                "change_id": f"C-{uuid.uuid4().hex[:6].upper()}",
                "text": text.strip(),
                "feature_area": detect_feature_area(text),
            }
        )
    return changes


async def parse_proposal(text: str) -> list[dict]:
    """
    Parse a product V2 proposal into individual changes.
    Uses heuristics first; optionally refines with LLM if available.
    """
    base = parse_proposal_heuristic(text)
    llm = get_llm()
    if not llm.available or len(base) <= 1:
        return base

    try:
        system = (
            "You are a precise product analyst. Given a product proposal, "
            "return a JSON object with key 'changes' — an array of objects, "
            "each with 'text' (the atomic proposed change, concise) and "
            "'feature_area' (one of: onboarding, checkout, search, recommendations, other)."
        )
        user = f"Proposal:\n{text}\n\nExtract each distinct proposed change."
        data = await llm.complete_json(system, user)
        parsed = data.get("changes") or []
        result = []
        for item in parsed:
            t = (item.get("text") or "").strip()
            if not t:
                continue
            area = item.get("feature_area")
            if area == "other":
                area = detect_feature_area(t)
            result.append(
                {
                    "change_id": f"C-{uuid.uuid4().hex[:6].upper()}",
                    "text": t,
                    "feature_area": area if area != "other" else detect_feature_area(t),
                }
            )
        return result or base
    except Exception:
        return base