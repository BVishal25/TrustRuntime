from __future__ import annotations
import ast, time
from app.core.types import VerificationResult

class Verifier:
    async def verify_text(self,text,task):
        checks=[]
        nonempty=bool(text.strip()); checks.append({"name":"non_empty","passed":nonempty})
        evidence_words=any(w in text.lower() for w in ("evidence","because","verified","source"))
        checks.append({"name":"evidence_signal","passed":evidence_words})
        score=sum(x["passed"] for x in checks)/len(checks)
        return VerificationResult(passed=score>=.5,score=score,checks=checks)
    def static_python(self,code):
        dangerous={"exec","eval","compile","__import__","open","system","popen","subprocess"}
        try: tree=ast.parse(code)
        except SyntaxError as e: return VerificationResult(passed=False,score=0,stderr=str(e),checks=[{"name":"syntax","passed":False}])
        bad=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Name) and node.id in dangerous: bad.append(node.id)
            if isinstance(node,ast.Attribute) and node.attr in {"system","popen","run"}: bad.append(node.attr)
        return VerificationResult(passed=not bad,score=1.0 if not bad else 0,checks=[{"name":"static_safety","passed":not bad,"findings":bad}])
