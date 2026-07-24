#!/usr/bin/env python3
"""POST /language-invariant/inject — conformal SCF inject (no elephant media required)."""
from _common import client, show
from affine_earth_sdk import LanguageGamesClient

with client() as c:
    lg = LanguageGamesClient(c)
    out = lg.inject("developer-suite-a", "developer-suite-b")
    show("inject", out)
