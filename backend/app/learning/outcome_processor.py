"""Process V2 outcomes and update Hindsight memory (confirm / refine lessons)."""

from __future__ import annotations

from app.memory.hindsight_client import get_memory_client
from app.memory.schema import MemoryType, MemoryUnit, OutcomeInput, ProductVersion, RetainRequest


async def process_outcome(payload: OutcomeInput) -> MemoryUnit:
    """
    Retain a new outcome + lesson.
    This is how ProMaker learns: after V2 ships, the result becomes future evidence.
    """
    client = get_memory_client()

    title = f"V2 outcome: {payload.change_description[:60]}"
    content = (
        f"Implemented: {payload.implemented}\n"
        f"Customer response: {payload.customer_response}\n"
        f"Outcome: {payload.outcome}\n"
        f"Lesson: {payload.lesson}"
    )

    req = RetainRequest(
        content=content,
        memory_type=MemoryType.OUTCOME,
        product_version=payload.product_version,
        feature_area=payload.feature_area,
        tags=["v2", "outcome", "learning"],
        title=title,
        problem=None,
        decision=payload.change_description,
        experiment=payload.implemented,
        customer_reaction=payload.customer_response,
        outcome=payload.outcome,
        lesson=payload.lesson,
        metrics=payload.metrics,
        related_ids=payload.related_evidence_ids,
    )
    unit = await client.retain(req)

    # Also retain an explicit LESSON unit so future targeted recall finds it easily
    lesson_req = RetainRequest(
        content=payload.lesson,
        memory_type=MemoryType.LESSON,
        product_version=payload.product_version,
        feature_area=payload.feature_area,
        tags=["v2", "lesson", "updated"],
        title=f"Updated lesson: {payload.feature_area or 'product'}",
        lesson=payload.lesson,
        outcome=payload.outcome,
        decision=payload.change_description,
        related_ids=[unit.id] + payload.related_evidence_ids,
    )
    await client.retain(lesson_req)

    return unit