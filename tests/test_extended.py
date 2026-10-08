import pytest
from starlette.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db.database import Base
from app.db.repository import Repository
from app.memory.store import MemoryEngine
from app.core.types import Evidence, AgentTask, ToolRequest
from app.reasoning.providers import DeterministicProvider
from app.reasoning.search import SearchEngine
from app.reasoning.mcts import MCTS
from app.security.injection import detect_injection, classify_content
from app.security.policy import PolicyEngine
from app.security.redteam import RedTeamHarness
from app.execution.sql import validate_read_only_sql
from app.tools.registry import build_default_registry
from app.observability.audit import AuditLogger
from app.core.runtime import TrustRuntime
from app.models.router import ModelRouter
from app.verification.verifier import Verifier
from app.main import app

@pytest.mark.asyncio
async def test_memory_engine_duplicate_entities_and_contradiction():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    session = Session()
    repo = Repository(session)
    memory = MemoryEngine(repo)

    # Ingest document 1
    ev1 = Evidence(source_id="INC-100", source_type="incident", text="PaymentService was operational on 2026-08-10.")
    await memory.ingest(ev1)

    # Ingest document 2 referencing the same entity and contradicting status
    ev2 = Evidence(source_id="INC-101", source_type="incident", text="PaymentService became degraded on 2026-08-18.")
    await memory.ingest(ev2)

    # Ingest third document referencing entity
    ev3 = Evidence(source_id="TCK-201", source_type="ticket", text="CUST-101 reports payment failure caused by PaymentService.")
    await memory.ingest(ev3)

    # Commit must not fail with IntegrityError
    await session.commit()

    docs = await repo.documents()
    assert len(docs) == 3

    entities = await repo.entities()
    assert any(e.id == "ent_paymentservice" for e in entities)

    claims = await memory.get_claims("ent_paymentservice")
    assert len(claims) >= 2

    # Verify conflict marking: one status claim should be contested and one active
    status_claims = [c for c in claims if c.predicate == "status"]
    assert len(status_claims) == 2
    active = [c for c in status_claims if c.status == "active"]
    contested = [c for c in status_claims if c.status == "contested"]
    assert len(active) == 1
    assert len(contested) == 1
    assert active[0].object_value == "degraded"
    assert contested[0].object_value == "online"

    # Snapshot check
    snap = await memory.snapshot()
    assert snap["documents"] == 3
    assert snap["active_claims"] >= 1
    assert snap["contested_claims"] >= 1

    await session.close()
    await engine.dispose()

@pytest.mark.asyncio
async def test_hybrid_retriever_ranking():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    session = Session()
    repo = Repository(session)
    memory = MemoryEngine(repo)

    await memory.ingest(Evidence(source_id="E1", text="Database latency increased after migration."))
    await memory.ingest(Evidence(source_id="E2", text="PaymentService checkout error ERR-401 reported by customer."))
    await memory.ingest(Evidence(source_id="E3", text="Network firewall rules were refreshed successfully."))
    await session.commit()

    results = await memory.search("ERR-401 PaymentService checkout", k=2)
    assert len(results) >= 1
    assert results[0].source_id == "E2"

    await session.close()
    await engine.dispose()

@pytest.mark.asyncio
async def test_mcts_candidate_scoring_and_sorting():
    provider = DeterministicProvider()
    verifier = Verifier()
    mcts = MCTS(provider, verifier)
    candidates = await mcts.search("Diagnose failure with evidence", "Evidence: Service is offline.", rollouts=4)

    assert len(candidates) > 0
    # First candidate should have the highest score
    assert candidates[0].candidate.verification is not None
    assert candidates[0].candidate.score >= 0.5
    for i in range(len(candidates) - 1):
        assert candidates[i].candidate.score >= candidates[i+1].candidate.score

@pytest.mark.asyncio
async def test_beam_search_execution():
    provider = DeterministicProvider()
    verifier = Verifier()
    search = SearchEngine(provider, verifier)
    beams = await search.beam_search("Diagnose incident", "Evidence: DB is down.", beam=2, depth=2)
    assert len(beams) == 2
    assert all(b.score > 0 for b in beams)

def test_sql_validator():
    assert validate_read_only_sql("SELECT * FROM payments WHERE id = 1")[0] is True
    assert validate_read_only_sql("WITH q AS (SELECT 1) SELECT * FROM q")[0] is True
    assert validate_read_only_sql("DROP TABLE customers")[0] is False
    assert validate_read_only_sql("INSERT INTO payments VALUES (1, 2)")[0] is False
    assert validate_read_only_sql("DELETE FROM users")[0] is False

