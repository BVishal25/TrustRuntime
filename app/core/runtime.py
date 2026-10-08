from __future__ import annotations
import uuid
from datetime import datetime, timezone
from app.core.types import AgentTask, AgentRunResult, Evidence, ToolRequest, SecurityDecision
from app.reasoning.search import SearchEngine
from app.verification.verifier import Verifier
from app.security.policy import PolicyEngine
from app.security.injection import classify_content
from app.observability.telemetry import RunMetrics
from app.db.models import RunRow

class TrustRuntime:
    def __init__(self, memory, repo, router, tools, audit):
        self.memory = memory
        self.repo = repo
        self.router = router
        self.tools = tools
        self.audit = audit
        self.verifier = Verifier()
        self.policy = PolicyEngine()

    async def run(self, task: AgentTask) -> AgentRunResult:
        metrics = RunMetrics()
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        security_events: list[SecurityDecision] = []
        tool_results: list[dict] = []

        # 1. REMEMBER: Retrieve relevant evidence
        evidence = await self.memory.search(task.prompt, 5)
        metrics.inc("retrieval_hits", len(evidence))
        if self.audit:
            await self.audit.log(run_id, "memory_retrieval", {"query": task.prompt, "hits": len(evidence)}, allowed=True)

        # 2. CHECK UNTRUSTED RETRIEVAL (Indirect Injection / Poisoning)
        for e in evidence:
            classification = classify_content(e.text)
            if classification["suspicious"]:
                decision = self.policy.evaluate(
                    ToolRequest(tool_name="unknown", reason=f"Suspicious evidence content: {e.text[:100]}"),
                    role=task.role
                )
                security_events.append(decision)
                if self.audit:
                    await self.audit.log(run_id, "untrusted_evidence_detected", {
                        "source_id": e.source_id,
                        "patterns": classification["patterns"],
                        "decision": decision.decision
                    }, allowed=False)

        # Check prompt for direct injection patterns
        prompt_classification = classify_content(task.prompt)
        if prompt_classification["suspicious"]:
            decision = SecurityDecision(
                decision="deny",
                risk="high",
                reasons=[f"Prompt injection patterns detected: {', '.join(prompt_classification['patterns'])}"],
                policy_id="prompt-injection-guard"
            )
            security_events.append(decision)
            if self.audit:
                await self.audit.log(run_id, "prompt_injection_detected", {
                    "patterns": prompt_classification["patterns"]
                }, allowed=False)

        # 3. AUTHORIZE & ACT (Tools) if requested
        context_extra = ""
        if task.tool_request and task.allow_tools:
            tool_dec = self.policy.evaluate(task.tool_request, role=task.role, approved=task.approved)
            security_events.append(tool_dec)
            if tool_dec.decision == "allow":
                try:
                    res = await self.tools.execute(task.tool_request)
                    tool_results.append({"tool": task.tool_request.tool_name, "result": res})
                    metrics.inc("tool_calls", 1)
                    context_extra = f"\nTool Output ({task.tool_request.tool_name}): {str(res)}"
                    if self.audit:
                        await self.audit.log(run_id, "tool_execution", {
                            "tool": task.tool_request.tool_name,
                            "arguments": task.tool_request.arguments,
                            "status": "success"
                        }, allowed=True)
                except Exception as ex:
                    tool_results.append({"tool": task.tool_request.tool_name, "error": str(ex)})
                    if self.audit:
                        await self.audit.log(run_id, "tool_execution", {
                            "tool": task.tool_request.tool_name,
                            "error": str(ex)
                        }, allowed=False)
            else:
                tool_results.append({"tool": task.tool_request.tool_name, "blocked": True, "reasons": tool_dec.reasons})
                if self.audit:
                    await self.audit.log(run_id, "tool_blocked", {
                        "tool": task.tool_request.tool_name,
                        "decision": tool_dec.decision,
                        "reasons": tool_dec.reasons
                    }, allowed=False)

        # 4. REASON: Search engine candidate generation
        context = "\n".join(f"[{e.source_id}] {e.text}" for e in evidence) + context_extra
        difficulty = min(1.0, len(task.prompt) / 1200.0)
        provider = self.router.choose(difficulty)
        search = SearchEngine(provider, self.verifier)

        if task.strategy == "beam_search":
            candidates = await search.beam_search(task.prompt, context, beam=min(task.candidate_count, 4), depth=2)
        elif task.strategy == "mcts":
            candidates = await search.mcts_like(task.prompt, context, rollouts=task.candidate_count)
        else:
            candidates = await search.best_of_n(task.prompt, context, task.candidate_count)

        metrics.inc("attempts", len(candidates))
        total_tokens = int((len(task.prompt) + len(context) + sum(len(c.text) for c in candidates)) / 3.5)
        metrics.inc("tokens_estimate", total_tokens)

        # 5. VERIFY: Deterministic scoring
        scored = []
        for c in candidates:
            if c.verification is None:
                vr = await self.verifier.verify_text(c.text, task.prompt)
                c.verification = vr
                c.score = vr.score
            scored.append(c)

        best = max(scored, key=lambda x: x.score, default=None)
        answer = best.text if best else "No candidate produced."
        status = "verified" if (best and best.verification and best.verification.passed) else "needs_review"

        # 6. LEARN / RECORD
        metrics.finish()
        if self.repo:
            try:
                run_row = RunRow(
                    id=run_id,
                    task_id=task.task_id,
                    status=status,
                    answer=answer,
                    metrics=metrics.data,
                    created_at=datetime.now(timezone.utc)
                )
                await self.repo.save_run(run_row)
            except Exception:
                pass

        if self.audit:
            await self.audit.log(run_id, "run_completed", {
                "task_id": task.task_id,
                "status": status,
                "strategy": task.strategy,
                "score": best.score if best else 0
            }, allowed=True)

        return AgentRunResult(
            task_id=task.task_id,
            status=status,
            answer=answer,
            confidence=best.score if best else 0.0,
            attempts=len(candidates),
            verification=best.verification if best else None,
            security_events=security_events,
            tool_results=tool_results,
            evidence=evidence,
            metrics=metrics.data
        )
