from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import MemoryDocument, EntityRow, ClaimRow, RunRow, AuditEventRow

class Repository:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def add_document(self, row: MemoryDocument):
        return await self.upsert_document(row)

    async def upsert_document(self, row: MemoryDocument):
        existing = await self.s.get(MemoryDocument, row.id)
        if existing:
            existing.source_type = row.source_type
            existing.text = row.text
            existing.observed_at = row.observed_at
            existing.metadata_json = row.metadata_json
            await self.s.flush()
            return existing
        self.s.add(row)
        await self.s.flush()
        return row

    async def add_entity(self, row: EntityRow):
        return await self.upsert_entity(row)

    async def upsert_entity(self, row: EntityRow):
        existing = await self.s.get(EntityRow, row.id)
        if existing:
            existing.name = row.name
            existing.entity_type = row.entity_type
            if row.metadata_json:
                merged = dict(existing.metadata_json or {})
                merged.update(row.metadata_json)
                existing.metadata_json = merged
            await self.s.flush()
            return existing
        self.s.add(row)
        await self.s.flush()
        return row

    async def add_claim(self, row: ClaimRow):
        return await self.upsert_claim(row)

    async def upsert_claim(self, row: ClaimRow):
        existing = await self.s.get(ClaimRow, row.id)
        if existing:
            existing.subject_id = row.subject_id
            existing.predicate = row.predicate
            existing.object_value = row.object_value
            existing.confidence = row.confidence
            existing.status = row.status
            existing.valid_from = row.valid_from
            existing.valid_until = row.valid_until
            existing.evidence_ids = row.evidence_ids
            await self.s.flush()
            return existing
        self.s.add(row)
        await self.s.flush()
        return row

    async def get_document(self, doc_id: str):
        return await self.s.get(MemoryDocument, doc_id)

    async def get_entity(self, entity_id: str):
        return await self.s.get(EntityRow, entity_id)

    async def get_claim(self, claim_id: str):
        return await self.s.get(ClaimRow, claim_id)

    async def documents(self):
        return list((await self.s.execute(select(MemoryDocument))).scalars())

    async def entities(self):
        return list((await self.s.execute(select(EntityRow))).scalars())

    async def claims(self):
        return list((await self.s.execute(select(ClaimRow))).scalars())

    async def save_run(self, row: RunRow):
        existing = await self.s.get(RunRow, row.id)
        if existing:
            existing.status = row.status
            existing.answer = row.answer
            existing.metrics = row.metrics
            await self.s.flush()
            return existing
        self.s.add(row)
        await self.s.flush()
        return row

    async def runs(self, limit: int = 50):
        stmt = select(RunRow).order_by(RunRow.created_at.desc()).limit(limit)
        return list((await self.s.execute(stmt)).scalars())

    async def audit(self, row: AuditEventRow):
        self.s.add(row)
        await self.s.flush()
        return row

    async def audit_events(self, limit: int = 100):
        stmt = select(AuditEventRow).order_by(AuditEventRow.id.desc()).limit(limit)
        return list((await self.s.execute(stmt)).scalars())
