import os
import subprocess
import tempfile
import time
from typing import Dict, Tuple, Optional
from ..core.types import LLVMCompilerConfig

class LLVMDriver:
    def __init__(self, config: LLVMCompilerConfig):
        self.config = config

    def compile_and_benchmark(
        self, source_code: str, language: str = "c"
    ) -> Tuple[bool, float, Optional[float], int, int, Dict[str, int], Optional[str]]:
        """
        Compiles source code with Clang/LLVM, measures compile time, binary text section size, and execution time.
        Returns: (success, compile_time, exec_time, text_size, total_size, ir_counts, error_msg)
        """
        ext = ".cpp" if language.lower() in ["cpp", "c++"] else ".c"
        compiler = "clang++" if language.lower() in ["cpp", "c++"] else self.config.compiler_path

        with tempfile.TemporaryDirectory() as tmpdir:
            src_file = os.path.join(tmpdir, f"sample{ext}")
            bin_file = os.path.join(tmpdir, "sample.out")
            ir_file = os.path.join(tmpdir, "sample.ll")

            with open(src_file, "w", encoding="utf-8") as f:
                f.write(source_code)

            # 1. Compile to executable & measure compilation time
            cmd = [
                compiler,
                self.config.opt_level,
                src_file,
                "-o",
                bin_file,
            ] + self.config.custom_flags

            start_compile = time.time()
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
                compile_time = time.time() - start_compile
            except Exception as e:
                compile_time = time.time() - start_compile
                err_text = getattr(e, "stderr", str(e))
                return False, compile_time, None, 0, 0, {}, err_text

            # 2. Measure binary & text section size
            total_size = os.path.getsize(bin_file) if os.path.exists(bin_file) else 0
            text_size = self._measure_text_size(bin_file, total_size)

            # 3. Generate LLVM IR for instruction analysis
            ir_counts = self._analyze_llvm_ir(compiler, src_file, ir_file)

            # 4. Execute binary & measure wall time
            exec_time = self._execute_binary(bin_file)

            return True, compile_time, exec_time, text_size, total_size, ir_counts, None

    def _measure_text_size(self, bin_file: str, total_size: int) -> int:
        # Try size tool (macOS/Linux)
        try:
            res = subprocess.run(["size", bin_file], capture_output=True, text=True)
            if res.returncode == 0:
                lines = res.stdout.strip().splitlines()
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if parts and parts[0].isdigit():
                        return int(parts[0])
        except Exception:
            pass
        return int(total_size * 0.7)  # Approximation fallback

    def _analyze_llvm_ir(self, compiler: str, src_file: str, ir_file: str) -> Dict[str, int]:
        counts = {"loads": 0, "stores": 0, "calls": 0, "vector_ops": 0, "branches": 0}
        cmd = [compiler, self.config.opt_level, "-S", "-emit-llvm", src_file, "-o", ir_file]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            if os.path.exists(ir_file):
                with open(ir_file, "r", encoding="utf-8") as f:
                    ir_text = f.read()
                counts["loads"] = ir_text.count("load ")
                counts["stores"] = ir_text.count("store ")
                counts["calls"] = ir_text.count("call ")
                counts["branches"] = ir_text.count("br ")
                counts["vector_ops"] = ir_text.count("<") + ir_text.count("vector")
        except Exception:
            pass
        return counts

    def _execute_binary(self, bin_file: str) -> Optional[float]:
        try:
            start = time.time()
            res = subprocess.run([bin_file], capture_output=True, text=True, timeout=10)
            exec_time = time.time() - start
            if res.returncode == 0:
                return exec_time
        except Exception:
            pass
        return None
