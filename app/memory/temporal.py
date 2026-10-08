from datetime import datetime, timezone

def is_valid_at(valid_from, valid_until, at=None):
    at=at or datetime.now(timezone.utc)
    if valid_from and at < valid_from: return False
    if valid_until and at >= valid_until: return False
    return True

def latest_claim(claims, subject_id, predicate):
    candidates=[c for c in claims if c.subject_id==subject_id and c.predicate==predicate and c.status in {'active','contested'}]
    return max(candidates,key=lambda c:c.valid_from,default=None)
