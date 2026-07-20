import pytest
from llm_llvm_bench.core.types import LLVMCompilerConfig
from llm_llvm_bench.llvm.driver import LLVMDriver
from llm_llvm_bench.llvm.runner import LLVMRunner
from llm_llvm_bench.llvm.benchmarks import MICROBENCH_C

def test_llvm_driver():
    cfg = LLVMCompilerConfig(name="clang-test", compiler_path="clang", opt_level="-O2")
    driver = LLVMDriver(cfg)
    success, compile_time, exec_time, text_size, total_size, ir_counts, err = (
        driver.compile_and_benchmark(MICROBENCH_C.source_code, MICROBENCH_C.language)
    )
    assert success == True
    assert compile_time > 0.0
    assert exec_time is not None
    assert text_size > 0
    assert total_size > 0

def test_llvm_runner():
    cfg = LLVMCompilerConfig(name="clang-o3", compiler_path="clang", opt_level="-O3")
    runner = LLVMRunner(cfg)
    res = runner.run_suite("microbench", [MICROBENCH_C])
    assert res.total_samples == 1
    assert res.compiled_samples == 1
    assert res.avg_compile_time_sec > 0.0
