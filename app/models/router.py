from app.core.config import get_settings
from app.reasoning.providers import DeterministicProvider, OllamaProvider, OpenAICompatibleProvider

class ModelRouter:
    def __init__(self):
        s=get_settings(); self.local=OllamaProvider() if s.ollama_enabled else DeterministicProvider(); self.fallback=OpenAICompatibleProvider() if s.cloud_model_enabled else DeterministicProvider()
    def choose(self,difficulty:float): return self.fallback if difficulty>.75 and get_settings().cloud_model_enabled else self.local
