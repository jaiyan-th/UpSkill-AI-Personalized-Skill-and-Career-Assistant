"""
Voice Analysis API Routes
Analyzes speech patterns, fluency, and communication quality
"""

from flask import Blueprint, request, jsonify
from app.auth_utils import require_auth
from app.services.voice_analyzer import VoiceAnalyzer

voice_bp = Blueprint('voice', __name__, url_prefix='/api/voice')
voice_analyzer = VoiceAnalyzer()

@voice_bp.route('/analyze', methods=['POST'])
@require_auth
def analyze_speech(current_user):
    """
    Analyze speech from transcript
    
    Request:
        {
            "transcript": "Um, so I think the answer is...",
            "duration_seconds": 45.5
        }
    
    Response:
        {
            "success": true,
            "analysis": {
                "fluency_score": 75,
                "confidence_score": 68,
                "clarity_score": 82,
                "overall_communication_score": 75,
                "words_per_minute": 145,
                "filler_word_count": 3,
                "feedback": "...",
                "strengths": [...],
                "improvements": [...]
            }
        }
    """
    try:
        data = request.json or {}
        
        transcript = data.get('transcript', '')
        duration = data.get('duration_seconds')
        
        if not transcript:
            return jsonify({
                "success": False,
                "error": "transcript is required"
            }), 400
        
        analysis = voice_analyzer.analyze_speech(transcript, duration)
        
        return jsonify({
            "success": True,
            "analysis": analysis
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@voice_bp.route('/compare', methods=['POST'])
@require_auth
def compare_answers(current_user):
    """
    Compare multiple answers to show improvement trends
    
    Request:
        {
            "answers": [
                {"transcript": "...", "duration": 30},
                {"transcript": "...", "duration": 45}
            ]
        }
    
    Response:
        {
            "success": true,
            "comparison": {
                "answer_count": 2,
                "fluency_trend": [65, 75],
                "confidence_trend": [60, 72],
                "improvement": {...},
                "trend_direction": {...}
            }
        }
    """
    try:
        data = request.json or {}
        answers = data.get('answers', [])
        
        if len(answers) < 2:
            return jsonify({
                "success": False,
                "error": "At least 2 answers required for comparison"
            }), 400
        
        comparison = voice_analyzer.compare_answers(answers)
        
        return jsonify({
            "success": True,
            "comparison": comparison
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@voice_bp.route('/batch-analyze', methods=['POST'])
@require_auth
def batch_analyze(current_user):
    """
    Analyze multiple transcripts at once
    
    Request:
        {
            "transcripts": [
                {"text": "...", "duration": 30, "question_id": 1},
                {"text": "...", "duration": 45, "question_id": 2}
            ]
        }
    
    Response:
        {
            "success": true,
            "analyses": [
                {"question_id": 1, "analysis": {...}},
                {"question_id": 2, "analysis": {...}}
            ],
            "summary": {
                "average_fluency": 72,
                "average_confidence": 68,
                "overall_communication": 70
            }
        }
    """
    try:
        data = request.json or {}
        transcripts = data.get('transcripts', [])
        
        if not transcripts:
            return jsonify({
                "success": False,
                "error": "transcripts array is required"
            }), 400
        
        analyses = []
        fluency_scores = []
        confidence_scores = []
        clarity_scores = []
        
        for item in transcripts:
            text = item.get('text', '')
            duration = item.get('duration')
            question_id = item.get('question_id')
            
            analysis = voice_analyzer.analyze_speech(text, duration)
            
            analyses.append({
                "question_id": question_id,
                "analysis": analysis
            })
            
            fluency_scores.append(analysis['fluency_score'])
            confidence_scores.append(analysis['confidence_score'])
            clarity_scores.append(analysis['clarity_score'])
        
        summary = {
            "average_fluency": round(sum(fluency_scores) / len(fluency_scores), 1) if fluency_scores else 0,
            "average_confidence": round(sum(confidence_scores) / len(confidence_scores), 1) if confidence_scores else 0,
            "average_clarity": round(sum(clarity_scores) / len(clarity_scores), 1) if clarity_scores else 0,
            "total_analyzed": len(analyses)
        }
        
        summary["overall_communication"] = round(
            (summary["average_fluency"] + summary["average_confidence"] + summary["average_clarity"]) / 3, 1
        )
        
        return jsonify({
            "success": True,
            "analyses": analyses,
            "summary": summary
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
