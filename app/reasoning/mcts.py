from __future__ import annotations
import math
from dataclasses import dataclass, field
from app.reasoning.search import Candidate

@dataclass
class Node:
    candidate: Candidate
    parent: 'Node|None' = None
    children: list['Node'] = field(default_factory=list)
    visits: int = 0
    value: float = 0.0

    def uct(self, exploration=1.414):
        if self.visits == 0:
            return float('inf')
        parent_visits = max(self.parent.visits if self.parent else 1, 1)
        return self.value / self.visits + exploration * math.sqrt(math.log(parent_visits) / self.visits)

class MCTS:
    def __init__(self, provider, verifier, exploration=1.414):
        self.provider=provider; self.verifier=verifier; self.exploration=exploration

    async def search(self, problem, context, rollouts=8):
        root=Node(Candidate(text=problem))
        for _ in range(rollouts):
            node=root
            # Selection
            while node.children:
                node=max(node.children,key=lambda n:n.uct(self.exploration))
            # Expansion
            prompt=(f"Problem:\n{problem}\nEvidence:\n{context}\n"
                    f"Produce one concrete candidate solution. If improving an existing candidate, improve it.\n"
                    f"Current candidate:\n{node.candidate.text}")
            text=await self.provider.generate(prompt)
            child=Node(Candidate(text=text),parent=node)
            node.children.append(child)
            # Simulation/evaluation
            vr=await self.verifier.verify_text(text,problem)
            child.candidate.verification=vr
            child.candidate.score=vr.score
            reward=vr.score
            # Backpropagation
            cur=child
            while cur:
                cur.visits += 1
                cur.value += reward
                cur=cur.parent
        leaves=[]
        def walk(n):
            for c in n.children:
                leaves.append(c); walk(c)
        walk(root)
        if not leaves:
            return [root]
        return sorted(leaves,key=lambda n:(n.candidate.score,n.visits),reverse=True)
