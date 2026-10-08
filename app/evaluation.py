from dataclasses import dataclass
from statistics import mean

@dataclass
class BenchmarkSummary:
    total:int
    verified:int
    average_confidence:float
    average_latency_ms:float
    average_attempts:float

    @property
    def success_rate(self): return self.verified/self.total if self.total else 0.0

def summarize(rows):
    return BenchmarkSummary(len(rows),sum(r.get('status')=='verified' for r in rows),mean([r.get('confidence',0) for r in rows]) if rows else 0,mean([r.get('latency_ms',0) for r in rows]) if rows else 0,mean([r.get('attempts',0) for r in rows]) if rows else 0)
