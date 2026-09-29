# ProMaker

**Your product team's decision memory. Don't repeat what already failed.**

ProMaker is an AI Product Decision Memory Agent. It remembers what your team tried, what happened, and what you learned — then uses that history to evaluate the next product decision.

---

## Why ProMaker exists

Companies make thousands of product decisions. Over time they forget:

- Why a decision was made
- What problem it was meant to solve
- What experiment ran
- What customers did afterward
- Whether it worked — and why

ProMaker keeps that history structured and recallable. When someone proposes a change for the next version, it does not give generic advice. It grounds the answer in **your** past.

It is **not** a chatbot.  
It is **not** a sentiment dashboard.  
It is **decision memory with a verdict**.

---

## Core idea

Example: customers love **fast checkout**. That does not mean V2 must keep the old checkout UI. ProMaker preserves the **value** (low friction) while allowing a new implementation.

The goal is:

> **New product + lessons from the old product**  
> — not —  
> Old product + cosmetic changes

---

## What it remembers

Five memory types, stored as complete decision stories:

| Type | Meaning |
|------|---------|
| **Feedback** | What customers said or experienced |
| **Habit** | How customers are used to using the product |
| **Experiment** | What the team tried |
| **Outcome** | What happened after the change |
| **Lesson** | What the company learned |

Unit of memory:

Memories are **version-aware** (V1 → V2 → V3). Each generation informs the next.

---

## The five verdicts

Every proposed change gets exactly one:

| Verdict | When |
|---------|------|
| **KEEP** | Proven customer value — protect it |
| **IMPROVE** | Useful, but the current form has problems |
| **RETIRE** | Low value or repeated harm |
| **REINVENT** | Need is real; previous implementation failed |
| **INTRODUCE** | Genuinely new capability with supporting evidence |

Plus:

- **Historical warning** — this looks like something that already failed
- **Habit collision** — this breaks a workflow users rely on
- **Evidence state** — strong / limited / insufficient (never invents history)

Every recommendation is traceable: **Verdict → Reason → Evidence IDs → Openable memories**.

---

## Demo product: FlowSync

Seed data is a coherent B2B SaaS product with real decision arcs:

- **Onboarding** — detailed tutorial shipped → completion did not improve → lesson: complexity, not lack of instructions
- **Checkout** — single-page low-friction flow → high completion → lesson: speed is a core value
- **Search** — Dashboard → Search → Product → Checkout is the dominant habit
- **Recommendations** — customers ask for smarter suggestions; rule-based banner underperformed

These power the three signature scenarios:

1. **Failed decision** — propose another step-by-step tutorial → **REINVENT** + warning
2. **Habit collision** — hide Search in a sidebar → **IMPROVE** + habit risk
3. **Learning** — retain "simplified onboarding succeeded" → future recalls use the updated lesson

---

## Quick start

### Requirements

- **Python 3.11 or 3.12** (3.14 is not recommended on Windows yet)
- **Node.js 18+**
- Optional: `LLM_API_KEY` for richer reasoning (works offline with heuristics + seed memory)

### Backend

```bash
cd backend
python -m venv .venv

# Windows (Git Bash)
source .venv/Scripts/activate

# macOS / Linux
# source .venv/bin/activate

pip install --upgrade pip
pip install fastapi "uvicorn[standard]" pydantic pydantic-settings \
  python-dotenv httpx openai sqlalchemy aiosqlite python-multipart tenacity

export PYTHONPATH=.          # Windows Git Bash / macOS / Linux
# set PYTHONPATH=.           # Windows CMD

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Architecture :


USER
  │
  ▼
V2 PRODUCT PROPOSAL
  │
  ▼
PROPOSAL PARSER  ──►  Change 1 · Change 2 · Change 3
                          │           │           │
                          ▼           ▼           ▼
                    Targeted      Targeted    Targeted
                    Hindsight     Hindsight   Hindsight
                    Recall        Recall      Recall
                          │           │           │
                          └───────────┼───────────┘
                                      ▼
                              EVIDENCE CHECK
                                      │
                                      ▼
                            DETERMINISTIC FACTS
                                      │
                                      ▼
                               LLM REASONING
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
                 Verdict          Warning          Habit Risk
                    │                 │                 │
                    └─────────────────┼─────────────────┘
                                      ▼
                                   EVIDENCE
                                      │
                                      ▼
                            EVOLUTION BLUEPRINT
                                      │
                                      ▼
                                NEW OUTCOME
                                      │
                                      ▼
                             HINDSIGHT RETAIN
                                      │
                                      ▼
                               BETTER MEMORY


Project layout

textpromaker/
├── backend/
│   ├── app/
│   │   ├── agent/          # parser, reasoner, blueprint
│   │   ├── memory/         # schema, local store, Hindsight client, seed
│   │   ├── learning/       # outcome → updated lessons
│   │   ├── api/            # FastAPI routes
│   │   ├── config.py
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx         # Proposal · Memory · Learn
│   │   ├── api.ts
│   │   └── ...
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
