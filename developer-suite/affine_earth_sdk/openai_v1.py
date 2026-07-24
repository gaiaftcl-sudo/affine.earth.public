"""OpenAI-compatible /v1 client — chat, responses, models, api-keys."""
from __future__ import annotations

from typing import Any, Mapping, Optional

from .client import AffineClient


class OpenAIV1Client:
    def __init__(self, client: AffineClient, prefix: str = "/v1") -> None:
        self.client = client
        self.prefix = prefix.rstrip("/")

    def models(self) -> dict[str, Any]:
        r = self.client.get(f"{self.prefix}/models")
        r.raise_for_status()
        return r.json()

    def chat_completions(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str = "franklin-membrane",
        stream: bool = False,
        max_tokens: int = 256,
        temperature: float = 0.0,
        exam: bool = False,
        extra_headers: Optional[Mapping[str, str]] = None,
        **kwargs: Any,
    ) -> Any:
        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        body.update(kwargs)
        headers = self.client.bearer_headers(extra_headers)
        if exam:
            headers["X-Affine-Exam"] = "hle"
            if "exam" not in model.lower():
                body["model"] = "franklin-membrane-exam"
        r = self.client.post(
            f"{self.prefix}/chat/completions",
            json=body,
            headers=headers,
        )
        r.raise_for_status()
        if stream:
            return r.text
        return r.json()

    def responses(
        self,
        input_data: Any,
        *,
        model: str = "franklin-membrane",
        instructions: Optional[str] = None,
        store: bool = False,
        max_output_tokens: int = 256,
        exam: bool = False,
        extra_headers: Optional[Mapping[str, str]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": model,
            "input": input_data,
            "store": store,
            "max_output_tokens": max_output_tokens,
        }
        if instructions:
            body["instructions"] = instructions
        body.update(kwargs)
        headers = self.client.bearer_headers(extra_headers)
        if exam:
            headers["X-Affine-Exam"] = "hle"
            if "exam" not in model.lower():
                body["model"] = "franklin-membrane-exam"
        r = self.client.post(f"{self.prefix}/responses", json=body, headers=headers)
        r.raise_for_status()
        return r.json()

    def list_api_keys(self) -> dict[str, Any]:
        r = self.client.get(
            f"{self.prefix}/api-keys",
            headers=self.client.bearer_headers(),
        )
        r.raise_for_status()
        return r.json()

    def create_api_key(self, name: str = "issued") -> dict[str, Any]:
        r = self.client.post(
            f"{self.prefix}/api-keys",
            json={"name": name},
            headers=self.client.bearer_headers(),
        )
        r.raise_for_status()
        return r.json()
