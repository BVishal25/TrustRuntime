# Data Model

## Evidence
`source_id`, `source_type`, `text`, `observed_at`, `valid_from`, `valid_until`, `confidence`, metadata.

## Claim
`subject`, `predicate`, `object`, status, validity interval, confidence, evidence IDs.

## Run
Task, strategy, attempts, model, latency, token estimate, verification, security events.

## Audit event
Run ID, event type, allowed flag, payload, timestamp.

A claim is never deleted merely because it becomes outdated. It becomes superseded/contested with provenance.
