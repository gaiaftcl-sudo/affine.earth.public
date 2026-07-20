"""
LLM evaluation module for testing real AI Large Language Models across real-world domains.
"""

from .providers import (
    BaseProvider,
    OpenAICompatibleProvider,
    AnthropicProvider,
    DirectAffineEarthProvider,
    get_provider,
)
from .evaluator import LLMEvaluator
from .runner import LLMRunner
from .suites import get_suite, LIST_OF_SUITES

__all__ = [
    "BaseProvider",
    "OpenAICompatibleProvider",
    "AnthropicProvider",
    "DirectAffineEarthProvider",
    "get_provider",
    "LLMEvaluator",
    "LLMRunner",
    "get_suite",
    "LIST_OF_SUITES",
]
