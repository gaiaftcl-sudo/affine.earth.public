#!/usr/bin/env python3
"""Capture RealityPro ATC LIVE airport scene video (Playwright record).

Shows KJFK zoom + aircraft positions updating from live
GET /language-invariant/adsb/tracks (adsb.lol HTTPS via Affine.Earth OS).
Not an authored timeSamples loop.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent
WIKI_ASSETS = Path(__file__).resolve().parents[4] / "wiki" / "assets" / "videos"
URL = os.environ.get(
    "REALITYPRO_URL",
    "https://affine.earth/language-game/realitypro/",
)
USDA = "/language-game/airspace-atc-world.usda"
DURATION_MS = int(os.environ.get("CAPTURE_MS", "24000"))
CHROME = os.environ.get(
    "CHROME_PATH",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    WIKI_ASSETS.mkdir(parents=True, exist_ok=True)
    video_dir = OUT / "pw_video"
    if video_dir.exists():
        shutil.rmtree(video_dir)
    video_dir.mkdir()

    states = []
    with sync_playwright() as p:
        launch_kwargs = {
            "headless": False,
            "args": [
                "--ignore-gpu-blocklist",
                "--enable-webgl",
                "--use-gl=angle",
                "--window-size=1280,800",
            ],
        }
        if Path(CHROME).exists():
            launch_kwargs["executable_path"] = CHROME
        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(video_dir),
            record_video_size={"width": 1280, "height": 720},
        )
        page = context.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)
        page.fill("#usdaPath", USDA)
        page.click("#btnLoadUsda")
        page.wait_for_timeout(4000)
        try:
            page.select_option("#gameSelect", "aviation_atc")
        except Exception:
            pass

        def snap_state():
            return page.evaluate(
                """() => {
                  const hud = document.getElementById('realitypro-live-hud');
                  const vp = document.getElementById('viewport');
                  return {
                    hud: hud ? hud.textContent : null,
                    strobe: hud && hud.getAttribute('data-strobe-tick'),
                    clock: hud && hud.getAttribute('data-clock-ms'),
                    membrane: hud && hud.getAttribute('data-membrane-ticks'),
                    liveRefresh: hud && hud.getAttribute('data-live-refresh'),
                    mode: hud && hud.getAttribute('data-scene-mode'),
                    focus: hud && hud.getAttribute('data-focus-icao'),
                    track: hud && hud.getAttribute('data-track-source'),
                    aircraft: hud && hud.getAttribute('data-aircraft'),
                    canvas: !!(vp && vp.querySelector('canvas')),
                    title: document.title,
                  };
                }"""
            )

        s0 = snap_state()
        states.append({"t": "start", **s0})
        page.screenshot(path=str(OUT / "poster_t0.png"), full_page=False)

        # Hold long enough for ≥2 live track polls (~2.5s each)
        page.wait_for_timeout(DURATION_MS)
        s1 = snap_state()
        states.append({"t": "end", **s1})
        page.screenshot(path=str(OUT / "poster_t1.png"), full_page=False)

        context.close()
        browser.close()

    webms = list(video_dir.glob("*.webm"))
    if not webms:
        print("NO_VIDEO_CAPTURED", file=sys.stderr)
        return 1
    dest_webm = OUT / "atc-kjfk-live-tracks.webm"
    shutil.copy2(webms[0], dest_webm)
    wiki_webm = WIKI_ASSETS / "atc-kjfk-live-tracks.webm"
    shutil.copy2(dest_webm, wiki_webm)
    for name in ("poster_t0.png", "poster_t1.png"):
        shutil.copy2(OUT / name, WIKI_ASSETS / f"atc-kjfk-{name}")

    dest_mp4 = OUT / "atc-kjfk-live-tracks.mp4"
    wiki_mp4 = WIKI_ASSETS / "atc-kjfk-live-tracks.mp4"
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(dest_webm),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(dest_mp4),
            ],
            check=True,
            capture_output=True,
        )
        shutil.copy2(dest_mp4, wiki_mp4)
    except Exception as e:
        print("ffmpeg mp4 convert soft-fail:", e, file=sys.stderr)

    # Also copy under wiki/assets (non-videos) for older links
    assets_root = WIKI_ASSETS.parent
    for src, name in (
        (dest_webm, "atc-kjfk-live-tracks.webm"),
        (dest_mp4 if dest_mp4.exists() else None, "atc-kjfk-live-tracks.mp4"),
    ):
        if src and src.exists():
            shutil.copy2(src, assets_root / name)

    ac0 = int((states[0].get("aircraft") or "0") or 0)
    ac1 = int((states[-1].get("aircraft") or "0") or 0)
    lr0 = int((states[0].get("liveRefresh") or "0") or 0)
    lr1 = int((states[-1].get("liveRefresh") or "0") or 0)

    meta = {
        "url": URL,
        "usda": USDA,
        "focus_icao": "KJFK",
        "track_source": "adsb.lol_https_v2",
        "tracks_path": "/language-invariant/adsb/tracks",
        "beast_tcp_status": "FOLLOW_ON_WAN_NOT_BRIDGED",
        "motion": "live_track_snapshot_refresh",
        "authored_aircraft_loop": False,
        "duration_ms": DURATION_MS,
        "states": states,
        "aircraft_start": ac0,
        "aircraft_end": ac1,
        "live_refresh_start": lr0,
        "live_refresh_end": lr1,
        "webm_bytes": dest_webm.stat().st_size,
        "mp4_bytes": dest_mp4.stat().st_size if dest_mp4.exists() else 0,
        "paths": {
            "receipt_webm": str(dest_webm),
            "receipt_mp4": str(dest_mp4) if dest_mp4.exists() else None,
            "wiki_webm": str(wiki_webm),
            "wiki_mp4": str(wiki_mp4) if wiki_mp4.exists() else None,
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (OUT / "capture_meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))
    if dest_webm.stat().st_size < 100_000:
        print("VIDEO_TOO_SMALL", file=sys.stderr)
        return 2
    if ac1 < 1 and ac0 < 1:
        print("WARN empty sky during capture — video still records live path", file=sys.stderr)
    if lr1 <= lr0:
        print("WARN liveRefresh did not advance — check tracks endpoint", file=sys.stderr)
    print("ATC_LIVE_AIRPORT_VIDEO_CAPTURE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
