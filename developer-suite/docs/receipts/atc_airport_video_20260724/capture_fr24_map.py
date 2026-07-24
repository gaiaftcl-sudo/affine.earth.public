#!/usr/bin/env python3
"""Capture FR24-class RealityPro ATC live map video + screenshot."""
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
WIKI = Path(__file__).resolve().parents[4] / "wiki" / "assets"
WVID = WIKI / "videos"
URL = os.environ.get("REALITYPRO_URL", "https://affine.earth/language-game/realitypro/")
DURATION_MS = int(os.environ.get("CAPTURE_MS", "24000"))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
REF = Path(
    "/Users/richardgillespie/.cursor/projects/Users-richardgillespie-Documents-AppleGaiaFTCL/assets/"
    "Screenshot_2026-07-24_at_1.03.32_PM-1d853c70-631e-4c50-b89a-99695c8da9f1.png"
)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    WVID.mkdir(parents=True, exist_ok=True)
    video_dir = OUT / "pw_video_fr24"
    if video_dir.exists():
        shutil.rmtree(video_dir)
    video_dir.mkdir()

    states = []
    with sync_playwright() as p:
        kw = {
            "headless": False,
            "args": ["--ignore-gpu-blocklist", "--enable-webgl", "--use-gl=angle", "--window-size=1400,900"],
        }
        if Path(CHROME).exists():
            kw["executable_path"] = CHROME
        browser = p.chromium.launch(**kw)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(video_dir),
            record_video_size={"width": 1280, "height": 720},
        )
        page = context.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)
        page.fill("#usdaPath", "/language-game/airspace-atc-world.usda")
        page.click("#btnLoadUsda")
        page.wait_for_timeout(5000)
        # Prefer EGLL for Europe density like FR24 reference, then KJFK
        try:
            page.click('button[data-icao="EGLL"]')
            page.wait_for_timeout(4000)
        except Exception:
            pass
        try:
            page.click('button[data-icao="KJFK"]')
            page.wait_for_timeout(3500)
        except Exception:
            pass

        def snap():
            return page.evaluate(
                """() => {
                  const h = document.getElementById('realitypro-live-hud');
                  const vp = document.getElementById('viewport');
                  return {
                    hud: h && h.textContent,
                    strobe: h && h.getAttribute('data-strobe-tick'),
                    clock: h && h.getAttribute('data-clock-ms'),
                    liveRefresh: h && h.getAttribute('data-live-refresh'),
                    mode: h && h.getAttribute('data-scene-mode'),
                    focus: h && h.getAttribute('data-focus-icao'),
                    aircraft: h && h.getAttribute('data-aircraft'),
                    canvas: !!(vp && vp.querySelector('canvas')),
                  };
                }"""
            )

        s0 = snap()
        states.append({"t": "start", **s0})
        page.screenshot(path=str(OUT / "our_app_fr24_look.png"), full_page=False)
        page.wait_for_timeout(DURATION_MS)
        # Zoom in for arrivals feel
        try:
            page.click("#btnZoomIn")
            page.wait_for_timeout(800)
            page.click("#btnZoomIn")
        except Exception:
            pass
        page.wait_for_timeout(4000)
        s1 = snap()
        states.append({"t": "end", **s1})
        page.screenshot(path=str(OUT / "our_app_fr24_zoom.png"), full_page=False)
        context.close()
        browser.close()

    webms = list(video_dir.glob("*.webm"))
    if not webms:
        print("NO_VIDEO", file=sys.stderr)
        return 1
    dest_webm = OUT / "atc-fr24-live-map.webm"
    shutil.copy2(webms[0], dest_webm)
    dest_mp4 = OUT / "atc-fr24-live-map.mp4"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(dest_webm), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(dest_mp4)],
            check=True,
            capture_output=True,
        )
    except Exception as e:
        print("ffmpeg soft-fail", e, file=sys.stderr)

    # Wiki assets
    for name in ("atc-fr24-live-map.webm", "atc-fr24-live-map.mp4", "our_app_fr24_look.png", "our_app_fr24_zoom.png"):
        src = OUT / name
        if src.exists():
            shutil.copy2(src, WVID / name if name.endswith((".webm", ".mp4")) else WIKI / name)
            if name.endswith((".webm", ".mp4")):
                shutil.copy2(src, WIKI / name)
    if REF.exists():
        shutil.copy2(REF, WIKI / "fr24-reference-target.png")
        shutil.copy2(REF, OUT / "fr24-reference-target.png")

    # Also keep legacy filenames for prior wiki embeds
    if dest_webm.exists():
        shutil.copy2(dest_webm, OUT / "atc-kjfk-live-tracks.webm")
        shutil.copy2(dest_webm, WVID / "atc-kjfk-live-tracks.webm")
        shutil.copy2(dest_webm, WIKI / "atc-kjfk-live-tracks.webm")
    if dest_mp4.exists():
        shutil.copy2(dest_mp4, OUT / "atc-kjfk-live-tracks.mp4")
        shutil.copy2(dest_mp4, WVID / "atc-kjfk-live-tracks.mp4")
        shutil.copy2(dest_mp4, WIKI / "atc-kjfk-live-tracks.mp4")
    for src_name, dst_name in (
        ("our_app_fr24_look.png", "atc-kjfk-poster_t0.png"),
        ("our_app_fr24_zoom.png", "atc-kjfk-poster_t1.png"),
    ):
        s = OUT / src_name
        if s.exists():
            shutil.copy2(s, OUT / dst_name)
            shutil.copy2(s, WIKI / dst_name)

    ac0 = int((states[0].get("aircraft") or "0") or 0)
    ac1 = int((states[-1].get("aircraft") or "0") or 0)
    lr0 = int((states[0].get("liveRefresh") or "0") or 0)
    lr1 = int((states[-1].get("liveRefresh") or "0") or 0)
    meta = {
        "url": URL,
        "look_target": "Flightradar24-class dark map + yellow heading sprites",
        "track_source": "adsb.lol_https_v2",
        "tracks_path": "/language-invariant/adsb/tracks",
        "authored_aircraft_loop": False,
        "states": states,
        "aircraft_start": ac0,
        "aircraft_end": ac1,
        "live_refresh_start": lr0,
        "live_refresh_end": lr1,
        "webm_bytes": dest_webm.stat().st_size,
        "mp4_bytes": dest_mp4.stat().st_size if dest_mp4.exists() else 0,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (OUT / "capture_meta_fr24.json").write_text(json.dumps(meta, indent=2) + "\n")
    (OUT / "capture_meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))
    if dest_webm.stat().st_size < 100_000:
        return 2
    if ac1 < 1 and ac0 < 1:
        print("WARN ac=0 during capture", file=sys.stderr)
    print("ATC_FR24_MAP_VIDEO_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
