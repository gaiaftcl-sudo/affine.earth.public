"""Measure local compiler and exact-integer checks, optionally probing a live URL."""

import argparse
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

import requests


SOURCE = r"""
#include <stdint.h>
#include <stdio.h>
uint64_t constant_time_compare(const uint8_t *a, const uint8_t *b, size_t len) {
    uint8_t acc = 0;
    for (size_t i = 0; i < len; i++) acc |= (a[i] ^ b[i]);
    return acc == 0;
}
int main(void) {
    uint8_t a[32] = {0xAA}, b[32] = {0xAA};
    printf("PASS=%llu\n", (unsigned long long)constant_time_compare(a, b, 32));
    return 0;
}
"""


def measure_clang(compiler: str) -> dict:
    results = {}
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "constant_time.c"
        source.write_text(SOURCE, encoding="utf-8")
        for opt in ("-O0", "-O2", "-O3", "-Os"):
            binary = Path(directory) / f"constant_time_{opt[1:]}"
            started = time.perf_counter_ns()
            subprocess.run(
                [compiler, opt, str(source), "-o", str(binary)],
                check=True,
                capture_output=True,
                text=True,
            )
            compile_ns = time.perf_counter_ns() - started
            started = time.perf_counter_ns()
            program = subprocess.run(
                [str(binary)], check=True, capture_output=True, text=True
            )
            execution_ns = time.perf_counter_ns() - started
            size = subprocess.run(
                ["size", str(binary)], check=True, capture_output=True, text=True
            ).stdout.splitlines()
            text_bytes = int(size[1].split()[0]) if len(size) > 1 else None
            results[opt] = {
                "compile_ns": compile_ns,
                "execution_ns": execution_ns,
                "text_section_bytes": text_bytes,
                "program_output": program.stdout.strip(),
            }
    return results


def measure_exact_integer_arithmetic() -> dict:
    numerator, denominator = 1, 3
    started = time.perf_counter_ns()
    for _ in range(10_000):
        numerator = numerator * 7 + denominator
        denominator *= 7
    return {
        "iterations": 10_000,
        "elapsed_ns": time.perf_counter_ns() - started,
        "numerator_digits": len(str(numerator)),
        "denominator_digits": len(str(denominator)),
    }


def probe_live(url: str) -> dict:
    started = time.perf_counter_ns()
    response = requests.get(url, timeout=10)
    elapsed_ns = time.perf_counter_ns() - started
    response.raise_for_status()
    return {"url": url, "status_code": response.status_code, "elapsed_ns": elapsed_ns}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compiler", default=os.getenv("AFFINE_LLVM_COMPILER", "clang"))
    parser.add_argument("--live-url", help="Optional URL that must return a successful HTTP response.")
    parser.add_argument("--out", default="reports/real_verification_proof.json")
    args = parser.parse_args()

    report = {
        "provenance": "MEASURED",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "compiler": args.compiler,
        "clang": measure_clang(args.compiler),
        "exact_integer_arithmetic": measure_exact_integer_arithmetic(),
        "live_probe": probe_live(args.live_url) if args.live_url else None,
    }
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"MEASURED verification report: {output}")


if __name__ == "__main__":
    main()
