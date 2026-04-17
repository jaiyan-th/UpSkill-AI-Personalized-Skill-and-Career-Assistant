"""
Enhanced Interview Routes - Complete Mock Interview API
Endpoints: start, question, answer, evaluate, result, proctor
"""

from flask import Blueprint, request, jsonify
from app.auth_utils import require_auth
from app.services.interview_service import InterviewService
import base64
import os
from datetime import datetime

interview_bp = Blueprint('interview_enhanced', __name__, url_prefix='/api/interview')

# Store active sessions in memory (use Redis in production)
active_sessions = {}

@interview_bp.route('/start', methods=['POST'])
@require_auth
def start_interview(current_user):
    """
    Start new interview session
    
    Request:
        {
            "role": "Software Developer",
            "level": "Mid-level"
        }
    
    Response:
        {
            "success": true,
            "session_id": 123,
            "first_question": "...",
            "question_type": "behavioral",
            "total_questions": 5,
            "duration_minutes": 4
        }
    """
    try:
        data = request.json or {}
        role = data.get('role', 'Software Developer')
        level = data.get('level', 'Mid-level')
        
        user_id = current_user['id']
        
        service = InterviewService()
        
        # Create session
        session_data = service.create_session(user_id, role, level)
        session_id = session_data['session_id']
        
        # Generate first question (with fallback)
        try:
            first_question = service.generate_question(role, level, 0)
        except Exception as qe:
            print(f"Question generation failed, using fallback: {str(qe)}")
            # Use fallback question
            first_question = {
                'type': 'behavioral',
                'text': f"Tell me about yourself and why you're interested in the {role} position.",
                'index': 0
            }
        
        # Store session state
        active_sessions[session_id] = {
            'user_id': user_id,
            'role': role,
            'level': level,
            'current_index': 0,
            'total_questions': 5,
            'qa_history': [],
            'current_question': first_question
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'first_question': first_question['text'],
            'question_type': first_question['type'],
            'question_index': 0,
            'total_questions': 5,
            'duration_minutes': session_data['duration_minutes'],
            'role': role,
            'level': level
        })
        
    except Exception as e:
        print(f"ERROR in start_interview: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500


@interview_bp.route('/question/<int:session_id>', methods=['GET'])
@require_auth
def get_question(current_user, session_id):
    """
    Get current or next question
    
    Response:
        {
            "question": "...",
            "question_type": "technical",
            "question_index": 1,
            "total_questions": 5
        }
    """
    try:
        session = active_sessions.get(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if session['user_id'] != current_user['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        current_q = session['current_question']
        
        return jsonify({
            'success': True,
            'question': current_q['text'],
            'question_type': current_q['type'],
            'question_index': session['current_index'],
            'total_questions': session['total_questions']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@interview_bp.route('/answer', methods=['POST'])
@require_auth
def submit_answer(current_user):
    """
    Submit answer and get evaluation + next question
    
    Request:
        {
            "session_id": 123,
            "answer": "My answer text...",
            "time_taken": 45
        }
    
    Response:
        {
            "success": true,
            "evaluation": {
                "score": 8,
                "feedback": "...",
                "improvement": "..."
            },
            "next_question": "...",
            "question_type": "coding",
            "is_final": false,
            "progress": 2
        }
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        answer = data.get('answer', '').strip()
        time_taken = data.get('time_taken', 0)
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        session = active_sessions.get(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if session['user_id'] != current_user['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        service = InterviewService()
        current_q = session['current_question']
        
        # Evaluate answer
        evaluation = service.evaluate_answer(
            question=current_q['text'],
            answer=answer,
            question_type=current_q['type'],
            role=session['role'],
            level=session['level']
        )
        
        # Save Q&A to database
        service.save_qa(
            session_id=session_id,
            question=current_q['text'],
            answer=answer,
            question_type=current_q['type'],
            evaluation=evaluation
        )
        
        # Add to history
        session['qa_history'].append({
            'question': current_q['text'],
            'answer': answer,
            'score': evaluation['score'],
            'type': current_q['type']
        })
        
        # Move to next question
        session['current_index'] += 1
        is_final = session['current_index'] >= session['total_questions']
        
        next_question_data = None
        if not is_final:
            # Generate next question (adaptive based on performance)
            next_question_data = service.generate_question(
                role=session['role'],
                level=session['level'],
                question_index=session['current_index'],
                previous_answers=session['qa_history']
            )
            session['current_question'] = next_question_data
        
        response = {
            'success': True,
            'evaluation': {
                'score': evaluation['score'],
                'feedback': evaluation['feedback'],
                'improvement': evaluation.get('improvement', ''),
                'content_score': evaluation['content_score'],
                'communication_score': evaluation['communication_score']
            },
            'is_final': is_final,
            'progress': session['current_index'],
            'total_questions': session['total_questions']
        }
        
        if next_question_data:
            response['next_question'] = next_question_data['text']
            response['question_type'] = next_question_data['type']
            response['question_index'] = next_question_data['index']
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@interview_bp.route('/evaluate/<int:session_id>', methods=['POST'])
@require_auth
def evaluate_interview(current_user, session_id):
    """
    Generate final evaluation for completed interview
    
    Response:
        {
            "success": true,
            "evaluation": {
                "overall_score": 75,
                "technical_accuracy": 8.0,
                "communication_clarity": 7.5,
                "role_fit": 8,
                "strengths": [...],
                "weaknesses": [...],
                "overall_assessment": "..."
            }
        }
    """
    try:
        session = active_sessions.get(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if session['user_id'] != current_user['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        service = InterviewService()
        
        # Generate comprehensive evaluation
        evaluation = service.generate_final_evaluation(
            session_id=session_id,
            role=session['role'],
            level=session['level']
        )
        
        # Clean up session
        del active_sessions[session_id]
        
        return jsonify({
            'success': True,
            'evaluation': evaluation
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@interview_bp.route('/result/<int:session_id>', methods=['GET'])
@require_auth
def get_result(current_user, session_id):
    """
    Get interview results (for completed interviews)
    
    Response:
        {
            "success": true,
            "session_id": 123,
            "role": "Software Developer",
            "level": "Mid-level",
            "overall_score": 75,
            "evaluation": {...},
            "qa_pairs": [...]
        }
    """
    try:
        service = InterviewService()
        
        # Get session status
        session_status = service.get_session_status(session_id)
        
        if not session_status:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get evaluation from database
        from app.database import get_db
        db = get_db()
        
        session_data = db.execute(
            """SELECT * FROM interview_sessions WHERE id = ?""",
            [session_id]
        ).fetchone()
        
        if session_data['user_id'] != current_user['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get Q&A pairs
        qa_pairs = db.execute(
            """SELECT question, answer, type, score, feedback
               FROM interview_qa
               WHERE session_id = ?
               ORDER BY id""",
            [session_id]
        ).fetchall()
        
        # Parse evaluation data
        import json
        evaluation = {}
        if session_data['evaluation_data']:
            try:
                evaluation = json.loads(session_data['evaluation_data'])
            except:
                pass
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'role': session_data['role'],
            'level': session_data['level'],
            'status': session_data['status'],
            'overall_score': session_data['overall_score'],
            'started_at': session_data['started_at'],
            'ended_at': session_data['ended_at'],
            'evaluation': evaluation,
            'qa_pairs': [dict(qa) for qa in qa_pairs]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@interview_bp.route('/proctor', methods=['POST'])
@require_auth
def log_proctor_event(current_user):
    """
    Log proctoring events
    
    Request:
        {
            "session_id": 123,
            "event_type": "tab_switch" | "face_not_detected" | "multiple_faces",
            "details": "Additional info",
            "snapshot": "base64_image_data" (optional)
        }
    
    Response:
        {
            "success": true,
            "logged": true
        }
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        event_type = data.get('event_type')
        details = data.get('details', '')
        snapshot = data.get('snapshot')  # Base64 encoded image
        
        if not session_id or not event_type:
            return jsonify({'error': 'Session ID and event type required'}), 400
        
        service = InterviewService()
        
        # Save snapshot if provided
        image_path = None
        if snapshot:
            try:
                # Create proctor_images directory if not exists
                images_dir = os.path.join('app', 'proctor_images')
                os.makedirs(images_dir, exist_ok=True)
                
                # Save image
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                image_filename = f"session_{session_id}_{timestamp}.jpg"
                image_path = os.path.join(images_dir, image_filename)
                
                # Decode and save
                image_data = base64.b64decode(snapshot.split(',')[1] if ',' in snapshot else snapshot)
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                
                details += f" | Image: {image_filename}"
            except Exception as e:
                print(f"Error saving snapshot: {e}")
        
        # Log event
        service.log_proctor_event(
            session_id=session_id,
            event_type=event_type,
            details=details
        )
        
        return jsonify({
            'success': True,
            'logged': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@interview_bp.route('/status/<int:session_id>', methods=['GET'])
@require_auth
def get_status(current_user, session_id):
    """Get current interview session status"""
    try:
        service = InterviewService()
        status = service.get_session_status(session_id)
        
        if not status:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
