from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, DateTime, JSON, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base

class MemoryDocument(Base):
    __tablename__="memory_documents"
    id: Mapped[str]=mapped_column(String(128), primary_key=True)
    source_type: Mapped[str]=mapped_column(String(64))
    text: Mapped[str]=mapped_column(Text)
    observed_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    metadata_json: Mapped[dict]=mapped_column(JSON, default=dict)

class EntityRow(Base):
    __tablename__="entities"
    id: Mapped[str]=mapped_column(String(128), primary_key=True)
    name: Mapped[str]=mapped_column(String(512), index=True)
    entity_type: Mapped[str]=mapped_column(String(128), index=True)
    metadata_json: Mapped[dict]=mapped_column(JSON, default=dict)

class ClaimRow(Base):
    __tablename__="claims"
    id: Mapped[str]=mapped_column(String(128), primary_key=True)
    subject_id: Mapped[str]=mapped_column(String(128), index=True)
    predicate: Mapped[str]=mapped_column(String(128), index=True)
    object_value: Mapped[str]=mapped_column(String(1024))
    confidence: Mapped[float]=mapped_column(Float, default=.5)
    status: Mapped[str]=mapped_column(String(32), default="active")
    valid_from: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)
    evidence_ids: Mapped[list]=mapped_column(JSON, default=list)

class RunRow(Base):
    __tablename__="runs"
    id: Mapped[str]=mapped_column(String(128), primary_key=True)
    task_id: Mapped[str]=mapped_column(String(128), index=True)
    status: Mapped[str]=mapped_column(String(32))
    answer: Mapped[str]=mapped_column(Text, default="")
    metrics: Mapped[dict]=mapped_column(JSON, default=dict)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class AuditEventRow(Base):
    __tablename__="audit_events"
    id: Mapped[int]=mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str]=mapped_column(String(128), index=True)
    event_type: Mapped[str]=mapped_column(String(128), index=True)
    allowed: Mapped[bool]=mapped_column(Boolean, default=True)
    payload: Mapped[dict]=mapped_column(JSON, default=dict)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
