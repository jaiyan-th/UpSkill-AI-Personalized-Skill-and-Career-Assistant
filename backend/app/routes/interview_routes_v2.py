"""
Interview Routes V2 - Production-Ready Mock Interview System
Refactored with structured responses, validation, and comprehensive error handling
"""

from flask import Blueprint, request
from app.auth_utils import require_auth
from app.database import get_db
from app.error_handlers import success_response, error_response
from app.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    BusinessLogicError,
    InterviewSessionError,
    LLMError,
    DatabaseError
)
from app.validators import validate_request
from app.services.interview_service import InterviewService
import base64
import os
from datetime import datetime
import json

interview_v2_bp = Blueprint('interview_v2', __name__, url_prefix='/api/ai/interview')

# Store active sessions in memory (use Redis in production)
active_sessions = {}


# Validation schemas
INTERVIEW_START_SCHEMA = {
    "role": {"type": "string", "required": True, "min_length": 2, "max_length": 100},
    "level": {"type": "enum", "required": True, "allowed_values": ["Entry", "Mid-level", "Senior"]}
}

INTERVIEW_ANSWER_SCHEMA = {
    "answer": {"type": "string", "required": True, "min_length": 1, "max_length": 5000}
}


@interview_v2_bp.post('/start')
@require_auth
@validate_request(INTERVIEW_START_SCHEMA)
def start_interview():
    """
    Start new interview session
    
    Request Body:
        {
            "role": "Software Developer" (required),
            "level": "Entry|Mid-level|Senior" (required),
            "skills": ["Python", "React"] (optional),
            "resume_summary": "..." (optional)
        }
    
    Returns:
        201: {
            success: true,
            data: {
                session_id, first_question, question_type,
                total_questions, duration_minutes
            },
            message
        }
    """
    try:
        data = request.validated_data
        user_id = request.user['id']
        
        role = data["role"]
        level = data["level"]
        
        # Optional fields
        full_data = request.get_json() or {}
        skills = full_data.get('skills', [])
        resume_summary = full_data.get('resume_summary')
        
        service = InterviewService()
        
        # Create session
        try:
            session_data = service.create_session(user_id, role, level)
            session_id = session_data['session_id']
        except ValueError as e:
            raise ResourceNotFoundError("User", str(user_id))
        except Exception as e:
            raise DatabaseError(f"Failed to create interview session: {str(e)}")
        
        # Generate first question with fallback
        try:
            first_question = service.generate_question(role, level, 0)
        except LLMError as e:
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
        
        response_data = {
            'session_id': session_id,
            'first_question': first_question['text'],
            'question_type': first_question['type'],
            'text_required': first_question.get('text_required', False),
            'question_index': 0,
            'total_questions': 5,
            'duration_minutes': session_data['duration_minutes'],
            'role': role,
            'level': level
        }
        
        return success_response(
            data=response_data,
            message="Interview session started successfully",
            status_code=201
        )
        
    except (ValidationError, ResourceNotFoundError, DatabaseError, LLMError):
        raise
    except Exception as e:
        raise InterviewSessionError(f"Failed to start interview: {str(e)}")


