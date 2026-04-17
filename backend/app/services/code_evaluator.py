"""
Code Evaluation Service
Evaluates coding answers with test cases and provides detailed feedback
"""

import re
import sys
import io
import traceback
from typing import Dict, List, Any
from .llm_service import LLMService

class CodeEvaluator:
    def __init__(self):
        self.llm = LLMService()
        self.supported_languages = ['python', 'javascript', 'java', 'cpp']
    
    def evaluate_code(
        self, 
        code: str, 
        language: str,
        problem_description: str,
        test_cases: List[Dict] = None
    ) -> Dict:
        """
        Evaluate code submission
        
        Args:
            code: Code submitted by candidate
            language: Programming language
            problem_description: Problem statement
            test_cases: [{"input": ..., "expected": ...}, ...]
        
        Returns:
            {
                "correctness_score": 0-100,
                "efficiency_score": 0-100,
                "code_quality_score": 0-100,
                "overall_score": 0-100,
                "test_results": [...],
                "feedback": "...",
                "strengths": [...],
                "improvements": [...],
                "time_complexity": "O(n)",
                "space_complexity": "O(1)"
            }
        """
        
        if language.lower() not in self.supported_languages:
            return {
                "error": f"Language {language} not supported",
                "supported": self.supported_languages
            }
        
        # Run test cases if provided
        test_results = []
        if test_cases and language.lower() == 'python':
            test_results = self._run_python_tests(code, test_cases)
        
        # AI-based code review
        code_review = self._ai_code_review(code, language, problem_description, test_results)
        
        # Calculate scores
        correctness_score = self._calculate_correctness(test_results) if test_results else code_review.get('correctness_score', 70)
        efficiency_score = code_review.get('efficiency_score', 70)
        quality_score = code_review.get('code_quality_score', 70)
        
        overall_score = int(
            correctness_score * 0.5 +
            efficiency_score * 0.25 +
            quality_score * 0.25
        )
        
        return {
            "correctness_score": correctness_score,
            "efficiency_score": efficiency_score,
            "code_quality_score": quality_score,
            "overall_score": overall_score,
            "test_results": test_results,
            "tests_passed": sum(1 for t in test_results if t.get('passed', False)),
            "tests_total": len(test_results),
            "feedback": code_review.get('feedback', ''),
            "strengths": code_review.get('strengths', []),
            "improvements": code_review.get('improvements', []),
            "time_complexity": code_review.get('time_complexity', 'Unknown'),
            "space_complexity": code_review.get('space_complexity', 'Unknown'),
            "best_practices": code_review.get('best_practices', []),
            "security_issues": code_review.get('security_issues', [])
        }
    
    def _run_python_tests(self, code: str, test_cases: List[Dict]) -> List[Dict]:
        """
        Run Python code against test cases in isolated environment
        
        Returns:
            [{"input": ..., "expected": ..., "actual": ..., "passed": bool, "error": ...}, ...]
        """
        results = []
        
        for i, test in enumerate(test_cases):
            test_input = test.get('input')
            expected = test.get('expected')
            
            try:
                # Create isolated namespace
                namespace = {}
                
                # Capture stdout
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                
                # Execute code
                exec(code, namespace)
                
                # Get output
                output = sys.stdout.getvalue()
                sys.stdout = old_stdout
                
                # Try to find main function or result
                actual = None
                if 'solution' in namespace:
                    actual = namespace['solution'](test_input)
                elif 'main' in namespace:
                    actual = namespace['main'](test_input)
                elif output:
                    actual = output.strip()
                
                # Compare results
                passed = str(actual).strip() == str(expected).strip()
                
                results.append({
                    "test_number": i + 1,
                    "input": test_input,
                    "expected": expected,
                    "actual": actual,
                    "passed": passed,
                    "error": None
                })
                
            except Exception as e:
                sys.stdout = old_stdout
                results.append({
                    "test_number": i + 1,
                    "input": test_input,
                    "expected": expected,
                    "actual": None,
                    "passed": False,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
        
        return results
    
    def _calculate_correctness(self, test_results: List[Dict]) -> int:
        """Calculate correctness score from test results"""
        if not test_results:
            return 0
        
        passed = sum(1 for t in test_results if t.get('passed', False))
        total = len(test_results)
        
        return int((passed / total) * 100)
    
    def _ai_code_review(
        self, 
        code: str, 
        language: str,
        problem: str,
        test_results: List[Dict]
    ) -> Dict:
        """
        AI-powered code review
        
        Returns:
            {
                "correctness_score": 0-100,
                "efficiency_score": 0-100,
                "code_quality_score": 0-100,
                "feedback": "...",
                "strengths": [...],
                "improvements": [...],
                "time_complexity": "O(n)",
                "space_complexity": "O(1)",
                "best_practices": [...],
                "security_issues": [...]
            }
        """
        
        system_prompt = f"""You are an expert {language} code reviewer and computer science educator.
Provide detailed, constructive feedback on code submissions.
Always return valid JSON format."""

        test_summary = ""
        if test_results:
            passed = sum(1 for t in test_results if t.get('passed', False))
            total = len(test_results)
            test_summary = f"\n\nTest Results: {passed}/{total} tests passed"
            if passed < total:
                failed = [t for t in test_results if not t.get('passed', False)]
                test_summary += f"\nFailed tests: {failed[:2]}"  # Show first 2 failures

        prompt = f"""Review this {language} code submission:

Problem: {problem}

Code:
```{language}
{code}
```
{test_summary}

Provide comprehensive review as JSON:
{{
  "correctness_score": 0-100 (does it solve the problem correctly?),
  "efficiency_score": 0-100 (time and space complexity),
  "code_quality_score": 0-100 (readability, style, best practices),
  
  "feedback": "2-3 paragraph detailed review",
  
  "strengths": [
    "specific strength 1",
    "specific strength 2"
  ],
  
  "improvements": [
    "specific improvement 1 with example",
    "specific improvement 2 with example"
  ],
  
  "time_complexity": "O(n) or O(n^2) etc.",
  "space_complexity": "O(1) or O(n) etc.",
  "complexity_explanation": "Brief explanation of complexity",
  
  "best_practices": [
    "best practice followed or violated"
  ],
  
  "security_issues": [
    "security concern if any"
  ],
  
  "alternative_approach": "Suggest a better approach if applicable",
  
  "learning_resources": [
    "topic to study for improvement"
  ]
}}

Be specific, constructive, and educational.
Return ONLY valid JSON, no other text."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.4,
            json_mode=True,
            max_tokens=2000
        )
        
        return self.llm.parse_json_response(response)
    
    def generate_test_cases(self, problem_description: str, language: str) -> List[Dict]:
        """
        Generate test cases for a coding problem
        
        Returns:
            [{"input": ..., "expected": ..., "description": "..."}, ...]
        """
        
        system_prompt = """You are an expert at creating comprehensive test cases for coding problems.
Generate diverse test cases including edge cases."""

        prompt = f"""Generate test cases for this {language} coding problem:

{problem_description}

Provide JSON array of test cases:
[
  {{
    "input": "test input",
    "expected": "expected output",
    "description": "what this test checks",
    "type": "basic/edge/stress"
  }},
  ...
]

Include:
- 2-3 basic test cases
- 2-3 edge cases (empty, null, boundary values)
- 1-2 stress tests (large inputs)

Return ONLY valid JSON array, no other text."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5,
            json_mode=True
        )
        
        try:
            test_cases = self.llm.parse_json_response(response)
            return test_cases if isinstance(test_cases, list) else []
        except:
            return []
    
    def detect_plagiarism(self, code: str, language: str) -> Dict:
        """
        Detect potential plagiarism or copied code
        
        Returns:
            {
                "suspicion_level": "low/medium/high",
                "indicators": [...],
                "confidence": 0-100
            }
        """
        
        indicators = []
        suspicion_score = 0
        
        # Check for common plagiarism indicators
        
        # 1. Unusual comments (like "TODO: remove before submission")
        suspicious_comments = [
            'stackoverflow', 'copied from', 'source:', 'credit:',
            'borrowed from', 'taken from', 'found at'
        ]
        for comment in suspicious_comments:
            if comment in code.lower():
                indicators.append(f"Suspicious comment containing '{comment}'")
                suspicion_score += 20
        
        # 2. Inconsistent coding style
        has_camelCase = bool(re.search(r'[a-z][A-Z]', code))
        has_snake_case = bool(re.search(r'[a-z]_[a-z]', code))
        if has_camelCase and has_snake_case:
            indicators.append("Inconsistent naming convention (mixed camelCase and snake_case)")
            suspicion_score += 15
        
        # 3. Overly complex for level
        lines = [l for l in code.split('\n') if l.strip() and not l.strip().startswith('#')]
        if len(lines) > 100:
            indicators.append("Unusually long solution")
            suspicion_score += 10
        
        # 4. Advanced patterns for junior level
        advanced_patterns = ['lambda', 'decorator', 'metaclass', 'generator', '__']
        advanced_count = sum(1 for pattern in advanced_patterns if pattern in code.lower())
        if advanced_count > 3:
            indicators.append("Uses many advanced patterns")
            suspicion_score += 15
        
        # Determine suspicion level
        if suspicion_score >= 40:
            level = "high"
        elif suspicion_score >= 20:
            level = "medium"
        else:
            level = "low"
        
        return {
            "suspicion_level": level,
            "confidence": min(100, suspicion_score),
            "indicators": indicators if indicators else ["No plagiarism indicators detected"],
            "recommendation": "Manual review recommended" if level == "high" else "Appears original"
        }
