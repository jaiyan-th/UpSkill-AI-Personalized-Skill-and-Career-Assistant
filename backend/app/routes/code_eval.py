"""
Code Evaluation API Routes
Evaluates coding answers with test cases and provides feedback
"""

from flask import Blueprint, request, jsonify
from app.auth_utils import require_auth
from app.services.code_evaluator import CodeEvaluator

code_eval_bp = Blueprint('code_eval', __name__, url_prefix='/api/code')
code_evaluator = CodeEvaluator()

@code_eval_bp.route('/evaluate', methods=['POST'])
@require_auth
def evaluate_code(current_user):
    """
    Evaluate code submission
    
    Request:
        {
            "code": "def solution(n): return n * 2",
            "language": "python",
            "problem_description": "Write a function that doubles a number",
            "test_cases": [
                {"input": 5, "expected": 10},
                {"input": 0, "expected": 0}
            ]
        }
    
    Response:
        {
            "success": true,
            "evaluation": {
                "correctness_score": 100,
                "efficiency_score": 85,
                "code_quality_score": 90,
                "overall_score": 95,
                "test_results": [...],
                "feedback": "...",
                "strengths": [...],
                "improvements": [...]
            }
        }
    """
    try:
        data = request.json or {}
        
        code = data.get('code')
        language = data.get('language', 'python')
        problem = data.get('problem_description', '')
        test_cases = data.get('test_cases', [])
        
        if not code:
            return jsonify({
                "success": False,
                "error": "code is required"
            }), 400
        
        evaluation = code_evaluator.evaluate_code(
            code=code,
            language=language,
            problem_description=problem,
            test_cases=test_cases
        )
        
        return jsonify({
            "success": True,
            "evaluation": evaluation
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@code_eval_bp.route('/generate-tests', methods=['POST'])
@require_auth
def generate_tests(current_user):
    """
    Generate test cases for a coding problem
    
    Request:
        {
            "problem_description": "Write a function that...",
            "language": "python"
        }
    
    Response:
        {
            "success": true,
            "test_cases": [
                {
                    "input": ...,
                    "expected": ...,
                    "description": "...",
                    "type": "basic/edge/stress"
                }
            ]
        }
    """
    try:
        data = request.json or {}
        
        problem = data.get('problem_description')
        language = data.get('language', 'python')
        
        if not problem:
            return jsonify({
                "success": False,
                "error": "problem_description is required"
            }), 400
        
        test_cases = code_evaluator.generate_test_cases(problem, language)
        
        return jsonify({
            "success": True,
            "test_cases": test_cases,
            "count": len(test_cases)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@code_eval_bp.route('/check-plagiarism', methods=['POST'])
@require_auth
def check_plagiarism(current_user):
    """
    Check code for plagiarism indicators
    
    Request:
        {
            "code": "...",
            "language": "python"
        }
    
    Response:
        {
            "success": true,
            "plagiarism": {
                "suspicion_level": "low/medium/high",
                "confidence": 15,
                "indicators": [...],
                "recommendation": "..."
            }
        }
    """
    try:
        data = request.json or {}
        
        code = data.get('code')
        language = data.get('language', 'python')
        
        if not code:
            return jsonify({
                "success": False,
                "error": "code is required"
            }), 400
        
        result = code_evaluator.detect_plagiarism(code, language)
        
        return jsonify({
            "success": True,
            "plagiarism": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
