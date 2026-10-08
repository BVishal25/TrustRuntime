# Evaluation

## Principles

Do not evaluate an AI system only with another LLM. Prefer deterministic checks wherever the task allows.

## Memory metrics

- entity precision/recall
- relation precision/recall
- entity resolution accuracy
- temporal consistency
- contradiction detection rate
- retrieval precision@k
- retrieval recall@k

## Reasoning metrics

- verified success rate
- attempts per task
- token estimate
- latency
- cost estimate
- success per compute budget

## Security metrics

- attack success rate
- blocked attack rate
- false positives
- false negatives
- critical findings
- mean time to regression fix

## System metrics

- p50/p95 latency
- tool calls/run
- sandbox duration
- graph traversal duration
- retrieval duration
- memory writes/run

## Required comparisons

1. Single-shot vs Best-of-N.
2. Best-of-N vs self-refinement.
3. Beam vs MCTS.
4. Vector-only vs hybrid retrieval.
5. No routing vs adaptive routing.
6. No security gate vs policy gate.

Never invent results. Store raw benchmark output under `artifacts/` and summarize it in `docs/experiments/`.
