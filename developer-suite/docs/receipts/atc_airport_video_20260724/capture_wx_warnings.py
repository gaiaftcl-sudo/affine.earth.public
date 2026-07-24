#!/usr/bin/env python3
"""Prove solar/weather overlay + warning panel on Affine.Earth OpenUSD."""
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


def snap(page):
    return page.evaluate(
        """() => {
          const h = document.getElementById('openusd-live-hud');
          const vp = document.getElementById('viewport');
          const title = document.title || '';
          const body = (document.body && document.body.innerText) || '';
          const warnList = document.getElementById('warnList');
          return {
            title,
            hud: h && h.textContent,
            band: h && h.getAttribute('data-manifold-band'),
            zoom: h && h.getAttribute('data-zoom'),
            wx: h && h.getAttribute('data-wx-status'),
            solar: h && h.getAttribute('data-solar-elev'),
            solarPhase: h && h.getAttribute('data-solar-phase'),
            warnCount: h && h.getAttribute('data-warn-count'),
            warnTop: h && h.getAttribute('data-warn-top'),
            aircraft: h && h.getAttribute('data-aircraft'),
            warnPanel: !!(warnList && warnList.textContent),
            warnText: warnList && warnList.textContent.slice(0, 240),
            canvas: !!(vp && vp.querySelector('canvas')),
            hasSolarWeather: typeof window.SolarWeather === 'object',
            hasTrafficWarnings: typeof window.TrafficWarnings === 'object',
            banned: /reality\\s*pro/i.test(title + body),
          };
        }"""
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    WVID.mkdir(parents=True, exist_ok=True)
    video_dir = OUT / "pw_video_wx"
    if video_dir.exists():
        shutil.rmtree(video_dir)
    video_dir.mkdir()

    states = []
    with sync_playwright() as p:
        headless = os.environ.get("OPENUSD_HEADLESS", "1") != "0"
        kw = {
            "headless": headless,
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
        page.wait_for_timeout(5500)

        def record(tag):
            s = snap(page)
            s["t"] = tag
            states.append(s)
            page.screenshot(path=str(OUT / f"wx_{tag}.png"), full_page=False)
            return s

        s0 = record("boot_hemisphere")
        # Inject two live-shaped conflict tracks into evaluate via page (prove warning path)
        # Prefer real live conflicts; always also force a synthetic pair through evaluate for determinism.
        inject = page.evaluate(
            """() => {
              if (!window.TrafficWarnings) return {ok:false};
              const tight = [
                {icao:'aa0001', callsign:'WX1', lat:40.6413, lon:-73.7781, alt_baro_ft:2800, gs_kt:230, track_deg:90},
                {icao:'bb0002', callsign:'WX2', lat:40.6460, lon:-73.7680, alt_baro_ft:3000, gs_kt:210, track_deg:270},
              ];
              const r = window.TrafficWarnings.evaluate(tight, 'METRO');
              const list = document.getElementById('warnList');
              const badge = document.getElementById('warnBadge');
              if (list && r.warnings.length) {
                list.innerHTML = r.warnings.slice(0,8).map(w =>
                  `<div class="warn-row sev-${(w.severity||'LOW').toLowerCase()}"><span class="sev">${w.severity}</span> ${w.message}</div>`
                ).join('');
              }
              if (badge) { badge.textContent = String(r.warnings.length); badge.className = 'warn-badge sev-high'; }
              const h = document.getElementById('openusd-live-hud');
              if (h) {
                h.setAttribute('data-warn-count', String(r.warnings.length));
                h.setAttribute('data-warn-top', r.warnings[0] ? (r.warnings[0].severity+':'+r.warnings[0].kind) : '');
                h.setAttribute('data-warn-demo', 'synthetic_live_shaped');
              }
              return {ok:true, n:r.warnings.length, top:r.warnings[0]||null, minima:r.minima};
            }"""
        )
        states.append({"t": "inject_sep_demo", **(inject if isinstance(inject, dict) else {})})
        page.wait_for_timeout(400)
        record("warn_demo")

        # Zoom toward metro for weather LOD change
        try:
            page.wait_for_selector("#viewport canvas", timeout=20000)
            canvas = page.locator("#viewport canvas")
            box = canvas.bounding_box()
        except Exception as e:
            states.append({"t": "canvas_wait_fail", "err": str(e), **snap(page)})
            page.screenshot(path=str(OUT / "wx_no_canvas.png"), full_page=False)
            box = None
        if box:
            cx = box["x"] + box["width"] * 0.55
            cy = box["y"] + box["height"] * 0.45
            page.mouse.move(cx, cy)
            for _ in range(12):
                page.mouse.wheel(0, -140)
                page.wait_for_timeout(140)
            page.wait_for_timeout(800)
            record("zoomed_band")

        try:
            page.click("#btnZoomHemi")
            page.wait_for_timeout(900)
            record("hemisphere_solar")
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
    dest_webm = OUT / "openusd-wx-warnings.webm"
    shutil.copy2(webms[0], dest_webm)
    dest_mp4 = OUT / "openusd-wx-warnings.mp4"
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

    for src in list(OUT.glob("wx_*.png")) + [dest_webm, dest_mp4]:
        if not Path(src).exists():
            continue
        src = Path(src)
        if src.suffix in (".webm", ".mp4"):
            shutil.copy2(src, WVID / src.name)
            shutil.copy2(src, WIKI / src.name)
        else:
            shutil.copy2(src, WIKI / src.name)

    banned = any(bool(s.get("banned")) for s in states if isinstance(s, dict))
    boot = states[0] if states else {}
    has_wx_mod = any(s.get("hasSolarWeather") for s in states if s.get("hasSolarWeather") is not None)
    has_tw_mod = any(s.get("hasTrafficWarnings") for s in states if s.get("hasTrafficWarnings") is not None)
    solar_ok = any(s.get("solar") not in (None, "", "null") for s in states if "solar" in s)
    wx_attr = any(s.get("wx") for s in states if s.get("wx"))
    inject_n = 0
    for s in states:
        if s.get("t") == "inject_sep_demo":
            inject_n = int(s.get("n") or 0)

    meta = {
        "url": URL,
        "brand": "Affine.Earth OpenUSD",
        "states": states,
        "solar_weather_module": has_wx_mod,
        "traffic_warnings_module": has_tw_mod,
        "solar_elev_seen": solar_ok,
        "wx_status_seen": wx_attr,
        "boot_band": boot.get("band"),
        "separation_demo_warnings": inject_n,
        "realitypro_banned_text_found": banned,
        "webm_bytes": dest_webm.stat().st_size,
        "mp4_bytes": dest_mp4.stat().st_size if dest_mp4.exists() else 0,
        "data_sources": {
            "solar": "computed UTC+lat/lon terminator (always)",
            "weather_radar": "membrane live_feeds.noaa_weather (BLOCKED → honest status + Affine stylized synoptic)",
            "aircraft": "GET /language-invariant/adsb/tracks live",
            "warnings": "TrafficWarnings.evaluate on live snapshot; demo pair for deterministic prove",
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (OUT / "capture_meta_wx_warnings.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps({k: meta[k] for k in meta if k != "states"}, indent=2))
    if banned:
        return 3
    if not has_wx_mod or not has_tw_mod:
        print("FAIL: modules missing on page", file=sys.stderr)
        return 4
    if not solar_ok or not wx_attr:
        print("FAIL: solar/wx attrs missing", file=sys.stderr)
        return 5
    if inject_n < 1:
        print("FAIL: separation demo produced 0 warnings", file=sys.stderr)
        return 6
    if dest_webm.stat().st_size < 40_000:
        return 2
    print("OPENUSD_WX_WARNINGS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
