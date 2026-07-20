import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class LLMModelConfig:
    name: str
    provider: str  # "openai", "anthropic", "gemini", "ollama", "mock"
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.0
    max_tokens: int = 2048

@dataclass
class LLMTestSample:
    sample_id: str
    domain: str  # "code", "reasoning", "tool_use", "long_context", "safety"
    prompt: str
    canonical_solution: Optional[str] = None
    test_cases: List[str] = field(default_factory=list)
    system_prompt: Optional[str] = None

@dataclass
class LLMResult:
    sample_id: str
    domain: str
    model_name: str
    prompt: str
    generated_text: str
    passed: bool
    latency_sec: float
    prompt_tokens: int
    completion_tokens: int
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LLMSuiteResult:
    suite_name: str
    model_name: str
    total_samples: int
    passed_samples: int
    accuracy_pct: float
    avg_latency_sec: float
    tokens_per_sec: float
    results: List[LLMResult] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

@dataclass
class LLVMCompilerConfig:
    name: str
    compiler_path: str = "clang"
    opt_level: str = "-O3"  # -O0, -O1, -O2, -O3, -Os, -Oz
    target_arch: str = "aarch64"  # aarch64, x86_64
    custom_flags: List[str] = field(default_factory=list)

@dataclass
class LLVMTestSample:
    sample_id: str
    domain: str  # "microbench", "codesize", "ir_analysis", "pass_timing"
    source_code: str
    language: str = "c"  # c, cpp
    expected_output: Optional[str] = None

@dataclass
class LLVMResult:
    sample_id: str
    domain: str
    compiler_name: str
    opt_level: str
    compile_success: bool
    compile_time_sec: float
    execution_time_sec: Optional[float]
    text_section_size_bytes: int
    total_binary_size_bytes: int
    ir_instruction_count: Dict[str, int] = field(default_factory=dict)
    error_message: Optional[str] = None

@dataclass
class LLVMSuiteResult:
    suite_name: str
    compiler_name: str
    opt_level: str
    total_samples: int
    compiled_samples: int
    avg_compile_time_sec: float
    avg_execution_time_sec: float
    total_text_size_bytes: int
    results: List[LLVMResult] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

@dataclass
class BenchmarkReport:
    report_id: str
    created_at: float = field(default_factory=time.time)
    llm_suites: List[LLMSuiteResult] = field(default_factory=list)
    llvm_suites: List[LLVMSuiteResult] = field(default_factory=list)
