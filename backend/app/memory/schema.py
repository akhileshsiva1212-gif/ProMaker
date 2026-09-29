"""Memory schema for ProMaker decision stories."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    FEEDBACK = "feedback"
    HABIT = "habit"
    EXPERIMENT = "experiment"
    OUTCOME = "outcome"
    LESSON = "lesson"
    DECISION = "decision"
    FEATURE = "feature"
    WORKFLOW = "workflow"


class EvidenceState(str, Enum):
    STRONG = "strong"
    LIMITED = "limited"
    INSUFFICIENT = "insufficient"


class Verdict(str, Enum):
    KEEP = "KEEP"
    IMPROVE = "IMPROVE"
    RETIRE = "RETIRE"
    REINVENT = "REINVENT"
    INTRODUCE = "INTRODUCE"


class ProductVersion(str, Enum):
    V1 = "V1"
    V2 = "V2"
    V3 = "V3"


class MemoryUnit(BaseModel):
    """A single atomic memory that can be retained and recalled."""

    id: str
    memory_type: MemoryType
    product_version: ProductVersion = ProductVersion.V1
    title: str
    content: str
    # Structured decision story fields (when applicable)
    problem: Optional[str] = None
    decision: Optional[str] = None
    experiment: Optional[str] = None
    customer_reaction: Optional[str] = None
    outcome: Optional[str] = None
    lesson: Optional[str] = None
    # Metadata
    tags: list[str] = Field(default_factory=list)
    feature_area: Optional[str] = None  # onboarding, checkout, search, recommendations, ...
    metrics: dict[str, Any] = Field(default_factory=dict)
    related_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = "seed"

    def to_story_text(self) -> str:
        """Render as a coherent narrative for LLM context."""
        parts = [f"[{self.id}] {self.memory_type.value.upper()} — {self.title}"]
        if self.product_version:
            parts.append(f"Product version: {self.product_version.value}")
        if self.feature_area:
            parts.append(f"Feature area: {self.feature_area}")
        if self.problem:
            parts.append(f"Problem: {self.problem}")
        if self.decision:
            parts.append(f"Decision: {self.decision}")
        if self.experiment:
            parts.append(f"Experiment: {self.experiment}")
        if self.customer_reaction:
            parts.append(f"Customer reaction: {self.customer_reaction}")
        if self.outcome:
            parts.append(f"Outcome: {self.outcome}")
        if self.lesson:
            parts.append(f"Lesson: {self.lesson}")
        if self.content and self.content not in (self.problem, self.decision, self.outcome, self.lesson):
            parts.append(f"Details: {self.content}")
        if self.metrics:
            metric_str = ", ".join(f"{k}={v}" for k, v in self.metrics.items())
            parts.append(f"Metrics: {metric_str}")
        if self.tags:
            parts.append(f"Tags: {', '.join(self.tags)}")
        return "\n".join(parts)


class RecallResult(BaseModel):
    memories: list[MemoryUnit]
    query: str
    evidence_state: EvidenceState
    total_found: int


class RetainRequest(BaseModel):
    content: str
    memory_type: Optional[MemoryType] = None
    product_version: ProductVersion = ProductVersion.V2
    feature_area: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    # Structured fields for decision stories
    problem: Optional[str] = None
    decision: Optional[str] = None
    experiment: Optional[str] = None
    customer_reaction: Optional[str] = None
    outcome: Optional[str] = None
    lesson: Optional[str] = None
    title: Optional[str] = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    related_ids: list[str] = Field(default_factory=list)


class ChangeAnalysis(BaseModel):
    change: str
    change_id: str
    verdict: Verdict
    historical_warning: bool = False
    habit_collision: bool = False
    evidence_state: EvidenceState
    reason: str
    evidence_ids: list[str] = Field(default_factory=list)
    suggested_direction: str
    habit_risk_detail: Optional[str] = None
    historical_warning_detail: Optional[str] = None
    # For Why? view
    evidence_memories: list[MemoryUnit] = Field(default_factory=list)


class Blueprint(BaseModel):
    keep: list[str] = Field(default_factory=list)
    improve: list[str] = Field(default_factory=list)
    retire: list[str] = Field(default_factory=list)
    reinvent: list[str] = Field(default_factory=list)
    introduce: list[str] = Field(default_factory=list)
    historical_warnings: list[str] = Field(default_factory=list)
    habit_risks: list[str] = Field(default_factory=list)
    migration_considerations: list[str] = Field(default_factory=list)


class ProposalAnalysisResult(BaseModel):
    proposal_id: str
    changes: list[ChangeAnalysis]
    blueprint: Blueprint
    memoryless_summary: Optional[str] = None  # comparison mode
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class OutcomeInput(BaseModel):
    change_description: str
    product_version: ProductVersion = ProductVersion.V2
    feature_area: Optional[str] = None
    implemented: str
    customer_response: str
    outcome: str
    lesson: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    related_evidence_ids: list[str] = Field(default_factory=list)