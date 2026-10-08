# Architecture

## Trust boundaries

1. **Input boundary:** all external content is untrusted data.
2. **Memory boundary:** LLMs may propose memory changes; the memory controller validates and commits them.
3. **Reasoning boundary:** model output is a proposal, never proof.
4. **Security boundary:** tool authorization is deterministic and independent of the LLM.
5. **Execution boundary:** untrusted code runs only inside the hardened container executor.
6. **Verification boundary:** verified status requires deterministic or evidence-backed checks.

## Core flow

`request → intent → retrieval → candidates → verification/security → action → evidence → memory`

## Storage

- PostgreSQL/SQLite: operational metadata, claims, documents, audit events and runs.
- Neo4j: relationship graph and temporal traversals.
- Vector backend: semantic retrieval.

The default repository uses SQLite + deterministic hashing so it can run offline. Optional adapters upgrade each component.

## Why not let the LLM mutate state directly?

Because generated text is not authority. State changes are typed commands that pass schema, provenance, policy and transaction checks.
