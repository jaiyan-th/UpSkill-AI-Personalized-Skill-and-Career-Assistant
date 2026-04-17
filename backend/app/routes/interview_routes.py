"""
Interview Routes - API endpoints for interview insights and analytics
"""

from flask import Blueprint, request, jsonify
from app.database import get_db
from app.auth_utils import require_auth
import json

interview_bp = Blueprint("interview", __name__)


@interview_bp.get("/insights")
@require_auth
def get_interview_insights():
    """
    Get comprehensive interview insights and analytics
    
    Returns:
        {
            "interviews": [
                {
                    "id": 1,
                    "role": "Full Stack Developer",
                    "level": "Mid-level",
                    "date": "2026-04-07",
                    "overall_score": 85,
                    "questions_answered": 5,
                    "evaluation": {
                        "overall_score": 85,
                        "technical_accuracy": 8.5,
                        "communication_clarity": 8.0,
                        "fluency": 7.5,
                        "pronunciation": 8.5,
                        "confidence": 8.0,
                        "role_fit": 8.5,
                        "strengths": [...],
                        "weaknesses": [...],
                        "communication_feedback": "...",
                        "fluency_feedback": "...",
                        "pronunciation_feedback": "...",
                        "speech_metrics_summary": {
                            "average_wpm": 145,
                            "total_pauses": 8,
                            "total_filler_words": 5,
                            "average_clarity": 85
                        }
                    }
                }
            ]
        }
    """
    uid = request.user["id"]
    db = get_db()
    
    # Get all completed interviews for user
    interviews = db.execute(
        """SELECT id, role, level, overall_score, started_at, ended_at, evaluation_data
           FROM interview_sessions 
           WHERE user_id = ? AND status = 'completed'
           ORDER BY ended_at DESC
           LIMIT 10""",
        [uid]
    ).fetchall()
    
    interview_list = []
    for interview in interviews:
        evaluation_data = {}
        if interview["evaluation_data"]:
            try:
                evaluation_data = json.loads(interview["evaluation_data"])
            except:
                evaluation_data = {}
        
        # Get question count
        qa_count = db.execute(
            "SELECT COUNT(*) as count FROM interview_qa WHERE session_id = ?",
            [interview["id"]]
        ).fetchone()
        
        interview_list.append({
            "id": interview["id"],
            "role": interview["role"],
            "level": interview["level"],
            "date": interview["ended_at"] or interview["started_at"],
            "overall_score": interview["overall_score"] or 0,
            "questions_answered": qa_count["count"] if qa_count else 0,
            "evaluation": evaluation_data
        })
    
    return jsonify({
        "interviews": interview_list,
        "total_interviews": len(interview_list)
    })


@interview_bp.get("/insights/<int:interview_id>")
@require_auth
def get_single_interview_insight(interview_id):
    """
    Get detailed insights for a specific interview
    """
    uid = request.user["id"]
    db = get_db()
    
    # Get interview
    interview = db.execute(
        """SELECT * FROM interview_sessions 
           WHERE id = ? AND user_id = ?""",
        [interview_id, uid]
    ).fetchone()
    
    if not interview:
        return jsonify({"error": "Interview not found"}), 404
    
    # Get all Q&A pairs
    qa_pairs = db.execute(
        """SELECT question, answer, content_score, communication_score, 
                  fluency_score, pronunciation_score, speech_analysis
           FROM interview_qa 
           WHERE session_id = ?
           ORDER BY id""",
        [interview_id]
    ).fetchall()
    
    qa_list = []
    for qa in qa_pairs:
        speech_analysis = {}
        if qa["speech_analysis"]:
            try:
                speech_analysis = json.loads(qa["speech_analysis"])
            except:
                speech_analysis = {}
        
        qa_list.append({
            "question": qa["question"],
            "answer": qa["answer"],
            "content_score": qa["content_score"],
            "communication_score": qa["communication_score"],
            "fluency_score": qa["fluency_score"],
            "pronunciation_score": qa["pronunciation_score"],
            "speech_analysis": speech_analysis
        })
    
    # Get evaluation
    evaluation_data = {}
    if interview["evaluation_data"]:
        try:
            evaluation_data = json.loads(interview["evaluation_data"])
        except:
            evaluation_data = {}
    
    return jsonify({
        "interview": {
            "id": interview["id"],
            "role": interview["role"],
            "level": interview["level"],
            "status": interview["status"],
            "started_at": interview["started_at"],
            "ended_at": interview["ended_at"],
            "overall_score": interview["overall_score"],
            "evaluation": evaluation_data
        },
        "qa_pairs": qa_list
    })


@interview_bp.get("/history")
@require_auth
def get_interview_history():
    """
    Get interview history with basic stats
    """
    uid = request.user["id"]
    db = get_db()

    # Auto-complete any stuck in_progress sessions older than 1 hour
    db.execute(
        """UPDATE interview_sessions 
           SET status='completed', ended_at=datetime('now')
           WHERE user_id=? AND status='in_progress'
           AND started_at < datetime('now', '-1 hour')""",
        [uid]
    )
    db.commit()

    interviews = db.execute(
        """SELECT id, role, level, overall_score, started_at, ended_at, status
           FROM interview_sessions 
           WHERE user_id = ?
           ORDER BY started_at DESC""",
        [uid]
    ).fetchall()
    
    history = []
    total_score = 0
    completed_count = 0
    
    for interview in interviews:
        history.append({
            "id": interview["id"],
            "role": interview["role"],
            "level": interview["level"],
            "score": interview["overall_score"],
            "date": interview["ended_at"] or interview["started_at"],
            "status": interview["status"]
        })
        
        if interview["status"] == "completed" and interview["overall_score"]:
            total_score += interview["overall_score"]
            completed_count += 1
    
    average_score = total_score / completed_count if completed_count > 0 else 0
    
    return jsonify({
        "history": history,
        "stats": {
            "total_interviews": len(history),
            "completed_interviews": completed_count,
            "average_score": round(average_score, 1)
        }
    })
