"""ProMaker API — Product Decision Memory Agent."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import get_settings
from app.memory.hindsight_client import get_memory_client
from app.memory.seed import seed_if_empty

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("promaker")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure data dir exists
    Path("./data").mkdir(parents=True, exist_ok=True)
    client = get_memory_client()
    n = await seed_if_empty(client)
    if n:
        logger.info("Seeded %s product decision memories", n)
    else:
        logger.info("Memory store ready (%s memories)", client.count())
    yield


app = FastAPI(
    title="ProMaker",
    description="Your product team's decision memory. Don't repeat what already failed.",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "ProMaker",
        "tagline": "Your product team's decision memory. Don't repeat what already failed.",
        "docs": "/docs",
    }