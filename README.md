# TrustRuntime

**TrustRuntime** is a model-agnostic AI agent runtime built around one loop:

> **Remember → Reason → Verify → Authorize → Act → Learn**

It combines temporal/provenance-aware memory, hybrid retrieval, test-time search, deterministic verification, capability-based tool security, adversarial evaluation, adaptive model routing, and observability.

## What this repository contains

- FastAPI API + interactive dashboard
- SQLite/PostgreSQL-ready persistence
- Temporal claims/evidence/entity memory
- Optional Neo4j graph adapter
- Hybrid lexical/vector retrieval with optional SentenceTransformers embeddings
- Best-of-N, self-refinement, beam search, and MCTS-style search
- Compute budgets and model routing
- Docker-backed code execution with resource limits
- Deterministic verification
- Capability-based tool registry and default-deny policy engine
- Prompt-injection and memory-poisoning heuristics
- Automated red-team harness
- Audit/event telemetry and optional OpenTelemetry
- Seed dataset and reproducible benchmark runner
- Tests, threat model, architecture docs, operations docs

## Quick start

```powershell
uv venv
.venv\Scripts\Activate.ps1
uv pip install -e ".[all]"
Copy-Item .env.example .env
uv run python scripts/seed_demo.py
uv run uvicorn app.main:app --reload
```

If PowerShell blocks activation, use: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.

Open `http://127.0.0.1:8000/` for the dashboard and `/docs` for OpenAPI.

## Local-first mode

The default runtime works without a paid API. If Ollama is installed, set `OLLAMA_MODEL` to a local model. Without a model server, the deterministic demo provider still exercises the complete orchestration path.

## Production note

This repository is a complete reference implementation and learning/portfolio platform, not a claim of production security certification. Untrusted code must only run inside the hardened container executor. The Python subprocess fallback is intentionally disabled by default for arbitrary code.

## Architecture

```text
                 ┌────────────── USER/API ──────────────┐
                 │                                       │
                 ▼                                       │
          Intent / Risk Router                           │
                 │                                       │
                 ▼                                       │
        ┌──── EPISTEMIC MEMORY ────┐                    │
        │ claims • evidence • time │                    │
        │ graph • vector • lineage │                    │
        └────────────┬─────────────┘                    │
                     ▼                                  │
             Retrieved evidence                          │
                     ▼                                  │
          TEST-TIME REASONING                            │
       best-of-n / beam / MCTS                          │
                     ▼                                  │
             Security Gate                               │
                     ▼                                  │
             Tool / Sandbox                              │
                     ▼                                  │
               Verifier                                  │
                     ▼                                  │
             Memory Update ─────────────────────────────┘
```

## Build order

Read `docs/BUILD_PLAN.md`. The codebase is intentionally modular: you can replace the default local adapters with Neo4j, pgvector, Ollama, OpenAI-compatible providers, or your own infrastructure without rewriting the runtime.
