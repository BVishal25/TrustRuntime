from __future__ import annotations
import httpx
from app.core.config import get_settings

class ModelProvider:
    async def generate(self,prompt:str,system:str="")->str: raise NotImplementedError

class DeterministicProvider(ModelProvider):
    async def generate(self,prompt,system=""):
        return "VERIFIED-DEMO: " + prompt.strip()[:600]

class OllamaProvider(ModelProvider):
    def __init__(self,base_url=None,model=None):
        s=get_settings(); self.base=base_url or s.ollama_base_url; self.model=model or s.ollama_model
    async def generate(self,prompt,system=""):
        async with httpx.AsyncClient(timeout=120) as c:
            r=await c.post(self.base.rstrip("/")+"/api/chat",json={"model":self.model,"messages":[{"role":"system","content":system},{"role":"user","content":prompt}],"stream":False})
            r.raise_for_status(); return r.json()["message"]["content"]

class OpenAICompatibleProvider(ModelProvider):
    def __init__(self):
        s=get_settings(); self.base=s.cloud_model_base_url; self.key=s.cloud_model_api_key; self.model=s.cloud_model_name
    async def generate(self,prompt,system=""):
        async with httpx.AsyncClient(timeout=120) as c:
            r=await c.post(self.base.rstrip("/")+"/chat/completions",headers={"Authorization":f"Bearer {self.key}"},json={"model":self.model,"messages":[{"role":"system","content":system},{"role":"user","content":prompt}]})
            r.raise_for_status(); return r.json()["choices"][0]["message"]["content"]
