#!/usr/bin/env python3
"""Capture Affine.Earth Linguistic / Formal / Coding exam-style UI screenshots.

Produces wiki/assets/exam-ui-hle-*.png plus gif/mp4 of context→answer frames.
Interaction evidence only — not an HLE score. No Keychain.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

ROOT = "https://affine.earth"
ASSETS = Path("wiki/assets")

GAMES = {
    "linguistic_membrane": (
        "Linguistic membrane",
        "Exam-style context drill: bind question identity, then answer with the "
        "option letter only. Which planet is commonly called the Red Planet? "
        "A) Earth B) Mars C) Venus D) Mercury",
        "chat",
    ),
    "formal_manifold": (
        "Formal manifold",
        "Formal answer-contract drill: return only the exact token. "
        "What is the chemical symbol for gold?",
        "ingest",
    ),
    "coding": (
        "Coding — UMC + MCP",
        "Coding harness drill: answer format exact_token. "
        "A triangle has angles 50, 60, and x degrees. What is x?",
        "chat_or_ingest",
    ),
}


def onboard(page) -> None:
    page.goto(f"{ROOT}/language-game/", wait_until="domcontentloaded")
    page.wait_for_timeout(900)
    page.locator("#tabNewUser").click()
    page.locator("#loginConsent").check(force=True)
    page.locator("#loginGeoBtn").click()
    page.wait_for_timeout(700)
    page.locator("#loginCreateBtn").click(force=True)
    page.wait_for_selector("#loginGate", state="hidden", timeout=30000)


def open_game(page, label: str) -> None:
    page.locator("#gamesBtn").click()
    page.wait_for_timeout(500)
    page.get_by_text(label, exact=False).first.click()
    page.wait_for_timeout(900)


def ask_chat(page, question: str) -> bool:
    chat = page.locator("#textInput")
    if not chat.count() or not chat.is_enabled():
        return False
    before = page.locator("#messageList").inner_text() if page.locator("#messageList").count() else ""
    page.get_by_placeholder("Message Franklin").fill(question)
    page.get_by_placeholder("Message Franklin").press("Enter")
    try:
        page.wait_for_function(
            """prev => {
              const t = (document.querySelector('#messageList') || {}).innerText || '';
              return t.length > (prev || '').length + 40;
            }""",
            arg=before,
            timeout=60000,
        )
        return True
    except PlaywrightTimeout:
        return False


def maybe_make_media(out_dir: Path) -> tuple[str | None, str | None]:
    frames = []
    for key in GAMES:
        frames.append(out_dir / f"exam-ui-hle-{key}.png")
        frames.append(out_dir / f"exam-ui-hle-{key}-answer.png")
    present = [str(path.resolve()) for path in frames if path.exists()]
    if len(present) < 2 or not shutil.which("ffmpeg"):
        return None, None
    list_file = Path("reports/hle_ui_ffmpeg_list.txt")
    list_file.parent.mkdir(parents=True, exist_ok=True)
    list_file.write_text(
        "".join(f"file '{path}'\nduration 1.2\n" for path in present)
        + f"file '{present[-1]}'\n",
        encoding="utf-8",
    )
    gif_path = out_dir / "exam-ui-hle-context-to-answer.gif"
    mp4_path = out_dir / "exam-ui-hle-context-to-answer.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-vf", "fps=2,scale=960:-1:flags=lanczos", str(gif_path),
        ],
        check=False,
        capture_output=True,
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-vf", "fps=2,scale=1280:-2", "-pix_fmt", "yuv420p", str(mp4_path),
        ],
        check=False,
        capture_output=True,
    )
    return (
        str(gif_path) if gif_path.exists() else None,
        str(mp4_path) if mp4_path.exists() else None,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", default=str(ASSETS))
    parser.add_argument("--record-video", action="store_true")
    args = parser.parse_args()
    out_dir = Path(args.assets)
    out_dir.mkdir(parents=True, exist_ok=True)
    video_dir = Path("reports/hle_ui_video")
    if args.record_video:
        video_dir.mkdir(parents=True, exist_ok=True)

    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        kwargs = {
            "viewport": {"width": 1280, "height": 800},
            "geolocation": {"longitude": -122.4194, "latitude": 37.7749},
            "permissions": ["geolocation"],
        }
        if args.record_video:
            kwargs["record_video_dir"] = str(video_dir)
            kwargs["record_video_size"] = {"width": 1280, "height": 800}
        context = browser.new_context(**kwargs)
        page = context.new_page()
        onboard(page)
        page.screenshot(path=str(out_dir / "exam-ui-hle-access-gate.png"), full_page=True)
        page.locator("#gamesBtn").click()
        page.wait_for_timeout(600)
        page.screenshot(path=str(out_dir / "exam-ui-hle-games-catalog.png"), full_page=True)

        for key, (label, question, mode) in GAMES.items():
            open_game(page, label)
            page.screenshot(path=str(out_dir / f"exam-ui-hle-{key}.png"), full_page=True)
            changed = False
            if mode == "ingest" or (mode == "chat_or_ingest" and not page.locator("#textInput").is_enabled()):
                if page.locator("#formalStatement").count():
                    page.locator("#formalStatement").fill(question)
                if page.locator("#formalIngestBtn").count():
                    page.locator("#formalIngestBtn").click()
                    page.wait_for_timeout(4000)
                    changed = True
            else:
                changed = ask_chat(page, question)
            page.screenshot(path=str(out_dir / f"exam-ui-hle-{key}-answer.png"), full_page=True)
            results.append(
                {
                    "game": key,
                    "ok": True,
                    "mode": mode,
                    "answer_state_changed": changed,
                    "before": str(out_dir / f"exam-ui-hle-{key}.png"),
                    "after": str(out_dir / f"exam-ui-hle-{key}-answer.png"),
                }
            )
        context.close()
        browser.close()

    gif_path, mp4_path = maybe_make_media(out_dir)
    receipt = {
        "kind": "hle_exam_ui_capture",
        "recorded_at_unix": int(time.time()),
        "official_claim_permitted": False,
        "doctrine_refs": [
            "docs/LANGUAGE_GAMES_HLE.md",
            "docs/LANGUAGE_GAMES_EXAM_INVARIANTS.md",
        ],
        "results": results,
        "gif": gif_path,
        "mp4": mp4_path,
        "notes": [
            "UI interaction evidence only.",
            "Not CAIS judge output and not Accuracy/Calibration.",
        ],
    }
    Path("reports/hle_ui_capture_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, indent=2))
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
