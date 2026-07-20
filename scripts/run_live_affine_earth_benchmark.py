"""Record a measured availability probe for an OpenAI-compatible /v1 endpoint."""

from __future__ import annotations

import json
import os
import time
from typing import Optional

import requests


def _first_env(*names: str) -> Optional[str]:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def probe_openai_endpoint() -> None:
    base_url = _first_env(
        "AFFINE_HARNESS_ENDPOINT",
        "AFFINE_OPENAI_BASE_URL",
        "OPENAI_BASE_URL",
        "AFFINE_BASE_URL",
    )
    api_key = _first_env("OPENAI_API_KEY", "AFFINE_HARNESS_API_KEY")
    if not base_url:
        raise SystemExit(
            "Set AFFINE_HARNESS_ENDPOINT, OPENAI_BASE_URL, or AFFINE_BASE_URL "
            "(OpenAI-compatible /v1 that returns JSON from /models)."
        )
    if not api_key:
        raise SystemExit("Set OPENAI_API_KEY or AFFINE_HARNESS_API_KEY.")

    url = f"{base_url.rstrip('/')}/models"
    started = time.perf_counter()
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        timeout=10,
    )
    elapsed_seconds = time.perf_counter() - started
    content_type = response.headers.get("Content-Type", "")
    body_prefix = response.text[:200]
    if "application/json" not in content_type and not body_prefix.lstrip().startswith("{"):
        raise SystemExit(
            f"GET {url} did not return JSON (HTTP {response.status_code}, "
            f"Content-Type={content_type!r}). "
            "https://affine.earth/v1 currently returns an HTML SPA."
        )
    response.raise_for_status()
    payload = response.json()

    os.makedirs("reports", exist_ok=True)
    output = "reports/affine_endpoint_probe.json"
    with open(output, "w", encoding="utf-8") as report:
        json.dump(
            {
                "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "endpoint": url,
                "http_status": response.status_code,
                "content_type": content_type,
                "elapsed_seconds": elapsed_seconds,
                "models": [model.get("id") for model in payload.get("data", [])],
            },
            report,
            indent=2,
        )
    print(f"OpenAI-compatible endpoint responded: HTTP {response.status_code}")
    print(f"Measured endpoint probe: {output}")


if __name__ == "__main__":
    probe_openai_endpoint()
