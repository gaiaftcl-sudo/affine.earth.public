from typing import List
from ..core.types import LLMTestSample

# Real-world domain benchmark test suites comparing external LLMs on Affine.Earth tasks
AFFINE_EARTH_DOMAIN_SUITE: List[LLMTestSample] = [
    LLMTestSample(
        sample_id="affine_domain_01_rational_arithmetic",
        domain="code",
        prompt="Write a Python class `Rational` with `num` and `den` (Int64) that avoids all floating point arithmetic and implements addition via cross-multiplication: a/b + c/d = (a*d + c*b)/(b*d).",
        canonical_solution="class Rational:\n    def __init__(self, num, den):\n        self.num = num\n        self.den = den",
        test_cases=[
            "r1 = Rational(1, 2)",
            "r2 = Rational(1, 3)",
            "assert r1.num * 3 + r2.num * 2 == 5",
        ],
    ),
    LLMTestSample(
        sample_id="affine_domain_02_constant_time_xor",
        domain="code",
        prompt="Write a Python function `constant_time_compare(a: bytes, b: bytes) -> bool` that compares two 32-byte byte strings using a full XOR accumulator without early exits.",
        canonical_solution="def constant_time_compare(a, b):\n    if len(a) != len(b): return False\n    acc = 0\n    for x, y in zip(a, b):\n        acc |= (x ^ y)\n    return acc == 0",
        test_cases=[
            "assert constant_time_compare(b'A'*32, b'A'*32) == True",
            "assert constant_time_compare(b'A'*32, b'B'*32) == False",
        ],
    ),
    LLMTestSample(
        sample_id="affine_domain_03_energy_tariff",
        domain="reasoning",
        prompt="In Affine.Earth OS, energy margin tariff is defined as Lambda = (torsion * license_constant * 1_000_000_000) / margin. Calculate Lambda when torsion=5, license_constant=2, and margin=10.",
        canonical_solution="1000000000",
    ),
]

CODE_SUITE: List[LLMTestSample] = [
    LLMTestSample(
        sample_id="code_01_fibonacci",
        domain="code",
        prompt="Write a Python function `fibonacci(n)` that returns the n-th Fibonacci number.",
        canonical_solution="def fibonacci(n):\n    if n <= 1: return n\n    return fibonacci(n-1) + fibonacci(n-2)",
        test_cases=[
            "assert fibonacci(0) == 0",
            "assert fibonacci(1) == 1",
            "assert fibonacci(5) == 5",
            "assert fibonacci(10) == 55",
        ],
    ),
    LLMTestSample(
        sample_id="code_02_is_prime",
        domain="code",
        prompt="Write a Python function `is_prime(n)` that returns True if n is a prime number, else False.",
        canonical_solution="def is_prime(n):\n    if n < 2: return False\n    for i in range(2, int(n**0.5)+1):\n        if n % i == 0: return False\n    return True",
        test_cases=[
            "assert is_prime(1) == False",
            "assert is_prime(2) == True",
            "assert is_prime(17) == True",
            "assert is_prime(20) == False",
        ],
    ),
]

REASONING_SUITE: List[LLMTestSample] = [
    LLMTestSample(
        sample_id="reasoning_01_math",
        domain="reasoning",
        prompt="If a store sells 5 apples for $10, and you buy 15 apples with a 10% discount, how much do you pay? Show step-by-step math.",
        canonical_solution="27",
    ),
]

LIST_OF_SUITES = {
    "affine_domain": AFFINE_EARTH_DOMAIN_SUITE,
    "code": CODE_SUITE,
    "reasoning": REASONING_SUITE,
}

def get_suite(suite_name: str) -> List[LLMTestSample]:
    normalized = suite_name.lower()
    if normalized not in LIST_OF_SUITES:
        available = ", ".join(sorted(LIST_OF_SUITES))
        raise ValueError(f"Unknown suite '{suite_name}'. Available suites: {available}.")
    return LIST_OF_SUITES[normalized]
