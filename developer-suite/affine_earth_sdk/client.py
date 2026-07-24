"""HTTP client for Affine.Earth apex (httpx)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional

import httpx


@dataclass
class AffineConfig:
    base_url: str = "https://affine.earth"
    api_key: str = "uum8d-hle-verifier"
    timeout_s: float = 60.0

    @classmethod
    def from_env(cls) -> "AffineConfig":
        return cls(
            base_url=(os.environ.get("AFFINE_BASE_URL") or "https://affine.earth").rstrip("/"),
            api_key=(os.environ.get("AFFINE_API_KEY") or "uum8d-hle-verifier").strip(),
            timeout_s=float(os.environ.get("AFFINE_TIMEOUT_S") or "60"),
        )


class AffineClient:
    """Shared HTTPS session — Bearer for OpenAI /v1; MCP/games are usually unauthenticated."""

    def __init__(self, config: Optional[AffineConfig] = None) -> None:
        self.config = config or AffineConfig.from_env()
        self._client = httpx.Client(
            base_url=self.config.base_url,
            timeout=self.config.timeout_s,
            headers={"User-Agent": "affine-earth-developer-suite/0.1"},
            follow_redirects=True,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "AffineClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return self.config.base_url + (path if path.startswith("/") else "/" + path)

    def bearer_headers(self, extra: Optional[Mapping[str, str]] = None) -> dict[str, str]:
        h = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        if extra:
            h.update(dict(extra))
        return h

    def get(
        self,
        path: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        params: Optional[Mapping[str, Any]] = None,
    ) -> httpx.Response:
        return self._client.get(path, headers=headers, params=params)

    def post(
        self,
        path: str,
        *,
        json: Any = None,
        headers: Optional[Mapping[str, str]] = None,
        data: Any = None,
    ) -> httpx.Response:
        return self._client.post(path, json=json, headers=headers, content=data)

    def delete(
        self,
        path: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
    ) -> httpx.Response:
        return self._client.delete(path, headers=headers)

    def healthz(self) -> dict[str, Any]:
        r = self.get("/language-invariant/healthz")
        r.raise_for_status()
        return r.json()
