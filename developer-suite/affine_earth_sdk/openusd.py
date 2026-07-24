"""OpenUSD / airspace fetch helpers (static USDA under /language-game/)."""
from __future__ import annotations

import re
from typing import Any, Optional

from .client import AffineClient

DEFAULT_AIRSPACE_USDA = "/language-game/airspace-lattice.usda"
DEFAULT_AIRSPACE_HTML = "/language-game/airspace.html"


class OpenUSDClient:
    def __init__(self, client: AffineClient) -> None:
        self.client = client

    def fetch_text(self, path: str = DEFAULT_AIRSPACE_USDA) -> str:
        r = self.client.get(path)
        r.raise_for_status()
        return r.text

    def airspace_usda(self) -> str:
        return self.fetch_text(DEFAULT_AIRSPACE_USDA)

    def airspace_html_ok(self) -> bool:
        r = self.client.get(DEFAULT_AIRSPACE_HTML)
        return r.status_code == 200 and len(r.content) > 100

    def observer_demo(self) -> dict[str, Any]:
        r = self.client.get("/language-invariant/observer-demo")
        r.raise_for_status()
        ctype = r.headers.get("content-type", "")
        if "json" in ctype:
            return r.json()
        return {"content_type": ctype, "text": r.text[:2000], "bytes": len(r.content)}

    def parse_def_names(self, usda: str) -> list[str]:
        """Lightweight USDA def Xform / Mesh name scan (no usdview required)."""
        names = re.findall(r"\bdef\s+\w+\s+[\"']([^\"']+)[\"']", usda)
        return names

    def summary(self, usda: Optional[str] = None) -> dict[str, Any]:
        text = usda if usda is not None else self.airspace_usda()
        defs = self.parse_def_names(text)
        return {
            "bytes": len(text.encode("utf-8")),
            "lines": text.count("\n") + 1,
            "def_count": len(defs),
            "def_names_sample": defs[:24],
            "has_upAxis": "upAxis" in text or "upAxis =" in text,
            "path": DEFAULT_AIRSPACE_USDA,
        }
