import math
from typing import List, Dict, Any

def calculate_pass_at_k(n: int, c: int, k: int) -> float:
    """
    Calculates pass@k metric based on HumanEval paper formula:
    pass@k = 1 - (binom(n-c, k) / binom(n, k))
    """
    if n - c < k:
        return 1.0
    return 1.0 - (math.comb(n - c, k) / math.comb(n, k))

def compute_llvm_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates LLVM performance metrics:
    - Average execution wall time
    - Code size reduction compared to baseline (-O0)
    - Instruction breakdown ratios
    """
    if not results:
        return {"avg_compile_time": 0.0, "avg_exec_time": 0.0, "total_code_size": 0}

    total_compile_time = sum(r.get("compile_time_sec", 0.0) for r in results)
    exec_times = [r.get("execution_time_sec", 0.0) for r in results if r.get("execution_time_sec") is not None]
    total_code_size = sum(r.get("text_section_size_bytes", 0) for r in results)

    avg_compile_time = total_compile_time / len(results)
    avg_exec_time = (sum(exec_times) / len(exec_times)) if exec_times else 0.0

    return {
        "avg_compile_time_sec": avg_compile_time,
        "avg_exec_time_sec": avg_exec_time,
        "total_text_size_bytes": total_code_size,
    }
