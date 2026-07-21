"""Exam miss → reinject → closure loop (ARC-AGI-2/3, HLE)."""

from .miss_reinjection import (  # noqa: F401
    ARISTOTELIAN_CLOSURE_TURNS,
    load_fail_receipts,
    run_reinjection_cycle,
)
