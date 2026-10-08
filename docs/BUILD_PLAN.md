# TrustRuntime Complete Build Plan

This is the implementation sequence for the reference architecture. Do not treat the order as optional: later subsystems depend on earlier trust boundaries.

## Phase 0 — Environment

1. Python 3.11–3.14, uv, Git, Docker.
2. Create `.venv`; install `.[all]`.
3. Copy `.env.example` to `.env`.
4. Run tests.
5. Seed demo data.

**Done when:** API, dashboard, tests and seed script work locally.

## Phase 1 — Data and epistemic memory

1. Normalize documents/events.
2. Extract entities/relations/claims.
3. Persist provenance.
4. Add temporal validity.
5. Detect contradictory active claims.
6. Add vector retrieval.
7. Enable Neo4j adapter.
8. Add graph traversal queries.
9. Add entity resolution.
10. Add evidence ranking.

**Done when:** every answer can return supporting evidence and the latest valid state without deleting historical facts.

## Phase 2 — Reasoning and TTC

1. Establish single-shot baseline.
2. Implement Best-of-N.
3. Add self-refinement from verifier feedback.
4. Add beam search.
5. Add MCTS.
6. Add compute budget.
7. Record attempts and scores.
8. Compare accuracy/cost/latency.

**Done when:** benchmark results demonstrate when additional inference compute helps.

## Phase 3 — Execution and verification

1. Static validation.
2. Docker executor.
3. No-network execution.
4. CPU/memory/pid/time limits.
5. stdout/stderr capture.
6. Code test harness.
7. SQL read-only verifier.
8. Evidence consistency verifier.

**Done when:** execution outcome, not LLM confidence, controls the verified status.

## Phase 4 — Security

1. Tool registry.
2. Capability-based permissions.
3. Default deny.
4. Risk classification.
5. Human approval boundary for critical actions.
6. Prompt-injection detection.
7. Memory-poisoning detection.
8. Audit trail.
9. Red-team attack generation.
10. Regression suite for discovered attacks.

**Done when:** every tool call is authorized independently of the model's text.

## Phase 5 — Adaptive routing

1. Local model adapter.
2. Cloud/openai-compatible adapter.
3. Difficulty estimator.
4. Failure-aware escalation.
5. Cost budget.
6. Latency budget.
7. Model selection benchmark.

**Done when:** routing improves cost/latency without unacceptable loss in verified success.

## Phase 6 — Observability

Trace task → retrieval → candidate → security → tool → execution → verification → memory update.

Collect p50/p95 latency, token estimates, model, strategy, tool calls, security decisions, verification outcomes, memory updates, and cost estimates.

## Phase 7 — Evaluation

Maintain fixed datasets for memory, reasoning, security and end-to-end tasks. Never tune and evaluate on the same cases. Version datasets and record configuration with every run.

## Phase 8 — Portfolio hardening

1. Architecture diagrams.
2. Threat model.
3. Failure analysis.
4. Benchmark report.
5. Demo dataset.
6. Reproducible setup.
7. CI.
8. Screenshots/video.
9. Resume bullets based only on measured results.
