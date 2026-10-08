from datetime import datetime, timezone
from app.db.models import AuditEventRow

class AuditLogger:
    def __init__(self,repo): self.repo=repo
    async def log(self,run_id,event_type,payload,allowed=True):
        await self.repo.audit(AuditEventRow(run_id=run_id,event_type=event_type,allowed=allowed,payload=payload,created_at=datetime.now(timezone.utc)))
