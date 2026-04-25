"""
Skill Gap Analysis Routes
API endpoints for skill gap analysis and learning recommendations
"""

from flask import Blueprint, request, jsonify
from app.auth_utils import require_auth
from app.services.skill_gap_service import SkillGapService

skill_gap_bp = Blueprint('skill_gap_enhanced', __name__, url_prefix='/api/skill-gap')

@skill_gap_bp.route('/analyze', methods=['POST'])
@require_auth
def analyze_skill_gaps(current_user):
    """
    Analyze skill gaps for user
    REQUIRES: BOTH Resume AND Interview data to be available
    
    Request:
        {
            "role": "Software Developer",
            "level": "Mid-level"
        }
    
    Response:
        {
            "success": true,
            "analysis": {
                "strong_skills": [...],
                "missing_skills": [...],
                "weak_skills": [...],
                "readiness_score": 75,
                "analysis_summary": "..."
            }
        }
    """
    try:
        data = request.json or {}
        role = data.get('role', 'Software Developer')
        level = data.get('level', 'Mid-level')
        
        user_id = current_user['id']
        
        # Check if user has BOTH resume AND interview data
        from app.database import get_db
        db = get_db()
        
        # Check for resume
        resume = db.execute(
            "SELECT id FROM resumes WHERE user_id = ? LIMIT 1",
            [user_id]
        ).fetchone()
        
        # Check for completed interview
        interview = db.execute(
            "SELECT id FROM interview_sessions WHERE user_id = ? AND status = 'completed' LIMIT 1",
            [user_id]
        ).fetchone()
        
        # Require BOTH data sources for skill gap analysis
        missing = []
        if not resume:
            missing.append('resume')
        if not interview:
            missing.append('interview')
        
        if missing:
            missing_text = ' and '.join(missing)
            return jsonify({
                'success': False,
                'error': 'Incomplete data for skill gap analysis',
                'message': f'Skill Gap Analysis requires both your resume and mock interview data. Please complete: {missing_text}.',
                'required_actions': {
                    'resume': not resume,
                    'interview': not interview
                },
                'missing': missing
            }), 400
        
        # Proceed with analysis (both data sources available)
        service = SkillGapService()
        analysis = service.analyze_skill_gaps(user_id, role, level)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        print(f"Error in analyze_skill_gaps: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500


@skill_gap_bp.route('/learning-path', methods=['POST'])
@require_auth
def generate_learning_path(current_user):
    """
    Generate personalized learning path
    
    Request:
        {
            "role": "Software Developer",
            "hours_per_week": 10
        }
    
    Response:
        {
            "success": true,
            "learning_path": {
                "phases": [...],
                "total_duration_weeks": 12,
                "next_steps": [...]
            }
        }
    """
    try:
        data = request.json or {}
        role = data.get('role', 'Software Developer')
        hours_per_week = data.get('hours_per_week', 10)
        
        user_id = current_user['id']
        service = SkillGapService()
        
        learning_path = service.generate_learning_path(user_id, role, hours_per_week)
        
        return jsonify({
            'success': True,
            'learning_path': learning_path
        })
        
    except Exception as e:
        print(f"Error in generate_learning_path: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500


@skill_gap_bp.route('/recommendations', methods=['GET'])
@require_auth
def get_recommendations(current_user):
    """
    Get course recommendations based on skill gaps
    
    Response:
        {
            "success": true,
            "recommendations": [
                {
                    "skill": "Python",
                    "courses": ["Course 1", "Course 2"]
                }
            ]
        }
    """
    try:
        user_id = current_user['id']
        service = SkillGapService()
        
        # Get latest analysis
        from app.database import get_db
        db = get_db()
        
        analysis = db.execute(
            """SELECT gap_data FROM skill_gap_analysis 
               WHERE user_id = ? ORDER BY created_at DESC LIMIT 1""",
            [user_id]
        ).fetchone()
        
        if not analysis:
            return jsonify({
                'success': False,
                'error': 'No skill gap analysis found. Please run analysis first.'
            }), 404
        
        import json
        gap_data = json.loads(analysis['gap_data'])
        missing_skills = [s['skill'] for s in gap_data.get('missing_skills', [])[:5]]
        
        recommendations = service.get_course_recommendations(missing_skills)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
        
    except Exception as e:
        print(f"Error in get_recommendations: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@skill_gap_bp.route('/history', methods=['GET'])
@require_auth
def get_analysis_history(current_user):
    """
    Get user's skill gap analysis history
    
    Response:
        {
            "success": true,
            "history": [
                {
                    "id": 1,
                    "target_role": "Software Developer",
                    "readiness_score": 75,
                    "created_at": "2026-04-09"
                }
            ]
        }
    """
    try:
        user_id = current_user['id']
        
        from app.database import get_db
        db = get_db()
        
        analyses = db.execute(
            """SELECT analysis_id as id, target_role, gap_data, created_at 
               FROM skill_gap_analysis 
               WHERE user_id = ? 
               ORDER BY created_at DESC 
               LIMIT 10""",
            [user_id]
        ).fetchall()
        
        history = []
        for analysis in analyses:
            import json
            gap_data = json.loads(analysis['gap_data'])
            history.append({
                'id': analysis['id'],
                'target_role': analysis['target_role'],
                'readiness_score': gap_data.get('readiness_score', 0),
                'missing_skills_count': len(gap_data.get('missing_skills', [])),
                'created_at': analysis['created_at']
            })
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        print(f"Error in get_analysis_history: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@skill_gap_bp.route('/history/<int:analysis_id>', methods=['DELETE'])
@require_auth
def delete_skill_gap_history(current_user, analysis_id):
    """Delete a specific skill gap analysis from history."""
    try:
        user_id = current_user['id']
        from app.database import get_db
        db = get_db()
        
        # Check if it exists and belongs to the user
        analysis = db.execute(
            "SELECT analysis_id FROM skill_gap_analysis WHERE analysis_id = ? AND user_id = ?",
            (analysis_id, user_id)
        ).fetchone()
        
        if not analysis:
            return jsonify({'success': False, 'error': 'Skill gap analysis not found or unauthorized'}), 404
            
        # Delete it
        db.execute("DELETE FROM skill_gap_analysis WHERE analysis_id = ?", (analysis_id,))
        db.commit()
        
        return jsonify({'success': True, 'message': 'Skill gap analysis deleted successfully'})
        
    except Exception as e:
        print(f"Error deleting skill gap history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@skill_gap_bp.route('/progress', methods=['POST'])
@require_auth
def update_progress(current_user):
    """
    Update learning progress
    
    Request:
        {
            "skill": "Python",
            "progress": 50
        }
    """
    try:
        data = request.json or {}
        skill = data.get('skill')
        progress = data.get('progress', 0)
        
        if not skill:
            return jsonify({'error': 'Skill is required'}), 400
        
        user_id = current_user['id']
        
        from app.database import get_db
        db = get_db()
        
        # Update or insert progress
        db.execute(
            """INSERT OR REPLACE INTO user_skill_graph 
               (user_id, skill_name, skill_level, last_assessed)
               VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
            [user_id, skill, f"{progress}%"]
        )
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Progress updated'
        })
        
    except Exception as e:
        print(f"Error in update_progress: {e}")
        return jsonify({'error': str(e), 'success': False}), 500
