#!/usr/bin/env python3
"""Fetch live OpenUSD airspace lattice — no usdview / no OS binary."""
from _common import client, show
from affine_earth_sdk import OpenUSDClient

with client() as c:
    usd = OpenUSDClient(c)
    print("airspace.html OK:", usd.airspace_html_ok())
    summary = usd.summary()
    show("airspace-lattice.usda summary", summary)
    try:
        show("observer-demo", usd.observer_demo())
    except Exception as exc:
        print("observer-demo:", type(exc).__name__, exc)
