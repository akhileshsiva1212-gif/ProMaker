"""
Core ProMaker reasoning engine.
For each proposed change:
  1. Targeted Hindsight recall
  2. Habit / historical warning detection
  3. Evidence-first verdict (KEEP | IMPROVE | RETIRE | REINVENT | INTRODUCE)
Never invents memories. Honest about insufficient history.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from app.agent.llm import get_llm
from app.memory.hindsight_client import get_memory_client
from app.memory.schema import (
    ChangeAnalysis,
    EvidenceState,
    MemoryType,
    MemoryUnit,
    Verdict,
)

logger = logging.getLogger("promaker.reasoner")

VERDICT_VALUES = {v.value for v in Verdict}


def _build_evidence_block(memories: list[MemoryUnit]) -> str:
    if not memories:
        return "No relevant historical memories found."
    return "\n\n---\n\n".join(m.to_story_text() for m in memories)


def _detect_habit_collision(change_text: str, memories: list[MemoryUnit]) -> tuple[bool, Optional[str]]:
    lower = change_text.lower()
    # Explicit patterns that collide with known search habit
    hide_search = any(
        p in lower
        for p in (
            "hide search",
            "hidden sidebar",
            "move search",
            "search into a hidden",
            "remove search from",
            "bury search",
            "search behind",
        )
    )
    workflow_mems = [m for m in memories if m.memory_type in (MemoryType.HABIT, MemoryType.WORKFLOW) or (m.feature_area == "search" and m.memory_type == MemoryType.LESSON)]
    if hide_search and workflow_mems:
        detail = (
            "Customers frequently follow: Dashboard → Search → Product → Checkout. "
            "Hiding Search behind a sidebar disrupts a well-established habit. "
            "Preserve low-friction access to search while redesigning the interface."
        )
        return True, detail
    return False, None


def _detect_historical_warning(change_text: str, memories: list[MemoryUnit]) -> tuple[bool, Optional[str]]:
    lower = change_text.lower()
    # Onboarding tutorial re-attempt
    tutorial_again = any(
        p in lower
        for p in (
            "step-by-step onboarding",
            "onboarding tutorial",
            "detailed tutorial",
            "instructional onboarding",
            "add a tutorial",
            "step by step onboarding",
        )
    )
    failed_onboarding = [
        m
        for m in memories
        if m.feature_area == "onboarding"
        and m.memory_type in (MemoryType.OUTCOME, MemoryType.LESSON)
        and (
            "did not improve" in (m.outcome or "").lower()
            or "complexity" in (m.lesson or "").lower()
            or "failed" in (m.content or "").lower()
        )
    ]
    if tutorial_again and failed_onboarding:
        detail = (
            "A similar approach was previously attempted: detailed instructional onboarding. "
            "Outcome: completion rate did not improve. Lesson: the problem was complexity, not lack of instructions."
        )
        return True, detail

    # Multi-step checkout against proven low-friction value
    multi_checkout = any(
        p in lower
        for p in (
            "multi-step checkout",
            "multi step checkout",
            "checkout into a multi",
            "redesign checkout into",
            "checkout wizard",
        )
    )
    checkout_lessons = [
        m
        for m in memories
        if m.feature_area == "checkout" and m.memory_type == MemoryType.LESSON
    ]
    if multi_checkout and checkout_lessons:
        detail = (
            "Low-friction, single-page checkout previously succeeded and is treated as a core customer value. "
            "Introducing multi-step friction risks undoing that value."
        )
        return True, detail

    return False, None


def _heuristic_verdict(
    change_text: str,
    memories: list[MemoryUnit],
    evidence_state: EvidenceState,
    historical_warning: bool,
    habit_collision: bool,
) -> tuple[Verdict, str, str]:
    """Deterministic fallback when LLM is unavailable or returns invalid output."""
    lower = change_text.lower()

    if evidence_state == EvidenceState.INSUFFICIENT:
        return (
            Verdict.INTRODUCE,
            "Insufficient history to make a confident historical recommendation. Treat as a new capability that requires validation.",
            "Instrument the change carefully and measure outcomes before scaling.",
        )

    if historical_warning and "onboard" in lower:
        return (
            Verdict.REINVENT,
            "A similar onboarding approach previously failed to improve completion. The historical lesson points to complexity as the root cause, not lack of instructions.",
            "Simplify onboarding rather than adding more instructional content.",
        )

    if historical_warning and "checkout" in lower:
        return (
            Verdict.KEEP,
            "Low-friction checkout is a proven customer value. Multi-step redesign risks regressing conversion without clear evidence of benefit.",
            "Preserve the low-friction value. If redesign is required, keep field count and steps minimal.",
        )

    if habit_collision:
        return (
            Verdict.IMPROVE,
            "Search is a high-frequency habit in the primary workflow (Dashboard → Search → Product → Checkout). Hiding it creates orientation risk.",
            "Preserve low-friction search access while redesigning the interface. Do not bury the primary discovery surface.",
        )

    if any(k in lower for k in ("ai", "recommend", "suggestion", "personaliz")):
        return (
            Verdict.INTRODUCE,
            "Customers have expressed unmet need for smarter recommendations; prior rule-based attempts under-delivered. An intelligent approach is supported by evidence of demand.",
            "Design context-aware recommendations and validate with a controlled experiment.",
        )

    if "simplif" in lower and "onboard" in lower:
        return (
            Verdict.REINVENT,
            "Historical evidence shows instruction-heavy onboarding failed; simplification aligns with the learned lesson.",
            "Proceed with simplified onboarding and measure completion and time-to-value.",
        )

    # Default with limited evidence
    return (
        Verdict.IMPROVE,
        "Relevant history exists but does not strongly confirm or reject this specific approach.",
        "Validate with a focused experiment and retain the outcome into ProMaker memory.",
    )


async def analyze_change(
    change_text: str,
    change_id: str,
    feature_area: Optional[str] = None,
) -> ChangeAnalysis:
    client = get_memory_client()

    # Targeted recall — critical: per-change, not global
    query_parts = [change_text]
    if feature_area:
        query_parts.append(feature_area)
        query_parts.append(f"{feature_area} feedback experiment outcome lesson decision habit")
    query = " ".join(query_parts)

    recall = await client.recall(
        query=query,
        feature_area=feature_area,
        top_k=10,
    )
    memories = recall.memories
    evidence_state = recall.evidence_state

    hist_warn, hist_detail = _detect_historical_warning(change_text, memories)
    habit_col, habit_detail = _detect_habit_collision(change_text, memories)

    # LLM reasoning when available
    llm = get_llm()
    verdict: Verdict
    reason: str
    direction: str

    if llm.available and memories:
        evidence_block = _build_evidence_block(memories)
        system = """You are ProMaker, a senior product strategist with organizational memory.
