from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class ProvenanceRecord:
    source_id: str
    source_type: str
    observed_at: datetime
    extractor: str
    extractor_version: str
    confidence: float

def make_provenance(source_id, source_type, confidence, extractor='rule+llm', version='1.0'):
    return ProvenanceRecord(source_id,source_type,datetime.now(timezone.utc),extractor,version,confidence)
