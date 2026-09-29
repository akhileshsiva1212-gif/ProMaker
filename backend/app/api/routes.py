"""ProMaker API routes."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent.blueprint_generator import generate_blueprint
from app.agent.decision_reasoner import analyze_change, memoryless_opinion
from app.agent.proposal_parser import parse_proposal
from app.learning.outcome_processor import process_outcome
from app.memory.hindsight_client import get_memory_client
from app.memory.schema import (
    ChangeAnalysis,
    OutcomeInput,
    ProposalAnalysisResult,
    RetainRequest,
)
from app.memory.seed import seed_if_empty

router = APIRouter()


class ProposalRequest(BaseModel):
    proposal: str = Field(..., min_length=3)
    include_memoryless: bool = True


class AnalyzeResponse(BaseModel):
    result: ProposalAnalysisResult


@router.get("/health")
async def health():
    client = get_memory_client()
    return {
        "status": "ok",
        "memory_count": client.count(),
        "using_real_hindsight": client.using_real,
    }


@router.post("/memory/seed")
async def seed_memory():
    client = get_memory_client()
    n = await seed_if_empty(client)
    return {"seeded": n, "total": client.count()}


@router.post("/memory/retain")
async def retain_memory(req: RetainRequest):
    client = get_memory_client()
    unit = await client.retain(req)
    return unit


@router.post("/memory/recall")
async def recall_memory(query: str, feature_area: Optional[str] = None, top_k: int = 8):
    client = get_memory_client()
    result = await client.recall(query=query, feature_area=feature_area, top_k=top_k)
    return result


@router.get("/memory/timeline")
async def memory_timeline():
    client = get_memory_client()
    return {"memories": client.list_timeline()}


@router.get("/memory/{memory_id}")
async def get_memory(memory_id: str):
    client = get_memory_client()
    m = client.get(memory_id)
    if not m:
        raise HTTPException(404, "Memory not found")
    return m


@router.post("/proposal/parse")
async def parse_proposal_endpoint(body: ProposalRequest):
    changes = await parse_proposal(body.proposal)
    return {"changes": changes}


@router.post("/proposal/analyze", response_model=AnalyzeResponse)
async def analyze_proposal(body: ProposalRequest):
    if not body.proposal.strip():
        raise HTTPException(400, "Empty proposal")

    client = get_memory_client()
    if client.count() == 0:
        await seed_if_empty(client)

    parsed = await parse_proposal(body.proposal)
    if not parsed:
        raise HTTPException(400, "Could not extract any changes from the proposal")

    analyses: list[ChangeAnalysis] = []
    for item in parsed:
        analysis = await analyze_change(
            change_text=item["text"],
            change_id=item["change_id"],
            feature_area=item.get("feature_area"),
        )
        analyses.append(analysis)

    blueprint = generate_blueprint(analyses)

    memoryless = None
    if body.include_memoryless and analyses:
        # One representative memoryless opinion for the whole proposal
        memoryless = await memoryless_opinion(body.proposal[:500])

    result = ProposalAnalysisResult(
        proposal_id=f"P-{uuid.uuid4().hex[:8].upper()}",
        changes=analyses,
        blueprint=blueprint,
        memoryless_summary=memoryless,
    )
    return AnalyzeResponse(result=result)


@router.post("/learning/outcome")
async def learn_from_outcome(payload: OutcomeInput):
    unit = await process_outcome(payload)
    return {"retained": unit}


@router.post("/blueprint/generate")
async def blueprint_from_analyses(analyses: list[ChangeAnalysis]):
    return generate_blueprint(analyses)