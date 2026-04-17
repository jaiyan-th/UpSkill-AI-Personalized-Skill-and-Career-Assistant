"""
Workflow Routes - Complete User Journey API
Orchestrates: Resume → Skills → Interview → Gaps → Learning → Dashboard
"""

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app.services.workflow_orchestrator import WorkflowOrchestrator
from app.auth_utils import require_auth as token_required
from app.database import get_db
import json
import sqlite3

workflow_bp = Blueprint('workflow', __name__, url_prefix='/api/workflow')

orchestrator = WorkflowOrchestrator()

# Store active interview engines (in production, use Redis)
active_interviews = {}

# ==================== COMPLETE FLOW ====================

@workflow_bp.route('/start', methods=['POST'])
@token_required
def start_complete_flow():
    current_user = request.user
    """
    Start complete workflow: Upload resume and begin journey
    
    Request:
        - resume: PDF file
        - target_role: Target job role
        - job_description: Optional job description
    
    Response:
        {
            "resume_analysis": {...},
            "skill_graph": {...},
            "next_step": "interview"
        }
    """
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'Resume file required'}), 400
        
        file = request.files['resume']
        job_description = request.form.get('job_description', None)
        
        if not file.filename.endswith('.pdf'):
            return jsonify({'error': 'Only PDF files supported'}), 400
        
        user_id = current_user['id']
        
        # Process resume
        result = orchestrator.process_resume_upload(
            user_id=user_id,
            pdf_file=file,
            job_description=job_description
        )
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/interview/start', methods=['POST'])
@token_required
def start_interview_flow():
    current_user = request.user
    """
    Start mock interview with user's skills
    
    Request:
        {
            "target_role": "Full Stack Developer",
            "experience_level": "Mid-level"
        }
    
    Response:
        {
            "session_id": 123,
            "first_question": "...",
            "context": {...}
        }
    """
    try:
        data = request.json
        target_role = data.get('target_role', 'Full Stack Developer')
        experience_level = data.get('experience_level', 'Mid-level')
        
        user_id = current_user['id']
        
        result = orchestrator.start_complete_interview(
            user_id=user_id,
            target_role=target_role,
            experience_level=experience_level
        )
        
        # Store interview engine
        from app.services.interview_engine import InterviewEngine
        engine = InterviewEngine()
        
        # Get skills for engine
        skill_graph = orchestrator.get_user_skill_graph(user_id)
        all_skills = []
        for category_skills in skill_graph.values():
            all_skills.extend(category_skills)
        
        # Initialize engine with context
        engine.interview_context = {
            "role": target_role,
            "level": experience_level,
            "skills": all_skills
        }
        
        active_interviews[user_id] = engine
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/interview/answer', methods=['POST'])
@token_required
def submit_interview_answer():
    current_user = request.user
    """
    Submit answer and get next question
    NOW INCLUDES: Speech metrics for fluency and pronunciation analysis
    
    Request:
        {
            "session_id": 123,
            "answer": "User's answer...",
            "speech_metrics": {
                "words_per_minute": 145,
                "pause_count": 5,
                "filler_words": ["um", "like"],
                "pronunciation_clarity": 85
            }
        }
    
    Response:
        {
            "feedback": "...",
            "next_question": "...",
            "score": 7,
            "fluency_score": 7.5,
            "pronunciation_score": 8.5,
            "question_number": 2
        }
    """
    try:
        data = request.json
        session_id = data.get('session_id')
        answer = data.get('answer')
        speech_metrics = data.get('speech_metrics', None)
        
        if not answer:
            return jsonify({'error': 'Answer required'}), 400
        
        user_id = current_user['id']
        engine = active_interviews.get(user_id)
        
        if not engine:
            return jsonify({'error': 'No active interview session'}), 400
        
        # Process answer with speech metrics
        result = engine.process_answer(
            user_answer=answer,
            audio_transcript=answer,
            speech_metrics=speech_metrics
        )
        
        # Save Q&A to database with all scores
        db = get_db()
        db.execute(
            """UPDATE interview_qa 
               SET answer = ?, score = ?, feedback = ?,
                   content_score = ?, communication_score = ?,
                   fluency_score = ?, pronunciation_score = ?,
                   speech_analysis = ?
               WHERE session_id = ? 
               AND answer IS NULL 
               ORDER BY asked_at DESC LIMIT 1""",
            (
                answer, 
                result['score'], 
                result['feedback'],
                result.get('content_score', 5.0),
                result.get('communication_score', 5.0),
                result.get('fluency_score', 5.0),
                result.get('pronunciation_score', 5.0),
                json.dumps(result.get('speech_analysis', {})),
                session_id
            )
        )
        
        # Save next question
        db.execute(
            """INSERT INTO interview_qa 
               (session_id, question) 
               VALUES (?, ?)""",
            (session_id, result['next_question'])
        )
        db.commit()
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/interview/complete', methods=['POST'])
@token_required
def complete_interview_flow():
    current_user = request.user
    """
    Complete interview and get full analysis
    NOW INCLUDES: Proctoring warnings data
    
    Request:
        {
            "session_id": 123,
            "proctoring_warnings": [...]  # Optional proctoring data
        }
    
    Response:
        {
            "evaluation": {...},
            "skill_gaps": {...},
            "learning_path": {...},
            "readiness": {...}
        }
    """
    try:
        data = request.json
        session_id = data.get('session_id')
        proctoring_warnings = data.get('proctoring_warnings', [])
        
        user_id = current_user['id']
        engine = active_interviews.get(user_id)
        
        if not engine:
            return jsonify({'error': 'No active interview session'}), 400
        
        # Get final evaluation from engine
        evaluation = engine.end_interview()
        
        # Add proctoring data to evaluation
        if proctoring_warnings:
            evaluation['proctoring'] = {
                'total_warnings': len(proctoring_warnings),
                'warnings': proctoring_warnings
            }
        
        # Update session in database
        db = get_db()
        db.execute(
            """UPDATE interview_sessions 
               SET status = 'completed', 
                   overall_score = ?, 
                   evaluation_data = ?,
                   ended_at = CURRENT_TIMESTAMP 
               WHERE id = ?""",
            (evaluation['overall_score'], json.dumps(evaluation), session_id)
        )
        db.commit()
        
        # Complete the cycle (gap analysis + learning path)
        result = orchestrator.complete_interview_cycle(
            session_id=session_id,
            user_id=user_id
        )
        
        # Clean up
        del active_interviews[user_id]
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/dashboard', methods=['GET'])
@token_required
def get_dashboard():
    current_user = request.user
    """
    Get complete user dashboard
    
    Response:
        {
            "resume": {...},
            "skill_graph": {...},
            "recent_interviews": [...],
            "skill_gaps": {...},
            "learning_path": {...},
            "stats": {...}
        }
    """
    try:
        user_id = current_user['id']
        
        dashboard = orchestrator.get_user_dashboard(user_id)
        
        return jsonify({
            'success': True,
            'data': dashboard
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/chat', methods=['POST'])
@token_required
def chat_with_ai():
    current_user = request.user
    """
    Chat with AI coach (context-aware)
    
    Request:
        {
            "message": "How can I improve my React skills?"
        }
    
    Response:
        {
            "response": "...",
            "suggestions": [...]
        }
    """
    try:
        data = request.json
        message = data.get('message')
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
        
        user_id = current_user['id']
        
        response = orchestrator.chat_with_context(
            user_id=user_id,
            message=message
        )
        
        # Save to chat history
        db = get_db()
        try:
            db.execute(
                """INSERT INTO chat_messages (user_id, role, message) 
                   VALUES (?, 'user', ?)""",
                (user_id, message)
            )
            db.execute(
                """INSERT INTO chat_messages (user_id, role, message) 
                   VALUES (?, 'assistant', ?)""",
                (user_id, response['response'])
            )
            db.commit()
        except sqlite3.IntegrityError as e:
            # Foreign key constraint or other integrity error
            print(f"Database integrity error (non-critical): {e}")
            print(f"User ID: {user_id}")
            # Response is still valid, just history wasn't saved
        except sqlite3.OperationalError as e:
            # If database is locked, log but don't fail the request
            print(f"Database lock error (non-critical): {e}")
            # Response is still valid, just history wasn't saved
        
        return jsonify({
            'success': True,
            'data': response
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/chat/history', methods=['GET'])
@token_required
def get_chat_history():
    current_user = request.user
    """Get chat history"""
    try:
        user_id = current_user['id']
        limit = request.args.get('limit', 50, type=int)
        
        db = get_db()
        messages = db.execute(
            """SELECT role, message, created_at 
               FROM chat_messages 
               WHERE user_id = ? 
               ORDER BY created_at DESC 
               LIMIT ?""",
            (user_id, limit)
        ).fetchall()
        
        history = []
        for msg in reversed(messages):
            history.append({
                "role": msg['role'],
                "message": msg['message'],
                "created_at": msg['created_at']
            })
        
        return jsonify({
            'success': True,
            'messages': history
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/chat/clear', methods=['POST'])
@token_required
def clear_chat_history():
    current_user = request.user
    """Clear all chat history for the user"""
    try:
        user_id = current_user['id']
        
        db = get_db()
        db.execute(
            "DELETE FROM chat_messages WHERE user_id = ?",
            (user_id,)
        )
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Chat history cleared successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/skill-graph', methods=['GET'])
@token_required
def get_skill_graph():
    current_user = request.user
    """Get user's skill graph"""
    try:
        user_id = current_user['id']
        
        skill_graph = orchestrator.get_user_skill_graph(user_id)
        
        return jsonify({
            'success': True,
            'data': skill_graph
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/learning-path/update-progress', methods=['POST'])
@token_required
def update_learning_progress():
    current_user = request.user
    """
    Update learning path progress
    
    Request:
        {
            "phase": 1,
            "completed": true
        }
    """
    try:
        data = request.json
        phase = data.get('phase')
        completed = data.get('completed', False)
        
        user_id = current_user['id']
        
        # Get current learning path
        db = get_db()
        path = db.execute(
            """SELECT id, path_data, progress 
               FROM learning_paths 
               WHERE user_id = ? 
               ORDER BY created_at DESC LIMIT 1""",
            (user_id,)
        ).fetchone()
        
        if not path:
            return jsonify({'error': 'No learning path found'}), 404
        
        path_data = json.loads(path['path_data'])
        total_phases = len(path_data.get('phases', []))
        
        # Calculate new progress
        if completed:
            new_progress = min(100, (phase / total_phases) * 100)
        else:
            new_progress = path['progress']
        
        # Update progress
        db.execute(
            """UPDATE learning_paths 
               SET progress = ?, updated_at = CURRENT_TIMESTAMP 
               WHERE id = ?""",
            (new_progress, path['id'])
        )
        db.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'progress': new_progress,
                'phase': phase,
                'total_phases': total_phases
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