@pytest.mark.asyncio
async def test_tool_registry_sql_validation_and_execution():
    registry = build_default_registry()
    allowed = await registry.execute(ToolRequest(tool_name="query_readonly_database", arguments={"sql": "SELECT 1"}))
    assert allowed["status"] == "executed"
    assert allowed["read_only"] is True

    blocked = await registry.execute(ToolRequest(tool_name="query_readonly_database", arguments={"sql": "DROP TABLE payments"}))
    assert blocked["status"] == "blocked"
    assert blocked["read_only"] is False

def test_red_team_all_attacks_blocked():
    harness = RedTeamHarness()
    results = harness.run()
    assert len(results) == 5
    for r in results:
        assert r.blocked is True, f"Attack {r.attack_id} ({r.category}) should have been blocked!"

def test_policy_engine_role_and_approval():
    policy = PolicyEngine()
    # Support cannot delete customer
    dec1 = policy.evaluate(ToolRequest(tool_name="delete_customer", arguments={"customer_id": "1"}), role="support")
    assert dec1.decision == "deny"

    # Admin without approval requires approval
    dec2 = policy.evaluate(ToolRequest(tool_name="delete_customer", arguments={"customer_id": "1"}), role="admin", approved=False)
    assert dec2.decision == "approval_required"

    # Admin with explicit approval allowed
    dec3 = policy.evaluate(ToolRequest(tool_name="delete_customer", arguments={"customer_id": "1"}), role="admin", approved=True)
    assert dec3.decision == "allow"

@pytest.mark.asyncio
async def test_runtime_end_to_end_with_tool_and_audit():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    session = Session()
    repo = Repository(session)
    memory = MemoryEngine(repo)
    audit = AuditLogger(repo)
    tools = build_default_registry()
    router = ModelRouter()

    await memory.ingest(Evidence(source_id="TCK-99", text="Server latency reported by customer."))
    await session.commit()

    rt = TrustRuntime(memory, repo, router, tools, audit)

    # Run with allowed tool
    task = AgentTask(
        task_id="T-100",
        prompt="Explain server latency with evidence.",
        strategy="best_of_n",
        candidate_count=2,
        role="support",
        tool_request=ToolRequest(tool_name="read_ticket", arguments={"ticket_id": "TCK-99"})
    )
    result = await rt.run(task)
    await session.commit()

    assert result.status == "verified"
    assert len(result.tool_results) == 1
    assert result.tool_results[0]["result"]["ticket_id"] == "TCK-99"

    # Verify run and audit records were persisted
    runs = await repo.runs()
    assert len(runs) >= 1
    assert runs[0].task_id == "T-100"

    audit_logs = await repo.audit_events()
    assert len(audit_logs) >= 2
    types = [a.event_type for a in audit_logs]
    assert "memory_retrieval" in types
    assert "tool_execution" in types
    assert "run_completed" in types

    await session.close()
    await engine.dispose()

def test_api_endpoints_via_test_client():
    with TestClient(app) as client:
        # Health
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

        # Memory Snapshot
        r = client.get("/api/memory/snapshot")
        assert r.status_code == 200
        assert "documents" in r.json()

        # Tools List
        r = client.get("/api/tools")
        assert r.status_code == 200
        assert "read_ticket" in r.json()["tools"]

        # Red Team
        r = client.get("/api/security/redteam")
        assert r.status_code == 200
        attacks = r.json()
        assert len(attacks) == 5
        assert all(a["blocked"] is True for a in attacks)

        # Execute Tool via API (allowed)
        r = client.post("/api/tools/execute", json={"tool_name": "read_ticket", "arguments": {"ticket_id": "TCK-1"}, "role": "support"})
        assert r.status_code == 200
        assert r.json()["status"] == "success"

        # Execute Tool via API (blocked unauthorized)
        r = client.post("/api/tools/execute", json={"tool_name": "delete_customer", "arguments": {"customer_id": "C-1"}, "role": "support"})
        assert r.status_code == 200
        assert r.json()["status"] == "blocked"

        # Run Benchmark
        r = client.post("/api/benchmark/run")
        assert r.status_code == 200
        res = r.json()
        assert res["summary"]["total"] == 3
        assert res["summary"]["verified"] == 3
