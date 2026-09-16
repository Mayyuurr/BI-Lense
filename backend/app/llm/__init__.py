"""Local LLaMA-7B Integration Package.

Provides copilot abstractions for semantic schema preprocessing and
decision support explanation generation.
"""

from app.llm.llama_client import BaseLLMClient, LocalLLaMAClient
from app.llm.semantic_copilot import SemanticCopilot, SchemaInferenceResult
from app.llm.explanation import ExplanationSynthesizer, BusinessNarrative

__all__ = [
    "BaseLLMClient",
    "LocalLLaMAClient",
    "SemanticCopilot",
    "SchemaInferenceResult",
    "ExplanationSynthesizer",
    "BusinessNarrative",
]
