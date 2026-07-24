#!/usr/bin/env python3
"""UMC domains cinema / aviation / gaming — Director Long Play surface."""
from _common import client, show
from affine_earth_sdk import UMCClient
from affine_earth_sdk.umc import UMC_DOMAINS

with client() as c:
    umc = UMCClient(c)
    for domain in UMC_DOMAINS:
        if domain == "coding":
            continue
        out = umc.direct(
            domain,
            session_id=f"devsuite-{domain}",
            title=f"developer-suite-{domain}",
            max_turns=8,
        )
        show(f"umc.direct {domain}", out)
