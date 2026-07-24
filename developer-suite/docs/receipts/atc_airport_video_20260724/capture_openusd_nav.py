#!/usr/bin/env python3
"""Prove Affine.Earth OpenUSD map nav: wheel zoom + drag pan + screenshot/video."""
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
URL = os.environ.get("OPENUSD_URL", "https://affine.earth/language-game/openusd/")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    WVID.mkdir(parents=True, exist_ok=True)
    video_dir = OUT / "pw_video_nav"
    if video_dir.exists():
        shutil.rmtree(video_dir)
    video_dir.mkdir()

    states = []
    with sync_playwright() as p:
        kw = {
            "headless": False,
            "args": [
                "--ignore-gpu-blocklist",
                "--enable-webgl",
                "--use-gl=angle",
                "--window-size=1400,900",
            ],
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
        page.wait_for_timeout(2000)
        # Ensure ATC scene
        page.fill("#usdaPath", "/language-game/airspace-atc-world.usda")
        page.click("#btnLoadUsda")
        page.wait_for_timeout(4500)
        try:
            page.click('button[data-icao="KJFK"]')
            page.wait_for_timeout(3000)
        except Exception:
            pass

        def snap():
            return page.evaluate(
                """() => {
                  const h = document.getElementById('openusd-live-hud');
                  const vp = document.getElementById('viewport');
                  const title = document.title || '';
                  return {
                    title,
                    hud: h && h.textContent,
                    strobe: h && h.getAttribute('data-strobe-tick'),
                    liveRefresh: h && h.getAttribute('data-live-refresh'),
                    mode: h && h.getAttribute('data-scene-mode'),
                    focus: h && h.getAttribute('data-focus-icao'),
                    aircraft: h && h.getAttribute('data-aircraft'),
                    zoom: h && h.getAttribute('data-zoom'),
                    canvas: !!(vp && vp.querySelector('canvas')),
                    banned: /reality\\s*pro/i.test(title + (document.body && document.body.innerText || '')),
                  };
                }"""
            )

        s0 = snap()
        states.append({"t": "boot", **s0})
        page.screenshot(path=str(OUT / "openusd_nav_boot.png"), full_page=False)

        canvas = page.locator("#viewport canvas")
        box = canvas.bounding_box()
        if not box:
            print("NO_CANVAS", file=sys.stderr)
            context.close()
            browser.close()
            return 1
        cx = box["x"] + box["width"] * 0.55
        cy = box["y"] + box["height"] * 0.45

        # Wheel zoom toward cursor (simulate trackpad/mouse)
        page.mouse.move(cx, cy)
        for _ in range(6):
            page.mouse.wheel(0, -120)
            page.wait_for_timeout(120)
        page.wait_for_timeout(600)
        s1 = snap()
        states.append({"t": "wheel_zoom_in", **s1})
        page.screenshot(path=str(OUT / "openusd_nav_zoom.png"), full_page=False)

        # Ctrl+wheel pinch-style zoom out a bit
        page.keyboard.down("Control")
        for _ in range(3):
            page.mouse.wheel(0, 100)
            page.wait_for_timeout(100)
        page.keyboard.up("Control")
        page.wait_for_timeout(400)

        # Click-drag pan
        page.mouse.move(cx, cy)
        page.mouse.down()
        page.mouse.move(cx - 140, cy + 60, steps=18)
        page.mouse.up()
        page.wait_for_timeout(500)
        s2 = snap()
        states.append({"t": "pan", **s2})
        page.screenshot(path=str(OUT / "openusd_nav_pan.png"), full_page=False)

        # Double-click zoom in
        page.mouse.dblclick(cx, cy)
        page.wait_for_timeout(700)
        s3 = snap()
        states.append({"t": "dblclick_zoom", **s3})
        page.screenshot(path=str(OUT / "openusd_nav_dblclick.png"), full_page=False)

        page.wait_for_timeout(2500)
        s4 = snap()
        states.append({"t": "end", **s4})

        context.close()
        browser.close()

    webms = list(video_dir.glob("*.webm"))
    if not webms:
        print("NO_VIDEO", file=sys.stderr)
        return 1
    dest_webm = OUT / "openusd-nav-interaction.webm"
    shutil.copy2(webms[0], dest_webm)
    dest_mp4 = OUT / "openusd-nav-interaction.mp4"
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(dest_webm),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-an",
                str(dest_mp4),
            ],
            check=True,
            capture_output=True,
        )
    except Exception as e:
        print("ffmpeg soft-fail", e, file=sys.stderr)

    for name in (
        "openusd-nav-interaction.webm",
        "openusd-nav-interaction.mp4",
        "openusd_nav_boot.png",
        "openusd_nav_zoom.png",
        "openusd_nav_pan.png",
        "openusd_nav_dblclick.png",
    ):
        src = OUT / name
        if not src.exists():
            continue
        if name.endswith((".webm", ".mp4")):
            shutil.copy2(src, WVID / name)
            shutil.copy2(src, WIKI / name)
        else:
            shutil.copy2(src, WIKI / name)

    z0 = float((states[0].get("zoom") or "1") or 1)
    z1 = float((states[1].get("zoom") or "1") or 1)
    z3 = float((states[3].get("zoom") or z1) or z1)
    ac = max(int((s.get("aircraft") or "0") or 0) for s in states)
    banned = any(bool(s.get("banned")) for s in states)
    meta = {
        "url": URL,
        "brand": "Affine.Earth OpenUSD",
        "states": states,
        "zoom_boot": z0,
        "zoom_after_wheel": z1,
        "zoom_after_dblclick": z3,
        "zoom_increased": z1 > z0 + 0.05,
        "aircraft_max": ac,
        "realitypro_banned_text_found": banned,
        "webm_bytes": dest_webm.stat().st_size,
        "mp4_bytes": dest_mp4.stat().st_size if dest_mp4.exists() else 0,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (OUT / "capture_meta_nav.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))
    if banned:
        print("FAIL: RealityPro text in UI", file=sys.stderr)
        return 3
    if not meta["zoom_increased"]:
        print("FAIL: wheel zoom did not increase zoom attr", file=sys.stderr)
        return 4
    if dest_webm.stat().st_size < 40_000:
        return 2
    print("OPENUSD_NAV_INTERACTION_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
