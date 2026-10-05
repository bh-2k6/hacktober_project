from .base import AIProvider, ItemAnalysis
from .mock import MockAIProvider
from .ollama import OllamaAIProvider


def create_ai_provider():
    from app.config import AI_PROVIDER
    if AI_PROVIDER == "ollama":
        return OllamaAIProvider()
    return MockAIProvider()


__all__ = ["AIProvider", "ItemAnalysis", "MockAIProvider", "OllamaAIProvider", "create_ai_provider"]
