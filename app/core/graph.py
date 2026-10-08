from typing import TypedDict
try:
    from langgraph.graph import StateGraph, END
except Exception:
    StateGraph=None; END='__end__'

class RuntimeState(TypedDict, total=False):
    task: str
    evidence: list
    candidates: list
    selected: str
    security: list
    verification: dict
    answer: str


def build_langgraph(runtime):
    if StateGraph is None: return None
    g=StateGraph(RuntimeState)
    async def retrieve(s): s['evidence']=[e.model_dump() for e in await runtime.memory.search(s['task'],5)]; return s
    async def reason(s):
        ctx='\n'.join(x['text'] for x in s.get('evidence',[])); cs=await runtime.router.choose(.5).generate('Solve:\n'+s['task']+'\nEvidence:\n'+ctx); s['candidates']=[cs]; return s
    async def verify(s):
        v=await runtime.verifier.verify_text(s['candidates'][0],s['task']); s['verification']=v.model_dump(); s['answer']=s['candidates'][0]; return s
    g.add_node('retrieve',retrieve); g.add_node('reason',reason); g.add_node('verify',verify)
    g.set_entry_point('retrieve'); g.add_edge('retrieve','reason'); g.add_edge('reason','verify'); g.add_edge('verify',END)
    return g.compile()
