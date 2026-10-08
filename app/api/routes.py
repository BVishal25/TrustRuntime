from __future__ import annotations
import uuid, json, time
from pathlib import Path
from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.api.deps import build_runtime
from app.core.types import AgentTask, Evidence, ToolRequest
from app.security.redteam import RedTeamHarness

router = APIRouter(prefix="/api")

class QueryRequest(BaseModel):
    prompt: str
    strategy: str = "best_of_n"
    candidate_count: int = Field(3, ge=1, le=20)
    role: str = "support"
    approved: bool = False
    tool_name: str | None = None
    tool_arguments: dict[str, Any] = Field(default_factory=dict)

class ToolExecutionRequest(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    role: str = "support"
    approved: bool = False

@router.get("/health")
async def health():
    return {"status": "ok", "service": "trustruntime", "version": "1.0.0"}

@router.post("/memory/ingest")
async def ingest(e: Evidence):
    session, r = await build_runtime()
    try:
        out = await r.memory.ingest(e)
        await session.commit()
        return out
    finally:
        await session.close()

@router.get("/memory/search")
async def search(q: str, k: int = 5):
    session, r = await build_runtime()
    try:
        return [e.model_dump(mode="json") for e in await r.memory.search(q, k)]
    finally:
        await session.close()

@router.get("/memory/snapshot")
async def snapshot():
    session, r = await build_runtime()
    try:
        return await r.memory.snapshot()
    finally:
        await session.close()

@router.get("/memory/claims")
async def list_claims(subject_id: str | None = None):
    session, r = await build_runtime()
    try:
        claims = await r.memory.get_claims(subject_id)
        return [c.model_dump(mode="json") for c in claims]
    finally:
        await session.close()

@router.post("/run")
async def run(q: QueryRequest):
    session, r = await build_runtime()
    try:
        tool_req = None
        if q.tool_name:
            tool_req = ToolRequest(tool_name=q.tool_name, arguments=q.tool_arguments)
        task = AgentTask(
            task_id=f"task_{uuid.uuid4().hex[:8]}",
            prompt=q.prompt,
            strategy=q.strategy,
            candidate_count=q.candidate_count,
            role=q.role,
            approved=q.approved,
            tool_request=tool_req
        )
        result = await r.run(task)
        await session.commit()
        return result.model_dump(mode="json")
    finally:
        await session.close()

@router.get("/runs")
async def list_runs(limit: int = 20):
    session, r = await build_runtime()
    try:
        rows = await r.repo.runs(limit)
        return [
            {
                "id": row.id,
                "task_id": row.task_id,
                "status": row.status,
                "answer": row.answer,
                "metrics": row.metrics,
                "created_at": row.created_at.isoformat() if row.created_at else None
            }
            for row in rows
        ]
    finally:
        await session.close()

@router.get("/audit")
async def list_audit(limit: int = 50):
    session, r = await build_runtime()
    try:
        rows = await r.repo.audit_events(limit)
        return [
            {
                "id": row.id,
                "run_id": row.run_id,
                "event_type": row.event_type,
                "allowed": row.allowed,
                "payload": row.payload,
                "created_at": row.created_at.isoformat() if row.created_at else None
            }
            for row in rows
        ]
    finally:
        await session.close()

@router.get("/tools")
async def list_tools():
    session, r = await build_runtime()
    try:
        tool_names = r.tools.names()
        policies = {
            t: r.policy.policies.get(t, {"risk": "unknown", "roles": [], "approval_required": True})
            for t in tool_names
        }
        # Format set to list for JSON serialization
        for t, p in policies.items():
            if isinstance(p.get("roles"), (set, tuple)):
                p["roles"] = sorted(list(p["roles"]))
        return {"tools": tool_names, "policies": policies}
    finally:
        await session.close()

@router.post("/tools/execute")
async def execute_tool(req: ToolExecutionRequest):
    session, r = await build_runtime()
    try:
        tool_req = ToolRequest(tool_name=req.tool_name, arguments=req.arguments)
        decision = r.policy.evaluate(tool_req, role=req.role, approved=req.approved)
        if decision.decision != "allow":
            await r.audit.log("manual_tool", "tool_blocked", {"tool": req.tool_name, "decision": decision.decision}, allowed=False)
            await session.commit()
            return {"status": "blocked", "decision": decision.model_dump()}
        res = await r.tools.execute(tool_req)
        await r.audit.log("manual_tool", "tool_executed", {"tool": req.tool_name, "result": res}, allowed=True)
        await session.commit()
        return {"status": "success", "result": res, "decision": decision.model_dump()}
    finally:
        await session.close()

@router.get("/security/redteam")
async def redteam():
    return [x.__dict__ for x in RedTeamHarness().run()]

@router.post("/benchmark/run")
async def run_benchmark():
    session, r = await build_runtime()
    try:
        benchmark_file = Path("data/benchmarks/tasks.json")
        if not benchmark_file.is_file():
            benchmark_file = Path(__file__).resolve().parent.parent.parent / "data" / "benchmarks" / "tasks.json"
        if benchmark_file.is_file():
            cases = json.loads(benchmark_file.read_text(encoding="utf-8"))
        else:
            cases = []
        results = []
        for c in cases:
            st = time.perf_counter()
            task = AgentTask(
                task_id=c["id"],
                prompt=c["prompt"],
                strategy=c.get("strategy", "best_of_n"),
                candidate_count=c.get("n", 3)
            )
            out = await r.run(task)
            results.append({
                "id": c["id"],
                "status": out.status,
                "confidence": out.confidence,
                "latency_ms": (time.perf_counter() - st) * 1000,
                "attempts": out.attempts
            })
        await session.commit()
        from app.evaluation import summarize
        summary = summarize(results)
        return {
            "cases": results,
            "summary": {
                "total": summary.total,
                "verified": summary.verified,
                "success_rate": summary.success_rate,
                "average_confidence": summary.average_confidence,
                "average_latency_ms": summary.average_latency_ms,
                "average_attempts": summary.average_attempts
            }
        }
    finally:
        await session.close()
