#!/usr/bin/env python3
"""Fail if Mach-O / ELF / GGUF / oversized opaque blobs appear under developer-suite."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_OPAQUE_BYTES = 2 * 1024 * 1024
SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    "*.egg-info",
}
FORBIDDEN_SUFFIXES = (
    ".gguf",
    ".ggml",
    ".bin",
    ".dylib",
    ".so",
    ".a",
    ".o",
    ".wasm",
    ".metallib",
    ".app",
    ".dmg",
    ".iso",
)
MACH_O = b"\xcf\xfa\xed\xfe"
MACH_O_BE = b"\xfe\xed\xfa\xcf"
ELF = b"\x7fELF"
GGUF = b"GGUF"


def main() -> int:
    bad: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES or part.endswith(".egg-info") for part in path.parts):
            continue
        rel = path.relative_to(ROOT).as_posix()
        low = rel.lower()
        if any(low.endswith(s) for s in FORBIDDEN_SUFFIXES):
            bad.append(f"forbidden suffix: {rel}")
            continue
        if "gaiaftclcli" in low or low.startswith("gaiaftcl"):
            bad.append(f"os binary name: {rel}")
            continue
        try:
            head = path.read_bytes()[:8]
        except OSError as exc:
            bad.append(f"unreadable {rel}: {exc}")
            continue
        if head.startswith(MACH_O) or head.startswith(MACH_O_BE) or head.startswith(ELF) or head.startswith(GGUF):
            bad.append(f"binary magic: {rel}")
            continue
        # Opaque large non-text files
        if path.suffix.lower() not in {
            ".py",
            ".md",
            ".txt",
            ".toml",
            ".json",
            ".html",
            ".js",
            ".css",
            ".c",
            ".h",
            ".usda",
            ".example",
            ".gitignore",
            ".yml",
            ".yaml",
        }:
            size = path.stat().st_size
            if size > MAX_OPAQUE_BYTES:
                bad.append(f"oversized opaque ({size} B): {rel}")
    if bad:
        print("NO_BINARIES_FAIL")
        for line in bad:
            print(" ", line)
        return 1
    print("NO_BINARIES_PASS", ROOT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