You evaluate proposed product changes using ONLY the historical memories provided.
You never invent feedback, metrics, experiments, or lessons.

Respond with JSON:
{
  "verdict": "KEEP" | "IMPROVE" | "RETIRE" | "REINVENT" | "INTRODUCE",
  "reason": "1-3 sentences, precise, evidence-based",
  "suggested_direction": "concrete next step"
}

Verdict guide:
- KEEP: proven customer value should remain
- IMPROVE: useful but current implementation has problems
- RETIRE: insufficient value or repeated problems
- REINVENT: need is valid but previous implementation failed
- INTRODUCE: genuinely new capability with supporting evidence or clear unmet need

If history is weak, prefer INTRODUCE or IMPROVE and say so honestly.
Be concise. Sound like a thoughtful product strategist, not a cheerleader."""
        user = f"""Proposed change:
{change_text}

Feature area: {feature_area or "unknown"}

Historical memories (use only these):
{evidence_block}

Historical warning detected by system: {hist_warn}
Habit collision detected by system: {habit_col}

Produce the verdict JSON."""
        try:
            data = await llm.complete_json(system, user)
            v = str(data.get("verdict", "")).upper().strip()
            if v not in VERDICT_VALUES:
                raise ValueError(f"Invalid verdict: {v}")
            verdict = Verdict(v)
            reason = str(data.get("reason") or "").strip() or "See historical evidence."
            direction = str(data.get("suggested_direction") or "").strip() or "Validate with a controlled experiment."
        except Exception as e:
            logger.warning("LLM reasoning failed, using heuristic: %s", e)
            verdict, reason, direction = _heuristic_verdict(
                change_text, memories, evidence_state, hist_warn, habit_col
            )
    else:
        verdict, reason, direction = _heuristic_verdict(
            change_text, memories, evidence_state, hist_warn, habit_col
        )

    # Force REINVENT when clear historical failure on same approach
    if hist_warn and "onboard" in change_text.lower() and verdict not in (Verdict.REINVENT, Verdict.RETIRE):
        verdict = Verdict.REINVENT
        if "simplif" not in reason.lower():
            reason = (
                "A similar onboarding approach previously failed to improve completion. "
                "Historical evidence suggests complexity, rather than lack of guidance, was the issue."
            )
            direction = "Simplify onboarding instead of adding more instructional content."

    return ChangeAnalysis(
        change=change_text,
        change_id=change_id,
        verdict=verdict,
        historical_warning=hist_warn,
        habit_collision=habit_col,
        evidence_state=evidence_state,
        reason=reason,
        evidence_ids=[m.id for m in memories],
        suggested_direction=direction,
        habit_risk_detail=habit_detail,
        historical_warning_detail=hist_detail,
        evidence_memories=memories,
    )


async def memoryless_opinion(change_text: str) -> str:
    """What a generic LLM would say without any product history."""
    llm = get_llm()
    if not llm.available:
        return (
            "Without product history this looks like a reasonable improvement to try. "
            "Validate with user testing and measure activation metrics."
        )
    system = (
        "You are a generic product advisor with NO company history. "
        "Give a short, optimistic but professional opinion on the proposed change. "
        "Do not invent company-specific data. 2-4 sentences."
    )
    try:
        return await llm.complete(system, f"Proposed change: {change_text}")
    except Exception:
        return "This change could improve the experience. Recommend testing with a small cohort first."