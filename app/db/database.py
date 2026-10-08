from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings

settings=get_settings()
engine=create_async_engine(settings.database_url, future=True)
SessionLocal=async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase): pass

async def init_db():
    from app.db import models
    if "sqlite" in settings.database_url and "///" in settings.database_url:
        try:
            db_path_str = settings.database_url.split("///")[-1]
            Path(db_path_str).parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session():
    async with SessionLocal() as session:
        yield session
