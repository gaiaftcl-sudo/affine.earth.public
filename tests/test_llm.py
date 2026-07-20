import pytest
from llm_llvm_bench.core.types import LLMModelConfig, LLMTestSample
from llm_llvm_bench.llm.providers import OpenAICompatibleProvider, get_provider
from llm_llvm_bench.llm.evaluator import LLMEvaluator
from llm_llvm_bench.llm.runner import LLMRunner
from llm_llvm_bench.llm.suites import get_suite

def test_evaluator_code():
    code = "def fibonacci(n):\n    if n <= 1: return n\n    return fibonacci(n-1) + fibonacci(n-2)"
    tests = ["assert fibonacci(5) == 5", "assert fibonacci(10) == 55"]
    assert LLMEvaluator.evaluate_code(code, tests) == True

    failing_tests = ["assert fibonacci(5) == 999"]
    assert LLMEvaluator.evaluate_code(code, failing_tests) == False

def test_evaluator_constant_time_compare():
    code = "def constant_time_compare(a, b):\n    if len(a) != len(b): return False\n    acc = 0\n    for x, y in zip(a, b):\n        acc |= (x ^ y)\n    return acc == 0"
    tests = [
        "assert constant_time_compare(b'A'*32, b'A'*32) == True",
        "assert constant_time_compare(b'A'*32, b'B'*32) == False",
    ]
    assert LLMEvaluator.evaluate_code(code, tests) == True

def test_get_suite():
    suite = get_suite("affine_domain")
    assert len(suite) >= 3
    assert suite[0].domain == "code"
