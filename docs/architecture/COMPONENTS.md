# Component Responsibilities

| Component | Responsibility | Trust level |
|---|---|---|
| API | request boundary | untrusted input |
| Memory | evidence/state | validated state |
| Reasoner | candidate generation | untrusted proposal |
| Security | authorization | trusted policy |
| Executor | side effects | isolated capability |
| Verifier | correctness evidence | trusted evaluator |
| Audit | accountability | append-only intent |
| Router | resource allocation | policy constrained |
