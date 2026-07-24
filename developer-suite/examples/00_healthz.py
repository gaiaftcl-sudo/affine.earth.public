#!/usr/bin/env python3
"""GET /language-invariant/healthz — membrane liveness."""
from _common import client, show

with client() as c:
    show("healthz", c.healthz())
