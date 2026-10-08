import asyncio, json, time
from app.db.database import init_db, SessionLocal
from app.db.repository import Repository
from app.memory.store import MemoryEngine
from app.models.router import ModelRouter
from app.tools.registry import build_default_registry
from app.observability.audit import AuditLogger
from app.core.runtime import TrustRuntime
from app.core.types import AgentTask

async def main():
    await init_db(); s=SessionLocal(); r=Repository(s); rt=TrustRuntime(MemoryEngine(r),r,ModelRouter(),build_default_registry(),AuditLogger(r))
    cases=json.load(open("data/benchmarks/tasks.json"))
    rows=[]
    for c in cases:
      st=time.perf_counter(); out=await rt.run(AgentTask(task_id=c["id"],prompt=c["prompt"],strategy=c.get("strategy","best_of_n"),candidate_count=c.get("n",3))); rows.append({"id":c["id"],"status":out.status,"confidence":out.confidence,"latency_ms":(time.perf_counter()-st)*1000,"attempts":out.attempts})
    print(json.dumps(rows,indent=2))
    await s.commit()
    await s.close()
    from app.evaluation import summarize
    summary = summarize(rows)
    print(f"\n--- Summary: Total={summary.total} | Verified={summary.verified} | Success Rate={summary.success_rate:.1%} | Avg Latency={summary.average_latency_ms:.1f}ms ---")
if __name__=="__main__": asyncio.run(main())
