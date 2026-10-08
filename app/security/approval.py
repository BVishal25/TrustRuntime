from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class ApprovalRequest:
    request_id: str
    tool_name: str
    requested_by: str
    risk: str
    created_at: datetime
    status: str='pending'

class ApprovalStore:
    def __init__(self): self.items={}
    def create(self,request_id,tool_name,requested_by,risk):
        x=ApprovalRequest(request_id,tool_name,requested_by,risk,datetime.now(timezone.utc)); self.items[request_id]=x; return x
    def decide(self,request_id,approved):
        x=self.items[request_id]; x.status='approved' if approved else 'rejected'; return x
