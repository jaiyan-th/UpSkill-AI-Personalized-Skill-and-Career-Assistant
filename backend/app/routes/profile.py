from flask import Blueprint, request, jsonify
from app.database import get_db
from app.auth_utils import require_auth

profile_bp = Blueprint("profile", __name__)


@profile_bp.post("/")
@require_auth
def save_profile():
    data = request.get_json()
    uid = request.user["id"]
    db = get_db()

    db.execute(
        """INSERT INTO profiles (user_id, education_level, preferred_field, goals, learning_pace, language_preference)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(user_id) DO UPDATE SET
               education_level=excluded.education_level,
               preferred_field=excluded.preferred_field,
               goals=excluded.goals,
               learning_pace=excluded.learning_pace,
               language_preference=excluded.language_preference,
               updated_at=CURRENT_TIMESTAMP""",
        [uid, data.get("education_level"), data.get("preferred_field"),
         data.get("goals"), data.get("learning_pace"), data.get("language_preference")],
    )

    db.execute("DELETE FROM student_interests WHERE user_id = ?", [uid])
    for interest in data.get("interests", []):
        db.execute("INSERT INTO student_interests (user_id, interest) VALUES (?, ?)", [uid, interest])

    db.execute("DELETE FROM student_skills WHERE user_id = ?", [uid])
    for skill in data.get("skills", []):
        db.execute(
            "INSERT INTO student_skills (user_id, skill_name, level) VALUES (?, ?, ?)",
            [uid, skill.get("name"), skill.get("level")],
        )

    db.commit()
    return jsonify({"message": "Profile saved successfully"})


@profile_bp.get("/me")
@require_auth
def get_profile():
    uid = request.user["id"]
    db = get_db()
    profile = db.execute("SELECT * FROM profiles WHERE user_id = ?", [uid]).fetchone()
    interests = db.execute("SELECT interest FROM student_interests WHERE user_id = ?", [uid]).fetchall()
    skills = db.execute(
        "SELECT skill_name AS name, level FROM student_skills WHERE user_id = ?", [uid]
    ).fetchall()
    return jsonify({
        **(dict(profile) if profile else {}),
        "interests": [r["interest"] for r in interests],
        "skills": [dict(r) for r in skills],
    })


@profile_bp.post("/skills")
@require_auth
def add_skill():
    """Add a single skill to user profile"""
    data = request.get_json()
    uid = request.user["id"]
    db = get_db()
    
    skill_name = data.get("skill_name")
    level = data.get("level", "Beginner")
    
    if not skill_name:
        return jsonify({"message": "skill_name is required"}), 400
    
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
    else:
        # Insert new skill
        db.execute(
            "INSERT INTO student_skills (user_id, skill_name, level) VALUES (?, ?, ?)",
            [uid, skill_name, level]
        )
    
    db.commit()
    return jsonify({"message": "Skill added successfully", "skill": {"name": skill_name, "level": level}})


@profile_bp.delete("/skills/<skill_name>")
@require_auth
def delete_skill(skill_name):
    """Delete a skill from user profile"""
    uid = request.user["id"]
    db = get_db()
    
    db.execute(
        "DELETE FROM student_skills WHERE user_id = ? AND skill_name = ?",
        [uid, skill_name]
    )
    db.commit()
    
    return jsonify({"message": "Skill deleted successfully"})
