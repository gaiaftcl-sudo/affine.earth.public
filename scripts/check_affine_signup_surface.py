#!/usr/bin/env python3
"""Smoke-check Affine.Earth signup / Sovereign entry surface (no account creation).

Asserts that the public language-game page is reachable and exposes the
wallet-based signup markers observed in the live DOM, including consent,
Use my location, Create wallet + QFOT, and post-login Q&A route markers.
Does not create wallets, sign in, complete consent, or claim auth success.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any, Dict, List, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_ROOT = "https://affine.earth"
DEFAULT_LANGUAGE_GAME = "https://affine.earth/language-game/"

# Markers present in the live HTML served on 2026-07-20 (correct signup path).
REQUIRED_MARKERS = (
    'id="loginGate"',
    'id="tabNewUser"',
    'id="tabReturning"',
    'id="loginCreateBtn"',
    'id="loginConsent"',
    'id="loginGeoBtn"',
    'id="loginAddress"',
    "Sovereign entry",
    "Create wallet + QFOT",
    "Use my location",
    "New wallet",
    "Returning",
)

# Post-login / Q&A surface markers discoverable without secrets.
QA_ROUTE_MARKERS = (
    'id="gamesBtn"',
    'id="gamesCatalog"',
    'id="messageList"',
    'id="profileBtn"',
    'id="exportKeyBtn"',
)


def fetch(url: str, timeout: float) -> Tuple[int, str, str]:
    req = Request(url, headers={"User-Agent": "llm-llvm-bench-signup-smoke/1.0"})
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310 — intentional live probe
        body = resp.read().decode("utf-8", errors="replace")
        ctype = resp.headers.get("Content-Type", "")
        return int(resp.status), ctype, body


def check_page(url: str, timeout: float) -> Dict[str, Any]:
    started = time.perf_counter()
    try:
        status, ctype, body = fetch(url, timeout=timeout)
        latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
        missing = [m for m in REQUIRED_MARKERS if m not in body]
        qa_missing = [m for m in QA_ROUTE_MARKERS if m not in body]
        return {
            "url": url,
            "ok": status == 200 and not missing,
            "status_code": status,
            "content_type": ctype,
            "latency_ms": latency_ms,
            "missing_markers": missing,
            "marker_count_ok": len(REQUIRED_MARKERS) - len(missing),
            "marker_count_required": len(REQUIRED_MARKERS),
            "qa_route_markers_ok": len(QA_ROUTE_MARKERS) - len(qa_missing),
            "qa_route_markers_required": len(QA_ROUTE_MARKERS),
            "qa_route_missing": qa_missing,
            "qa_routes_present": not qa_missing,
        }
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
        return {
            "url": url,
            "ok": False,
            "status_code": getattr(exc, "code", None),
            "content_type": "",
            "latency_ms": latency_ms,
            "missing_markers": list(REQUIRED_MARKERS),
            "qa_route_missing": list(QA_ROUTE_MARKERS),
            "qa_routes_present": False,
            "error": str(exc),
        }


def probe_onboard_not_create(timeout: float) -> Dict[str, Any]:
    """Probe economics-onboard without creating a user.

    Documents reachability only. A 404 is reported honestly; this is not a
    registration attempt (empty body, no address).
    """
    url = "https://affine.earth/language-invariant/economics-onboard"
    started = time.perf_counter()
    req = Request(
        url,
        data=b"{}",
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "llm-llvm-bench-signup-smoke/1.0",
        },
    )
    try:
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310
            body = resp.read().decode("utf-8", errors="replace")[:400]
            return {
                "url": url,
                "status_code": int(resp.status),
                "latency_ms": round((time.perf_counter() - started) * 1000.0, 2),
                "body_prefix": body,
                "note": "Probe only — not a successful registration claim.",
            }
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:400] if exc.fp else ""
        return {
            "url": url,
            "status_code": int(exc.code),
            "latency_ms": round((time.perf_counter() - started) * 1000.0, 2),
            "body_prefix": body,
            "note": "Probe only — not a successful registration claim.",
        }
    except (URLError, TimeoutError, OSError) as exc:
        return {
            "url": url,
            "status_code": None,
            "latency_ms": round((time.perf_counter() - started) * 1000.0, 2),
            "error": str(exc),
            "note": "Probe only — not a successful registration claim.",
        }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--language-game", default=DEFAULT_LANGUAGE_GAME)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument(
        "--json-out",
        default="",
        help="Optional path to write the full probe report JSON.",
    )
    parser.add_argument(
        "--require-qa-routes",
        action="store_true",
        help="Also fail if Games/messageList/export markers are missing.",
    )
    args = parser.parse_args(argv)

    results = [
        check_page(args.root, args.timeout),
        check_page(args.language_game, args.timeout),
    ]
    onboard = probe_onboard_not_create(args.timeout)
    signup_ok = all(r.get("ok") for r in results)
    qa_ok = all(r.get("qa_routes_present") for r in results)
    report = {
        "proven_status": "SIGNUP_SURFACE_REACHABLE"
        if signup_ok
        else "SIGNUP_SURFACE_CHECK_FAILED",
        "qa_routes_status": "QA_ROUTE_MARKERS_PRESENT"
        if qa_ok
        else "QA_ROUTE_MARKERS_MISSING",
        "pages": results,
        "economics_onboard_probe": onboard,
        "correct_ui_path": [
            "New wallet (#tabNewUser)",
            "consent checkbox (#loginConsent)",
            "Use my location (#loginGeoBtn)",
            "Create wallet + QFOT (#loginCreateBtn)",
            "app opens → Games (#gamesBtn) / Linguistic membrane / #messageList Q&A",
        ],
        "manual_only": [
            "consent + Use my location + Create wallet + QFOT (creates edge wallet)",
            "Export private key backup",
            "Returning Sign in with a controlled BTC address",
        ],
        "superseded_demo": [
            "affine-earth-demo-signup-healthz.* / demo-signup-healthz.gif",
            "use affine-earth-demo-signup-app-qa.* / demo-signup-app-qa.gif",
        ],
    }

    text = json.dumps(report, indent=2)
    print(text)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")

    if not signup_ok:
        print(
            "FAIL: signup/login surface markers missing or non-200.",
            file=sys.stderr,
        )
        return 1
    if args.require_qa_routes and not qa_ok:
        print("FAIL: post-login Q&A route markers missing.", file=sys.stderr)
        return 1
    print(
        "OK: Sovereign entry signup surface reachable "
        "(consent + use-my-location + create-wallet markers; no account created).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
