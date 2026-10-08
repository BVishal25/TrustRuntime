from __future__ import annotations
import math, re

class EmbeddingProvider:
    def embed(self, text: str) -> list[float]: raise NotImplementedError

class HashEmbedding(EmbeddingProvider):
    """Deterministic offline embedding fallback. Not semantic SOTA; useful for local reproducibility."""
    def __init__(self, dims=256): self.dims=dims
    def embed(self,text):
        v=[0.0]*self.dims
        for tok in re.findall(r"[a-zA-Z0-9_]+", text.lower()):
            h=hash(tok)%self.dims; v[h]+=1.0
        n=math.sqrt(sum(x*x for x in v)) or 1
        return [x/n for x in v]

class SentenceTransformerEmbedding(EmbeddingProvider):
    def __init__(self, model_name):
        from sentence_transformers import SentenceTransformer
        self.model=SentenceTransformer(model_name)
    def embed(self,text): return self.model.encode(text, normalize_embeddings=True).tolist()

def cosine(a,b):
    return sum(x*y for x,y in zip(a,b)) / ((sum(x*x for x in a)**.5)*(sum(y*y for y in b)**.5) or 1)
