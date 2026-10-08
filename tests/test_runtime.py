import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db.database import Base
from app.db.repository import Repository
from app.memory.store import MemoryEngine
from app.reasoning.providers import DeterministicProvider
from app.models.router import ModelRouter
from app.tools.registry import build_default_registry
from app.observability.audit import AuditLogger
from app.core.runtime import TrustRuntime
from app.core.types import Evidence, AgentTask

@pytest.fixture
async def runtime():
    engine=create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as c: await c.run_sync(Base.metadata.create_all)
    S=async_sessionmaker(engine,expire_on_commit=False); s=S(); repo=Repository(s)
    memory=MemoryEngine(repo); await memory.ingest(Evidence(source_id='INC-1',source_type='incident',text='PaymentService is degraded.'))
    rt=TrustRuntime(memory,repo,ModelRouter(),build_default_registry(),AuditLogger(repo))
    # Force deterministic provider for test isolation.
    from app.reasoning.search import SearchEngine
    original=rt.router.choose; rt.router.choose=lambda difficulty: DeterministicProvider()
    yield rt
    await s.close(); await engine.dispose()

@pytest.mark.asyncio
async def test_runtime_returns_verifiedish_result(runtime):
    out=await runtime.run(AgentTask(task_id='T1',prompt='Explain the payment incident.',candidate_count=2))
    assert out.attempts==2
    assert out.evidence
    assert out.verification is not None
