from dataclasses import dataclass
from app.memory.embeddings import cosine

@dataclass
class RetrievalHit:
    source_id: str
    score: float
    reason: str

class HybridRetriever:
    def __init__(self, embedding): self.embedding=embedding
    def rank(self, query, records, k=5):
        q=self.embedding.embed(query); hits=[]
        for record,vector in records:
            semantic=cosine(q,vector)
            lexical=len(set(query.lower().split()) & set(record.text.lower().split())) / max(len(set(query.lower().split())),1)
            score=.7*semantic+.3*lexical
            hits.append(RetrievalHit(record.source_id,score,'semantic+lexical'))
        return sorted(hits,key=lambda x:x.score,reverse=True)[:k]
