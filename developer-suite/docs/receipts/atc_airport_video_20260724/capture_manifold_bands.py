#!/usr/bin/env python3
"""Prove UUM8D manifold zoom bands: hemisphere → regional → metro → airport walk.

Wheel zoom across all bands; assert band transitions; screenshot each band;
record interaction video. Live ADS-B only (no mocks).
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
WIKI = Path(__file__).resolve().parents[4] / "wiki" / "assets"
WVID = WIKI / "videos"
URL = os.environ.get("OPENUSD_URL", "https://affine.earth/language-game/openusd/")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

BAND_ORDER = ["HEMISPHERE", "REGIONAL", "METRO", "AIRPORT_WALK"]


def snap(page):
    return page.evaluate(
        """() => {
          const h = document.getElementById('openusd-live-hud');
          const vp = document.getElementById('viewport');
          const title = document.title || '';
          const body = (document.body && document.body.innerText) || '';
          return {
            title,
            hud: h && h.textContent,
            strobe: h && h.getAttribute('data-strobe-tick'),
            liveRefresh: h && h.getAttribute('data-live-refresh'),
            mode: h && h.getAttribute('data-scene-mode'),
            focus: h && h.getAttribute('data-focus-icao'),
            aircraft: h && h.getAttribute('data-aircraft'),
            lodTracks: h && h.getAttribute('data-lod-tracks'),
            zoom: h && h.getAttribute('data-zoom'),
            zoomRational: h && h.getAttribute('data-zoom-rational'),
            band: h && h.getAttribute('data-manifold-band') || (vp && vp.getAttribute('data-manifold-band')),
            walk: h && h.getAttribute('data-walk-mode'),
            canvas: !!(vp && vp.querySelector('canvas')),
            banned: /reality\\s*pro/i.test(title + body),
            skinHref: (document.getElementById('mapSkin') || {}).href || '',
          };
        }"""
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    WVID.mkdir(parents=True, exist_ok=True)
    video_dir = OUT / "pw_video_manifold"
    if video_dir.exists():
        shutil.rmtree(video_dir)
    video_dir.mkdir()

    states = []
    bands_seen = []

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
        page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(2500)
        page.fill("#usdaPath", "/language-game/airspace-atc-world.usda")
        page.click("#btnLoadUsda")
        page.wait_for_timeout(5000)

        canvas = page.locator("#viewport canvas")
        box = canvas.bounding_box()
        if not box:
            print("NO_CANVAS", file=sys.stderr)
            context.close()
            browser.close()
            return 1
        cx = box["x"] + box["width"] * 0.55
        cy = box["y"] + box["height"] * 0.45

        def record(tag: str):
            s = snap(page)
            s["t"] = tag
            states.append(s)
            b = s.get("band") or "?"
            if b not in bands_seen:
                bands_seen.append(b)
            page.screenshot(path=str(OUT / f"manifold_band_{b.lower()}.png"), full_page=False)
            page.screenshot(path=str(OUT / f"manifold_{tag}.png"), full_page=False)
            return s

        s0 = record("boot")
        # Expect hemisphere at boot
        page.mouse.move(cx, cy)

        # Drive zoom through all bands via wheel (in) then assert sequence
        last_band = s0.get("band")
        for i in range(28):
            page.mouse.wheel(0, -140)
            page.wait_for_timeout(180)
            s = snap(page)
            b = s.get("band")
            if b and b != last_band:
                record(f"enter_{b.lower()}")
                last_band = b
            if b == "AIRPORT_WALK":
                break

        # Pan in airport walk
        page.mouse.move(cx, cy)
        page.mouse.down()
        page.mouse.move(cx - 160, cy + 80, steps=20)
        page.mouse.up()
        page.wait_for_timeout(500)
        record("airport_walk_pan")

        # Zoom back out toward hemisphere
        for i in range(24):
            page.mouse.wheel(0, 160)
            page.wait_for_timeout(150)
            s = snap(page)
            if (s.get("band") or "") == "HEMISPHERE":
                record("return_hemisphere")
                break

        # Explicit hemisphere + airport buttons
        try:
            page.click("#btnZoomHemi")
            page.wait_for_timeout(800)
            record("btn_hemisphere")
        except Exception:
            pass
        try:
            page.click("#btnZoomAirport")
            page.wait_for_timeout(1200)
            record("btn_airport_walk")
        except Exception:
            pass

        page.wait_for_timeout(2000)
        record("end")

        context.close()
        browser.close()

    webms = list(video_dir.glob("*.webm"))
    if not webms:
        print("NO_VIDEO", file=sys.stderr)
        return 1
    dest_webm = OUT / "openusd-manifold-bands.webm"
    shutil.copy2(webms[0], dest_webm)
    dest_mp4 = OUT / "openusd-manifold-bands.mp4"
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

    for name in list(OUT.glob("manifold_*.png")) + [
        dest_webm,
        dest_mp4,
    ]:
        if not Path(name).exists():
            continue
        src = Path(name)
        if src.suffix in (".webm", ".mp4"):
            shutil.copy2(src, WVID / src.name)
            shutil.copy2(src, WIKI / src.name)
        else:
            shutil.copy2(src, WIKI / src.name)

    banned = any(bool(s.get("banned")) for s in states)
    boot_band = (states[0].get("band") if states else "") or ""
    end_bands = {s.get("band") for s in states if s.get("band")}
    transitions = []
    prev = None
    for s in states:
        b = s.get("band")
        if b and b != prev:
            transitions.append({"t": s.get("t"), "band": b, "zoom": s.get("zoom")})
            prev = b

    meta = {
        "url": URL,
        "brand": "Affine.Earth OpenUSD",
        "product_physics": "UUM8D manifold staging bands (not CSS bitmap scale)",
        "band_order_expected": BAND_ORDER,
        "bands_seen": bands_seen,
        "transitions": transitions,
        "boot_band": boot_band,
        "boot_is_hemisphere": boot_band == "HEMISPHERE",
        "all_four_bands_seen": all(b in end_bands for b in BAND_ORDER),
        "airport_walk_seen": "AIRPORT_WALK" in end_bands,
        "realitypro_banned_text_found": banned,
        "states": states,
        "webm_bytes": dest_webm.stat().st_size,
        "mp4_bytes": dest_mp4.stat().st_size if dest_mp4.exists() else 0,
        "skins": {
            "HEMISPHERE": "assets/skins/map-hemisphere.css",
            "REGIONAL": "assets/skins/map-regional.css",
            "METRO": "assets/skins/map-metro.css",
            "AIRPORT_WALK": "assets/skins/map-airport.css",
        },
        "thresholds": {
            "HEMISPHERE": "[0, 0.42)",
            "REGIONAL": "[0.42, 1.15)",
            "METRO": "[1.15, 3.60)",
            "AIRPORT_WALK": "[3.60, 14]",
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (OUT / "capture_meta_manifold.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps({k: meta[k] for k in meta if k != "states"}, indent=2))
    if banned:
        print("FAIL: RealityPro text in UI", file=sys.stderr)
        return 3
    if not meta["boot_is_hemisphere"]:
        print("FAIL: boot band is not HEMISPHERE:", boot_band, file=sys.stderr)
        return 4
    if not meta["all_four_bands_seen"]:
        print("FAIL: missing bands:", sorted(BAND_ORDER - end_bands) if False else sorted(set(BAND_ORDER) - end_bands), file=sys.stderr)
        return 5
    if dest_webm.stat().st_size < 40_000:
        return 2
    print("OPENUSD_MANIFOLD_BANDS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
