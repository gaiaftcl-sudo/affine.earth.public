import os
import json
import pytest
from llm_llvm_bench.core.types import (
    LLMModelConfig, LLMResult, LLMSuiteResult, BenchmarkReport
)
from llm_llvm_bench.core.metrics import calculate_pass_at_k, compute_llvm_metrics
from llm_llvm_bench.core.reporter import Reporter

def test_pass_at_k():
    # When n=10, c=10, k=1 -> pass@1 should be 1.0
    assert calculate_pass_at_k(10, 10, 1) == 1.0
    # When n=10, c=0, k=1 -> pass@1 should be 0.0
    assert calculate_pass_at_k(10, 0, 1) == 0.0

def test_compute_llvm_metrics():
    results = [
        {"compile_time_sec": 0.1, "execution_time_sec": 0.05, "text_section_size_bytes": 1000},
        {"compile_time_sec": 0.2, "execution_time_sec": 0.05, "text_section_size_bytes": 2000},
    ]
    metrics = compute_llvm_metrics(results)
    assert abs(metrics["avg_compile_time_sec"] - 0.15) < 1e-4
    assert abs(metrics["avg_exec_time_sec"] - 0.05) < 1e-4
    assert metrics["total_text_size_bytes"] == 3000

def test_reporter_json_and_markdown(tmp_path):
    report = BenchmarkReport(report_id="test_report_123")
    suite = LLMSuiteResult(
        suite_name="code",
        model_name="mock_gpt",
        total_samples=2,
        passed_samples=2,
        accuracy_pct=100.0,
        avg_latency_sec=0.01,
        tokens_per_sec=100.0,
    )
    report.llm_suites.append(suite)

    json_path = tmp_path / "report.json"
    md_path = tmp_path / "report.md"

    Reporter.save_json(report, str(json_path))
    Reporter.save_markdown(report, str(md_path))

    assert json_path.exists()
    assert md_path.exists()

    with open(json_path) as f:
        data = json.load(f)
        assert data["report_id"] == "test_report_123"
