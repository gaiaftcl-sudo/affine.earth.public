import re
import json
from typing import List, Optional

class LLMEvaluator:
    @staticmethod
    def evaluate_code(generated_text: str, test_cases: List[str]) -> bool:
        """
        Executes Python unit test assertions against the generated code.
        """
        # Clean markdown code blocks if present
        clean_code = LLMEvaluator._extract_code_block(generated_text)

        global_scope = {}
        try:
            exec(clean_code, global_scope)
        except Exception as e:
            return False

        # Execute test cases
        for test in test_cases:
            try:
                exec(test, global_scope)
            except Exception:
                return False

        return True

    @staticmethod
    def evaluate_reasoning(generated_text: str, canonical_solution: Optional[str]) -> bool:
        if not canonical_solution:
            return len(generated_text.strip()) > 0

        # Extract final answer if present
        target = canonical_solution.strip().lower()
        output = generated_text.strip().lower()

        if target in output:
            return True

        # Extract numerical numbers
        numbers_target = re.findall(r'\d+', target)
        numbers_output = re.findall(r'\d+', output)

        if numbers_target and numbers_output:
            return numbers_target[-1] == numbers_output[-1]

        return False

    @staticmethod
    def evaluate_tool_use(generated_text: str, expected_schema: Optional[str]) -> bool:
        clean = LLMEvaluator._extract_json(generated_text)
        try:
            data = json.loads(clean)
            if expected_schema:
                schema = json.loads(expected_schema)
                for key in schema.get("required", []):
                    if key not in data:
                        return False
            return True
        except Exception:
            return False

    @staticmethod
    def _extract_code_block(text: str) -> str:
        match = re.search(r'```python\n(.*?)\n```', text, re.DOTALL)
        if match:
            return match.group(1)
        match = re.search(r'```\n(.*?)\n```', text, re.DOTALL)
        if match:
            return match.group(1)
        return text

    @staticmethod
    def _extract_json(text: str) -> str:
        match = re.search(r'```json\n(.*?)\n```', text, re.DOTALL)
        if match:
            return match.group(1)
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return match.group(0)
        return text
