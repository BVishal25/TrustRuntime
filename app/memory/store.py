from __future__ import annotations
import re, uuid
from datetime import datetime, timezone
from app.core.types import Evidence, Entity, Claim
from app.db.models import MemoryDocument, EntityRow, ClaimRow
from app.memory.embeddings import HashEmbedding
from app.memory.retrieval import HybridRetriever

class MemoryEngine:
    def __init__(self, repo, embedding=None, graph=None):
        self.repo = repo
        self.embedding = embedding or HashEmbedding()
        self.retriever = HybridRetriever(self.embedding)
        self.graph = graph
        self.index: list[tuple[Evidence, list[float]]] = []

    async def ingest(self, evidence: Evidence):
        doc = MemoryDocument(
            id=evidence.source_id,
            source_type=evidence.source_type,
            text=evidence.text,
            observed_at=evidence.observed_at,
            metadata_json=evidence.metadata
        )
        await self.repo.upsert_document(doc)
        entities = self.extract_entities(evidence)
        for e in entities:
            await self.repo.upsert_entity(EntityRow(
                id=e.entity_id,
                name=e.name,
                entity_type=e.entity_type,
                metadata_json=e.metadata
            ))
        claims = self.extract_claims(evidence, entities)
        for c in claims:
            await self._upsert_claim(c)
        # Update in-memory index
        vec = self.embedding.embed(evidence.text)
        # Replace if existing or append
        self.index = [item for item in self.index if item[0].source_id != evidence.source_id]
        self.index.append((evidence, vec))
        if self.graph:
            await self.graph.upsert(evidence, entities, claims)
        return {
            "document": evidence.source_id,
            "entities": [e.model_dump() for e in entities],
            "claims": [c.model_dump() for c in claims]
        }

    def extract_entities(self, e: Evidence) -> list[Entity]:
        found = []
        for token in re.findall(r"(?:[A-Z][A-Za-z0-9_-]{2,}|ERR[-_]?\d+|INC[-_]?\d+|CUST[-_]?\d+)", e.text):
            typ = "Identifier" if re.match(r"(?:ERR|INC|CUST)[-_]?\d+", token) else "Entity"
            found.append(Entity(entity_id="ent_" + token.lower().replace("-", "_"), name=token, entity_type=typ))
        return list({x.entity_id: x for x in found}.values())

    def extract_claims(self, e: Evidence, entities: list[Entity]) -> list[Claim]:
        claims = []
        low = e.text.lower()
        valid_time = e.valid_from or e.observed_at
        if "offline" in low or "online" in low or "operational" in low or "degraded" in low:
            state = "offline" if "offline" in low else "degraded" if "degraded" in low else "online"
            subject = entities[0].entity_id if entities else "unknown"
            claims.append(Claim(
                claim_id="clm_" + uuid.uuid4().hex[:12],
                subject_id=subject,
                predicate="status",
                object_value=state,
                confidence=0.75,
                valid_from=valid_time,
                evidence_ids=[e.source_id]
            ))
        if "caused by" in low:
            parts = low.split("caused by", 1)
            subject = entities[0].entity_id if entities else "unknown"
            claims.append(Claim(
                claim_id="clm_" + uuid.uuid4().hex[:12],
                subject_id=subject,
                predicate="caused_by",
                object_value=parts[1].strip()[:200],
                confidence=0.65,
                valid_from=valid_time,
                evidence_ids=[e.source_id]
            ))
        return claims

    async def _upsert_claim(self, c: Claim):
        existing = await self.repo.claims()
        conflicts = [
            x for x in existing
            if x.subject_id == c.subject_id
            and x.predicate == c.predicate
            and x.object_value != c.object_value
            and x.status == "active"
        ]
        for old in conflicts:
            old.status = "contested"
            old.valid_until = c.valid_from
            await self.repo.upsert_claim(old)
        await self.repo.upsert_claim(ClaimRow(
            id=c.claim_id,
            subject_id=c.subject_id,
            predicate=c.predicate,
            object_value=c.object_value,
            confidence=c.confidence,
            status=c.status,
            valid_from=c.valid_from,
            valid_until=c.valid_until,
            evidence_ids=c.evidence_ids
        ))

    async def sync_index(self):
        docs = await self.repo.documents()
        existing_ids = {e.source_id for e, _ in self.index}
        for d in docs:
            if d.id not in existing_ids:
                ev = Evidence(
                    source_id=d.id,
                    source_type=d.source_type,
                    text=d.text,
                    observed_at=d.observed_at,
                    metadata=d.metadata_json or {}
                )
                self.index.append((ev, self.embedding.embed(d.text)))

    async def search(self, query: str, k: int = 5) -> list[Evidence]:
        await self.sync_index()
        if not self.index:
            return []
        hits = self.retriever.rank(query, self.index, k=k)
        doc_map = {e.source_id: e for e, _ in self.index}
        return [doc_map[h.source_id] for h in hits if h.source_id in doc_map]

    async def get_claims(self, subject_id: str | None = None) -> list[Claim]:
        rows = await self.repo.claims()
        if subject_id:
            rows = [r for r in rows if r.subject_id == subject_id]
        return [
            Claim(
                claim_id=r.id,
                subject_id=r.subject_id,
                predicate=r.predicate,
                object_value=r.object_value,
                confidence=r.confidence,
                status=r.status, # type: ignore
                valid_from=r.valid_from,
                valid_until=r.valid_until,
                evidence_ids=r.evidence_ids or []
            )
            for r in rows
        ]

    async def snapshot(self) -> dict:
        docs = await self.repo.documents()
        ents = await self.repo.entities()
        clms = await self.repo.claims()
        return {
            "documents": len(docs),
            "entities": len(ents),
            "claims": len(clms),
            "active_claims": sum(1 for c in clms if c.status == "active"),
            "contested_claims": sum(1 for c in clms if c.status == "contested")
        }
