from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Evidence(BaseModel):
    source_id: str
    source_type: str = "document"
    text: str
    observed_at: datetime = Field(default_factory=utcnow)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    confidence: float = Field(0.8, ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

class Entity(BaseModel):
    entity_id: str
    name: str
    entity_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class Claim(BaseModel):
    claim_id: str
    subject_id: str
    predicate: str
    object_value: str
    confidence: float = Field(0.5, ge=0, le=1)
    status: Literal["active", "contested", "superseded", "rejected"] = "active"
    valid_from: datetime = Field(default_factory=utcnow)
    valid_until: datetime | None = None
    evidence_ids: list[str] = Field(default_factory=list)

class ToolRequest(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""

class SecurityDecision(BaseModel):
    decision: Literal["allow", "deny", "approval_required"]
    risk: Literal["low", "medium", "high", "critical"]
    reasons: list[str] = Field(default_factory=list)
    policy_id: str = "default-deny"

class VerificationResult(BaseModel):
    passed: bool
    score: float = Field(0, ge=0, le=1)
    checks: list[dict[str, Any]] = Field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0

class AgentTask(BaseModel):
    task_id: str
    prompt: str
    user_id: str = "demo-user"
    strategy: str = "best_of_n"
    candidate_count: int = Field(3, ge=1, le=20)
    max_attempts: int = Field(5, ge=1, le=20)
    require_verification: bool = True
    allow_tools: bool = True
    role: str = "support"
    approved: bool = False
    tool_request: ToolRequest | None = None

class AgentRunResult(BaseModel):
    task_id: str
    status: str
    answer: str
    confidence: float
    attempts: int
    verification: VerificationResult | None = None
    security_events: list[SecurityDecision] = Field(default_factory=list)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
