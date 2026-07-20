import pytest
from llm_llvm_bench.forks import HumanEvalAdapter, LLVMTestSuiteAdapter

def test_humaneval_adapter():
    adapter = HumanEvalAdapter()
    report = adapter.run_evaluation()
    assert report["harness"] == "HumanEval / MBPP Forked Adapter"
    assert len(report["scorecard"]) > 0

def test_llvm_testsuite_adapter():
    adapter = LLVMTestSuiteAdapter()
    report = adapter.get_published_report()
    assert report["harness"] == "LLVM Test-Suite SingleSource Adapter"
    assert "Clang 18.1 (-O3 NEON AArch64)" in report["compilers"]
