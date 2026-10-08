from app.db.database import SessionLocal, init_db
from app.db.repository import Repository
from app.memory.store import MemoryEngine
from app.memory.embeddings import HashEmbedding
from app.models.router import ModelRouter
from app.tools.registry import build_default_registry
from app.observability.audit import AuditLogger
from app.core.runtime import TrustRuntime
from app.core.config import get_settings

async def build_runtime():
    await init_db()
    session=SessionLocal(); repo=Repository(session); settings=get_settings()
    embedding=HashEmbedding()
    if settings.embedding_model:
        try:
            from app.memory.embeddings import SentenceTransformerEmbedding
            embedding=SentenceTransformerEmbedding(settings.embedding_model)
        except Exception:
            pass
    graph=None
    if settings.neo4j_enabled:
        try:
            from app.memory.graph import Neo4jGraph
            graph=Neo4jGraph(settings.neo4j_uri,settings.neo4j_user,settings.neo4j_password)
        except Exception:
            graph=None
    memory=MemoryEngine(repo,embedding=embedding,graph=graph)
    tools=build_default_registry(); audit=AuditLogger(repo)
    runtime=TrustRuntime(memory,repo,ModelRouter(),tools,audit)
    return session,runtime
