from flask import Blueprint, jsonify, request
from app.database import get_db
from app.auth_utils import require_auth
from app.services.recommend import get_learning_path, recommend_careers

learning_bp = Blueprint("learning", __name__)


@learning_bp.get("/")
@require_auth
def get_learning_path_route():
    uid = request.user["id"]
    db = get_db()
    
    # Get user's target role from profile or latest interview
    profile = db.execute("SELECT preferred_field FROM profiles WHERE user_id = ?", [uid]).fetchone()
    
    if not profile or not profile['preferred_field']:
        interview = db.execute(
            "SELECT role FROM interview_sessions WHERE user_id = ? ORDER BY started_at DESC LIMIT 1",
            [uid]
        ).fetchone()
        target_role = interview['role'] if interview else 'Software Engineer'
    else:
        target_role = profile['preferred_field']
    
    # Get latest skill gap analysis
    gap_record = db.execute(
        "SELECT gap_data FROM skill_gap_analysis WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        [uid]
    ).fetchone()
    
    if not gap_record:
        # No gap analysis yet - return error with clear message
        return jsonify({
            "success": False,
            "error": "No skill gap analysis found. Please complete resume upload, mock interview, and skill gap analysis first.",
            "learning_path": None
        }), 404
    
    import json
    gap_data = json.loads(gap_record['gap_data'])
    
    # Extract resume gaps and interview gaps
    resume_gaps = gap_data.get('missing_skills', [])
    interview_gaps = gap_data.get('communication_gaps', [])
    
    # Get user skills
    user_skills = db.execute("SELECT skill_name, level FROM student_skills WHERE user_id = ?", [uid]).fetchall()
    skills_list = [{"name": s["skill_name"], "level": s["level"]} for s in user_skills]
    
    # Generate learning path with both gap sources
    from app.services.skill_gap_analyzer import SkillGapAnalyzer
    analyzer = SkillGapAnalyzer()
    
    learning_path = analyzer.generate_learning_path(
        current_skills=skills_list,
        target_role=target_role,
        skill_gaps=gap_data.get('skill_gaps'),
        time_available_hours_per_week=10,
        resume_gaps=resume_gaps,
        interview_gaps=interview_gaps
    )
    
    # Save learning path
    db.execute(
        "INSERT INTO learning_paths (user_id, target_role, path_data) VALUES (?, ?, ?)",
        [uid, target_role, json.dumps(learning_path)]
    )
    db.commit()
    
    # Return structured response
    return jsonify({
        "success": True,
        "learning_path": {
            "resume_based_resources": learning_path.get('resume_based_resources', []),
            "interview_based_resources": learning_path.get('interview_based_resources', []),
            "phases": learning_path.get('phases', []),
            "target_role": target_role,
            "total_duration_weeks": learning_path.get('total_duration_weeks'),
            "estimated_job_readiness": learning_path.get('estimated_job_readiness')
        }
    })
