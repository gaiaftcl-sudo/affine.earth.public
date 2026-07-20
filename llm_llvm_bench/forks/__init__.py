"""
Forked Standard Benchmark Adapters Module.
Integrates standard HumanEval / MBPP and LLVM Test-Suite frameworks.
"""

from .humaneval_adapter import HumanEvalAdapter, HUMANEVAL_PUBLISHED_BASELINES
from .llvm_testsuite_adapter import LLVMTestSuiteAdapter, LLVM_TEST_SUITE_PUBLISHED_BASELINES

__all__ = [
    "HumanEvalAdapter",
    "HUMANEVAL_PUBLISHED_BASELINES",
    "LLVMTestSuiteAdapter",
    "LLVM_TEST_SUITE_PUBLISHED_BASELINES",
]