@interview_v2_bp.post('/answer')
@require_auth
def submit_answer():
    """
    Submit answer and get evaluation + next question
    
    Request Body:
        {
            "session_id": 123 (required),
            "answer": "My answer..." (required),
            "time_taken": 45 (optional, seconds)
        }
    
    Returns:
        200: {
            success: true,
            data: {
                evaluation, next_question, is_final, progress
            },
            message
        }
    """
    try:
        data = request.get_json() or {}
        user_id = request.user['id']
        
        # Validate required fields
        session_id = data.get('session_id')
        if not session_id:
            raise ValidationError("Session ID is required", field="session_id")
        
        answer = data.get('answer', '').strip()
        if not answer:
            raise ValidationError("Answer is required", field="answer")
        
        if len(answer) > 5000:
            raise ValidationError(
                "Answer is too long (maximum 5000 characters)",
                field="answer"
            )
        
        time_taken = data.get('time_taken', 0)
        
        # Get session
        session = active_sessions.get(session_id)
        
        if not session:
            raise ResourceNotFoundError("Interview session", str(session_id))
        
        if session['user_id'] != user_id:
            raise InterviewSessionError("Unauthorized access to interview session")
        
        service = InterviewService()
        current_q = session['current_question']

        # Validate: text-required questions must have a real answer (not just "Skipped")
        TEXT_REQUIRED_TYPES = {'coding', 'aptitude', 'writing'}
        q_type = current_q.get('type', '')
        text_required = current_q.get('text_required', q_type in TEXT_REQUIRED_TYPES)
        if text_required and answer.lower() in ('skipped', 'skip', ''):
            raise ValidationError(
                f"A written answer is required for {q_type} questions.",
                field="answer"
            )
        
        # Evaluate answer with retry logic
        try:
            evaluation = service.evaluate_answer(
                question=current_q['text'],
                answer=answer,
                question_type=current_q['type'],
                role=session['role'],
                level=session['level']
            )
        except LLMError:
            # Provide fallback evaluation
            evaluation = {
                'score': 5,
                'content_score': 5,
                'communication_score': 5,
                'technical_accuracy': 5,
                'feedback': 'Answer received. Evaluation temporarily unavailable.',
                'improvement': 'Keep practicing and provide detailed responses.'
            }
        
        # Save Q&A to database
        try:
            service.save_qa(
                session_id=session_id,
                question=current_q['text'],
                answer=answer,
                question_type=current_q['type'],
                evaluation=evaluation
            )
        except Exception as e:
            raise DatabaseError(f"Failed to save answer: {str(e)}")
        
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
            try:
                next_question_data = service.generate_question(
                    role=session['role'],
                    level=session['level'],
                    question_index=session['current_index'],
                    previous_answers=session['qa_history']
                )
                session['current_question'] = next_question_data
            except LLMError:
                # Use fallback question
                next_question_data = {
                    'type': 'technical',
                    'text': f"Describe your experience with {session['role']} technologies.",
                    'index': session['current_index']
                }
                session['current_question'] = next_question_data
        
        response_data = {
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
            response_data['next_question'] = next_question_data['text']
            response_data['question_type'] = next_question_data['type']
            response_data['text_required'] = next_question_data.get('text_required', False)
            response_data['question_index'] = next_question_data['index']
        
        return success_response(
            data=response_data,
            message="Answer submitted successfully"
        )
        
    except (ValidationError, ResourceNotFoundError, InterviewSessionError, DatabaseError):
        raise
    except Exception as e:
        raise InterviewSessionError(f"Failed to submit answer: {str(e)}")


@interview_v2_bp.post('/end')
@require_auth
def end_interview():
    """
    End interview and generate final evaluation
    
    Request Body:
        {
            "session_id": 123 (required)
        }
    
    Returns:
        200: {
            success: true,
            data: { evaluation: {...} },
            message
        }
    """
    try:
        data = request.get_json() or {}
        user_id = request.user['id']
        
        # Validate session_id
        session_id = data.get('session_id')
        if not session_id:
            raise ValidationError("Session ID is required", field="session_id")
        
        # Get session
        session = active_sessions.get(session_id)
        
        if not session:
            raise ResourceNotFoundError("Interview session", str(session_id))
        
        if session['user_id'] != user_id:
            raise InterviewSessionError("Unauthorized access to interview session")
        
        service = InterviewService()
        
        # Generate comprehensive evaluation
        try:
            evaluation = service.generate_final_evaluation(
                session_id=session_id,
                role=session['role'],
                level=session['level']
            )
        except LLMError:
            # Provide basic evaluation as fallback
            db = get_db()
            qa_pairs = db.execute(
                """SELECT score FROM interview_qa WHERE session_id = ?""",
                [session_id]
            ).fetchall()
            
            if qa_pairs:
                avg_score = sum(qa['score'] for qa in qa_pairs) / len(qa_pairs)
                overall_score = round(avg_score * 10)
            else:
                overall_score = 0
            
            evaluation = {
                'overall_score': overall_score,
                'technical_accuracy': overall_score / 10,
                'communication_clarity': overall_score / 10,
                'role_fit': 5,
                'questions_answered': len(qa_pairs),
                'strengths': ['Completed the interview'],
                'weaknesses': ['Evaluation temporarily unavailable'],
                'areas_to_improve': ['Practice more technical questions'],
                'overall_assessment': 'Good effort. Keep practicing.',
                'confidence': 5,
                'fluency': 5
            }
            
            # Save basic evaluation
            db.execute(
                """UPDATE interview_sessions
                   SET overall_score = ?,
                       status = 'completed',
                       ended_at = datetime('now'),
                       evaluation_data = ?
                   WHERE id = ?""",
                [overall_score, json.dumps(evaluation), session_id]
            )
            db.commit()
        
        # Clean up session
        if session_id in active_sessions:
            del active_sessions[session_id]
        
        return success_response(
            data={'evaluation': evaluation},
            message="Interview completed successfully"
        )
        
    except (ValidationError, ResourceNotFoundError, InterviewSessionError):
        raise
    except Exception as e:
        raise InterviewSessionError(f"Failed to end interview: {str(e)}")


@interview_v2_bp.get('/insights')
@require_auth
def get_insights():
    """
    Get interview insights and analytics for user
    
    Returns:
        200: {
            success: true,
            data: {
                total_interviews, average_score, recent_interviews,
                skill_trends, improvement_areas
            }
        }
    """
    try:
        user_id = request.user['id']
        db = get_db()
        
        # Get interview statistics
        stats = db.execute(
            """SELECT 
                   COUNT(*) as total_interviews,
                   AVG(overall_score) as avg_score,
                   MAX(overall_score) as best_score
               FROM interview_sessions
               WHERE user_id = ? AND status = 'completed'""",
            [user_id]
        ).fetchone()
        
        # Get recent interviews
        recent = db.execute(
            """SELECT id, role, level, overall_score, started_at
               FROM interview_sessions
               WHERE user_id = ? AND status = 'completed'
               ORDER BY started_at DESC
               LIMIT 5""",
            [user_id]
        ).fetchall()
        
        recent_list = [
            {
                'session_id': r['id'],
                'role': r['role'],
                'level': r['level'],
                'score': r['overall_score'],
                'date': r['started_at']
            }
            for r in recent
        ]
        
        insights_data = {
            'total_interviews': stats['total_interviews'] or 0,
            'average_score': round(stats['avg_score'] or 0, 1),
            'best_score': stats['best_score'] or 0,
            'recent_interviews': recent_list,
            'improvement_areas': [
                'Practice more technical questions',
                'Improve communication clarity',
                'Provide more specific examples'
            ]
        }
        
        return success_response(
            data=insights_data
        )
        
    except Exception as e:
        raise DatabaseError(f"Failed to fetch insights: {str(e)}")
