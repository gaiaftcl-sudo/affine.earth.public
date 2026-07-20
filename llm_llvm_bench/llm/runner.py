import time
from typing import List
from ..core.types import LLMModelConfig, LLMResult, LLMSuiteResult, LLMTestSample
from .providers import get_provider
from .evaluator import LLMEvaluator

class LLMRunner:
    def __init__(self, model_config: LLMModelConfig):
        self.config = model_config
        self.provider = get_provider(model_config)

    def run_suite(self, suite_name: str, samples: List[LLMTestSample]) -> LLMSuiteResult:
        results: List[LLMResult] = []
        passed_count = 0
        total_latency = 0.0
        total_completion_tokens = 0

        for sample in samples:
            text, latency, p_tokens, c_tokens = self.provider.generate(
                prompt=sample.prompt, system_prompt=sample.system_prompt
            )
            total_latency += latency
            total_completion_tokens += c_tokens

            # Evaluate sample based on domain
            if sample.domain == "code":
                passed = LLMEvaluator.evaluate_code(text, sample.test_cases)
            elif sample.domain == "reasoning":
                passed = LLMEvaluator.evaluate_reasoning(text, sample.canonical_solution)
            elif sample.domain == "tool_use":
                passed = LLMEvaluator.evaluate_tool_use(text, sample.canonical_solution)
            else:
                passed = len(text.strip()) > 0

            if passed:
                passed_count += 1

            results.append(
                LLMResult(
                    sample_id=sample.sample_id,
                    domain=sample.domain,
                    model_name=self.config.name,
                    prompt=sample.prompt,
                    generated_text=text,
                    passed=passed,
                    latency_sec=latency,
                    prompt_tokens=p_tokens,
                    completion_tokens=c_tokens,
                )
            )

        total_samples = len(samples)
        accuracy = (passed_count / total_samples * 100.0) if total_samples > 0 else 0.0
        avg_latency = (total_latency / total_samples) if total_samples > 0 else 0.0
        tokens_per_sec = (total_completion_tokens / total_latency) if total_latency > 0 else 0.0

        return LLMSuiteResult(
            suite_name=suite_name,
            model_name=self.config.name,
            total_samples=total_samples,
            passed_samples=passed_count,
            accuracy_pct=accuracy,
            avg_latency_sec=avg_latency,
            tokens_per_sec=tokens_per_sec,
            results=results,
        )
