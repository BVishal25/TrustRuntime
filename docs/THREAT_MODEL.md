# Threat Model

## Assets

- mock customer records
- credentials/secrets in test fixtures
- tool permissions
- memory integrity
- execution environment
- audit logs

## Threats

### Prompt injection
Malicious text attempts to override agent instructions.

### Indirect prompt injection
Instructions embedded in retrieved tickets/logs/documents.

### Memory poisoning
Attacker inserts false claims that later influence retrieval.

### Tool abuse
Model invokes a tool outside its intended capability.

### Privilege escalation
Low-privilege identity attempts a high-risk action.

### Data exfiltration
Agent attempts to move protected information to an external destination.

### Resource exhaustion
Infinite/repeated reasoning or tool calls consume compute.

## Controls

- Treat retrieval as data, not authority.
- Default-deny tool policy.
- Capability and role checks.
- Explicit approval for critical actions.
- No-network sandbox.
- Resource limits.
- Audit every decision.
- Fixed red-team regression cases.
- Separate evaluator and target environments.
