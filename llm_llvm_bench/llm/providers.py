import time
import json
import os
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
from ..core.types import LLMModelConfig

class BaseProvider(ABC):
    def __init__(self, config: LLMModelConfig):
        self.config = config

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Tuple[str, float, int, int]:
        """
        Returns: (completion_text, latency_seconds, prompt_tokens, completion_tokens)
        """
        pass

class OpenAICompatibleProvider(BaseProvider):
    """
    Connects to OpenAI, DeepSeek, Qwen, vLLM, Ollama, or local Affine.Earth endpoints.
    """
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Tuple[str, float, int, int]:
        endpoint = self.config.endpoint or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions")
        headers = {
            "Content-Type": "application/json",
        }
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.config.name,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        start = time.time()
        try:
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=60)
            latency = time.time() - start
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", len(prompt.split()))
            completion_tokens = usage.get("completion_tokens", len(choice.split()))
            return choice, latency, prompt_tokens, completion_tokens
        except Exception as e:
            latency = time.time() - start
            return f"ERROR: {str(e)}", latency, 0, 0

class AnthropicProvider(BaseProvider):
    """
    Connects to Anthropic Claude API (Claude 3.5 / 3.7 Sonnet).
    """
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Tuple[str, float, int, int]:
        endpoint = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.config.api_key or os.getenv("ANTHROPIC_API_KEY", ""),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.config.name,
            "max_tokens": self.config.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt

        start = time.time()
        try:
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=60)
            latency = time.time() - start
            resp.raise_for_status()
            data = resp.json()
            choice = data["content"][0]["text"]
            usage = data.get("usage", {})
            prompt_tokens = usage.get("input_tokens", len(prompt.split()))
            completion_tokens = usage.get("output_tokens", len(choice.split()))
            return choice, latency, prompt_tokens, completion_tokens
        except Exception as e:
            latency = time.time() - start
            return f"ERROR: {str(e)}", latency, 0, 0

class DirectAffineEarthProvider(BaseProvider):
    """
    Connects directly to Affine.Earth OS live language-game and NATS endpoints.
    """
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Tuple[str, float, int, int]:
        endpoint = self.config.endpoint or "https://affine.earth/language-invariant/healthz"
        start = time.time()
        try:
            resp = requests.get(endpoint, timeout=10, verify=False)
            latency = time.time() - start
            return f"Affine.Earth Status: {resp.status_code}", latency, len(prompt.split()), 10
        except Exception as e:
            latency = time.time() - start
            return f"ERROR: {str(e)}", latency, 0, 0

def get_provider(config: LLMModelConfig) -> BaseProvider:
    provider_type = config.provider.lower()
    if provider_type == "anthropic":
        return AnthropicProvider(config)
    elif provider_type == "affine_earth":
        return DirectAffineEarthProvider(config)
    else:
        return OpenAICompatibleProvider(config)
