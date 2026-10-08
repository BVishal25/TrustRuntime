# Operations

## Local

Use SQLite + deterministic embeddings + deterministic provider. This is the zero-cost path.

## Local model

Run Ollama separately and configure `OLLAMA_BASE_URL` and `OLLAMA_MODEL`. The router will use it for local inference.

## Neo4j

Start `docker compose up -d neo4j`, then enable `NEO4J_ENABLED=true`.

## Full stack

`docker compose up --build` starts the API and Neo4j. For real production deployment, put the executor in a separate hardened worker pool rather than running it inside the API container.

## Security

Never place real credentials or production databases in the demo. Use synthetic data. Critical tools should remain approval-gated.
