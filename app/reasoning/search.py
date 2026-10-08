from __future__ import annotations
from dataclasses import dataclass
from app.core.types import VerificationResult

@dataclass
class Candidate:
    text:str
    score:float=0.0
    verification:VerificationResult|None=None

class SearchEngine:
    def __init__(self, provider, verifier=None):
        self.provider = provider
        self.verifier = verifier

    async def best_of_n(self, prompt: str, context: str, n: int = 3) -> list[Candidate]:
        candidates = []
        for i in range(n):
            out = await self.provider.generate(
                f"Problem:\n{prompt}\nEvidence:\n{context}\nGenerate candidate solution #{i+1}. Be concise."
            )
            c = Candidate(out)
            if self.verifier:
                vr = await self.verifier.verify_text(out, prompt)
                c.verification = vr
                c.score = vr.score
            candidates.append(c)
        return candidates

    async def self_refine(self, prompt: str, candidate: str, feedback: str = "") -> Candidate:
        if not feedback and self.verifier:
            vr = await self.verifier.verify_text(candidate, prompt)
            failed = [c["name"] for c in vr.checks if not c["passed"]]
            feedback = f"Failed checks: {', '.join(failed)}" if failed else "Improve evidence citations and conciseness."
        out = await self.provider.generate(
            f"Problem: {prompt}\nCandidate: {candidate}\nVerifier feedback: {feedback}\nReturn a corrected candidate."
        )
        c = Candidate(out)
        if self.verifier:
            vr = await self.verifier.verify_text(out, prompt)
            c.verification = vr
            c.score = vr.score
        return c

    async def beam_search(self, prompt: str, context: str, beam: int = 2, depth: int = 2) -> list[Candidate]:
        beams = await self.best_of_n(prompt, context, beam)
        for _ in range(1, depth):
            nxt = []
            for c in beams:
                feedback = ""
                if c.verification:
                    failed = [chk["name"] for chk in c.verification.checks if not chk["passed"]]
                    if failed:
                        feedback = f"Address failed checks: {', '.join(failed)}"
                nxt.append(await self.self_refine(prompt, c.text, feedback=feedback))
            pool = beams + nxt
            if self.verifier:
                pool = sorted(pool, key=lambda x: x.score, reverse=True)
            beams = pool[:beam]
        return beams

    async def mcts_like(self, prompt: str, context: str, rollouts: int = 6) -> list[Candidate]:
        if not self.verifier:
            return await self.best_of_n(prompt, context, min(rollouts, 8))
        from app.reasoning.mcts import MCTS
        tree = MCTS(self.provider, self.verifier)
        nodes = await tree.search(prompt, context, rollouts=min(rollouts, 20))
        return [n.candidate for n in nodes]
