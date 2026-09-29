"""
Local Hindsight-compatible memory store.
Stores structured decision stories and supports targeted semantic + keyword recall.
This implements the retain/recall interface so ProMaker can run fully offline for demos
while remaining drop-in compatible with real Hindsight when configured.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.memory.schema import (
    EvidenceState,
    MemoryType,
    MemoryUnit,
    ProductVersion,
    RecallResult,
    RetainRequest,
)

# Simple keyword + TF-style scoring (no heavy embedding dependency required at runtime)
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "must", "shall", "can", "this", "that", "these", "those", "it", "its", "they",
    "them", "their", "we", "our", "you", "your", "i", "me", "my", "not", "no", "yes",
}


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return {t for t in tokens if t not in STOPWORDS and len(t) > 2}


def _score(query_tokens: set[str], memory: MemoryUnit) -> float:
    if not query_tokens:
        return 0.0
    text = " ".join(
        filter(
            None,
            [
                memory.title,
                memory.content,
                memory.problem,
                memory.decision,
                memory.experiment,
                memory.customer_reaction,
                memory.outcome,
                memory.lesson,
                memory.feature_area or "",
                " ".join(memory.tags),
            ],
        )
    )
    mem_tokens = _tokenize(text)
    if not mem_tokens:
        return 0.0
    overlap = query_tokens & mem_tokens
    # Jaccard-ish + bonus for feature_area / tag exact match
    score = len(overlap) / max(len(query_tokens | mem_tokens), 1)
    if memory.feature_area and memory.feature_area.lower() in query_tokens:
        score += 0.35
    for tag in memory.tags:
        if tag.lower() in query_tokens:
            score += 0.15
    # Boost lessons and outcomes slightly for decision reasoning
    if memory.memory_type in (MemoryType.LESSON, MemoryType.OUTCOME):
        score += 0.05
    return score


class LocalMemoryStore:
    """Persistent local store that mimics Hindsight retain / recall."""

    def __init__(self, data_path: str | Path | None = None):
        if data_path is None:
            data_path = "/tmp/promaker_memories.json"
        self.data_path = Path(data_path)
        try:
            self.data_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            self.data_path = Path("/tmp/promaker_memories.json")
        self._memories: dict[str, MemoryUnit] = {}
        self._load()

    def _load(self) -> None:
        if self.data_path.exists():
            try:
                raw = json.loads(self.data_path.read_text(encoding="utf-8"))
                for item in raw:
                    m = MemoryUnit.model_validate(item)
                    self._memories[m.id] = m
            except Exception:
                self._memories = {}

    def _save(self) -> None:
        payload = [m.model_dump(mode="json") for m in self._memories.values()]
        self.data_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    def retain(self, req: RetainRequest) -> MemoryUnit:
        mid = f"M-{uuid.uuid4().hex[:6].upper()}"
        title = req.title or (req.content[:80] + ("…" if len(req.content) > 80 else ""))
        memory = MemoryUnit(
            id=mid,
            memory_type=req.memory_type or MemoryType.OUTCOME,
            product_version=req.product_version,
            title=title,
            content=req.content,
            problem=req.problem,
            decision=req.decision,
            experiment=req.experiment,
            customer_reaction=req.customer_reaction,
            outcome=req.outcome,
            lesson=req.lesson,
            tags=req.tags,
            feature_area=req.feature_area,
            metrics=req.metrics,
            related_ids=req.related_ids,
            created_at=datetime.utcnow(),
            source="user",
        )
        self._memories[mid] = memory
        self._save()
        return memory

    def retain_unit(self, unit: MemoryUnit) -> MemoryUnit:
        self._memories[unit.id] = unit
        self._save()
        return unit

    def recall(
        self,
        query: str,
        feature_area: Optional[str] = None,
        memory_types: Optional[list[MemoryType]] = None,
        product_version: Optional[ProductVersion] = None,
        top_k: int = 8,
        min_score: float = 0.08,
    ) -> RecallResult:
        q_tokens = _tokenize(query)
        if feature_area:
            q_tokens.add(feature_area.lower())

        scored: list[tuple[float, MemoryUnit]] = []
        for m in self._memories.values():
            if memory_types and m.memory_type not in memory_types:
                continue
            if product_version and m.product_version != product_version:
                # Still allow related versions; soft filter later
                pass
            s = _score(q_tokens, m)
            if feature_area and m.feature_area and m.feature_area.lower() == feature_area.lower():
                s += 0.4
            if s >= min_score:
                scored.append((s, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [m for _, m in scored[:top_k]]

        if len(top) >= 3:
            state = EvidenceState.STRONG
        elif len(top) >= 1:
            state = EvidenceState.LIMITED
        else:
            state = EvidenceState.INSUFFICIENT

        return RecallResult(
            memories=top,
            query=query,
            evidence_state=state,
            total_found=len(top),
        )

    def get(self, memory_id: str) -> Optional[MemoryUnit]:
        return self._memories.get(memory_id)

    def list_all(self) -> list[MemoryUnit]:
        return sorted(self._memories.values(), key=lambda m: m.created_at)

    def list_timeline(self) -> list[MemoryUnit]:
        """Return memories ordered for timeline (decision stories first)."""
        order = {
            MemoryType.DECISION: 0,
            MemoryType.EXPERIMENT: 1,
            MemoryType.FEEDBACK: 2,
            MemoryType.OUTCOME: 3,
            MemoryType.LESSON: 4,
            MemoryType.HABIT: 5,
            MemoryType.FEATURE: 6,
            MemoryType.WORKFLOW: 7,
        }
        return sorted(
            self._memories.values(),
            key=lambda m: (m.product_version.value, order.get(m.memory_type, 9), m.created_at),
        )

    def count(self) -> int:
        return len(self._memories)

    def clear(self) -> None:
        self._memories = {}
        self._save()


# Singleton for the process
_store: Optional[LocalMemoryStore] = None


def get_local_store() -> LocalMemoryStore:
    global _store
    if _store is None:
        _store = LocalMemoryStore()
    return _store