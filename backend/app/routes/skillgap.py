from flask import Blueprint, request, jsonify
from app.database import get_db
from app.auth_utils import require_auth

skillgap_bp = Blueprint("skillgap", __name__)


@skillgap_bp.get("/")
@require_auth
def get_skill_gap():
    """Get user's skills and advanced gap analysis"""
    uid = request.user["id"]
    db = get_db()
    
    # Get target role from profiles table or latest interview session
    profile = db.execute("SELECT preferred_field FROM profiles WHERE user_id = ?", [uid]).fetchone()
    
    # If no profile, try to get from latest interview session
    if not profile or not profile['preferred_field']:
        interview = db.execute(
            "SELECT role FROM interview_sessions WHERE user_id = ? ORDER BY started_at DESC LIMIT 1",
            [uid]
        ).fetchone()
        target_role = interview['role'] if interview else 'your target role'
    else:
        target_role = profile['preferred_field']
    
    # Check if user has uploaded resume
    resume_check = db.execute(
        "SELECT id FROM resumes WHERE user_id = ? LIMIT 1",
        [uid]
    ).fetchone()
    has_resume = resume_check is not None
    
    # Check if user has completed interview
    interview_check = db.execute(
        "SELECT id FROM interview_sessions WHERE user_id = ? AND status = 'completed' LIMIT 1",
        [uid]
    ).fetchone()
    has_interview = interview_check is not None
    
    # Get basic skills
    skills = db.execute(
        "SELECT skill_name, level FROM student_skills WHERE user_id = ?",
        [uid]
    ).fetchall()
    
    basic_skills = [{"name": s["skill_name"], "level": s["level"]} for s in skills]

    # Get latest gap analysis (only if resume or interview exists)
    gap_data = None
    if has_resume or has_interview:
        gap_record = db.execute(
            "SELECT gap_data FROM skill_gap_analysis WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            [uid]
        ).fetchone()

        if gap_record:
            import json
            try:
                gap_data = json.loads(gap_record["gap_data"])
            except:
                gap_data = None

    return jsonify({
        "skills": basic_skills,
        "gap_analysis": gap_data,
        "has_resume": has_resume,
        "has_interview": has_interview,
        "target_role": target_role
    })


@skillgap_bp.post("/add-skill")
@require_auth
def add_skill():
    """Add a skill for the user"""
    uid = request.user["id"]
    data = request.get_json()
    
    skill_name = data.get("skill_name")
    level = data.get("level")
    
    if not skill_name or not level:
        return jsonify({"message": "Skill name and level are required"}), 400
    
    if level not in ["Beginner", "Intermediate", "Advanced"]:
        return jsonify({"message": "Invalid level. Must be Beginner, Intermediate, or Advanced"}), 400
    
    db = get_db()
    
    # Check if skill already exists
    existing = db.execute(
        "SELECT id FROM student_skills WHERE user_id = ? AND skill_name = ?",
        [uid, skill_name]
    ).fetchone()
    
    if existing:
        # Update existing skill
        db.execute(
            "UPDATE student_skills SET level = ? WHERE user_id = ? AND skill_name = ?",
            [level, uid, skill_name]
        )
        message = "Skill updated successfully"
    else:
        # Insert new skill
        db.execute(
            "INSERT INTO student_skills (user_id, skill_name, level) VALUES (?, ?, ?)",
            [uid, skill_name, level]
        )
        message = "Skill added successfully"
    
    db.commit()
    
    return jsonify({"message": message}), 200


@skillgap_bp.delete("/delete-skill")
@require_auth
def delete_skill():
    """Delete a skill"""
    uid = request.user["id"]
    data = request.get_json()
    
    skill_name = data.get("skill_name")
    
    if not skill_name:
        return jsonify({"message": "Skill name is required"}), 400
    
    db = get_db()
    db.execute(
        "DELETE FROM student_skills WHERE user_id = ? AND skill_name = ?",
        [uid, skill_name]
    )
    db.commit()
    
    return jsonify({"message": "Skill deleted successfully"}), 200
