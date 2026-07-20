import time
from typing import List
from ..core.types import LLVMCompilerConfig, LLVMResult, LLVMSuiteResult, LLVMTestSample
from .driver import LLVMDriver

class LLVMRunner:
    def __init__(self, compiler_config: LLVMCompilerConfig):
        self.config = compiler_config
        self.driver = LLVMDriver(compiler_config)

    def run_suite(self, suite_name: str, samples: List[LLVMTestSample]) -> LLVMSuiteResult:
        results: List[LLVMResult] = []
        compiled_count = 0
        total_compile_time = 0.0
        total_exec_time = 0.0
        exec_count = 0
        total_text_bytes = 0

        for sample in samples:
            success, compile_time, exec_time, text_size, total_size, ir_counts, err_msg = (
                self.driver.compile_and_benchmark(sample.source_code, sample.language)
            )

            total_compile_time += compile_time
            if success:
                compiled_count += 1
                total_text_bytes += text_size

            if exec_time is not None:
                total_exec_time += exec_time
                exec_count += 1

            results.append(
                LLVMResult(
                    sample_id=sample.sample_id,
                    domain=sample.domain,
                    compiler_name=self.config.name,
                    opt_level=self.config.opt_level,
                    compile_success=success,
                    compile_time_sec=compile_time,
                    execution_time_sec=exec_time,
                    text_section_size_bytes=text_size,
                    total_binary_size_bytes=total_size,
                    ir_instruction_count=ir_counts,
                    error_message=err_msg,
                )
            )

        total_samples = len(samples)
        avg_compile_time = (total_compile_time / total_samples) if total_samples > 0 else 0.0
        avg_exec_time = (total_exec_time / exec_count) if exec_count > 0 else 0.0

        return LLVMSuiteResult(
            suite_name=suite_name,
            compiler_name=self.config.name,
            opt_level=self.config.opt_level,
            total_samples=total_samples,
            compiled_samples=compiled_count,
            avg_compile_time_sec=avg_compile_time,
            avg_execution_time_sec=avg_exec_time,
            total_text_size_bytes=total_text_bytes,
            results=results,
        )
