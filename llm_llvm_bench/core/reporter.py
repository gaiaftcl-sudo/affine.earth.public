import json
import os
import time
from dataclasses import asdict
from typing import Dict, Any
from .types import BenchmarkReport

class Reporter:
    @staticmethod
    def to_json(report: BenchmarkReport) -> str:
        return json.dumps(asdict(report), indent=2)

    @staticmethod
    def save_json(report: BenchmarkReport, filepath: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(Reporter.to_json(report))

    @staticmethod
    def to_markdown(report: BenchmarkReport) -> str:
        lines = [
            f"# Benchmark Comparison Report: `{report.report_id}`",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.created_at))}",
            "",
        ]

        if report.llm_suites:
            lines.append("## AI LLM Real-World Domain Benchmarks")
            lines.append("| Model | Suite | Accuracy | Avg Latency | Tokens/sec | Passed / Total |")
            lines.append("|-------|-------|----------|-------------|------------|----------------|")
            for suite in report.llm_suites:
                lines.append(
                    f"| `{suite.model_name}` | `{suite.suite_name}` | {suite.accuracy_pct:.1f}% | "
                    f"{suite.avg_latency_sec:.3f}s | {suite.tokens_per_sec:.1f} t/s | "
                    f"{suite.passed_samples}/{suite.total_samples} |"
                )
            lines.append("")

        if report.llvm_suites:
            lines.append("## LLVM Compiler Infrastructure Benchmarks")
            lines.append("| Compiler | Opt Level | Suite | Avg Compile Time | Avg Exec Time | Text Size (Bytes) |")
            lines.append("|----------|-----------|-------|------------------|---------------|-------------------|")
            for suite in report.llvm_suites:
                lines.append(
                    f"| `{suite.compiler_name}` | `{suite.opt_level}` | `{suite.suite_name}` | "
                    f"{suite.avg_compile_time_sec:.4f}s | {suite.avg_execution_time_sec:.4f}s | "
                    f"{suite.total_text_size_bytes:,} B |"
                )
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def save_markdown(report: BenchmarkReport, filepath: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(Reporter.to_markdown(report))
