from flask import Blueprint, jsonify, request
from app.database import get_db
from app.auth_utils import require_auth
from app.services.recommend import recommend_careers

careers_bp = Blueprint("careers", __name__)


@careers_bp.get("/")
@require_auth
def list_careers():
    uid = request.user["id"]
    
    # Get personalized career recommendations based on user's skills
    career_data = recommend_careers(uid)
    
    # Format for frontend (matching expected structure)
    careers = [
        {
            "id": career["id"],
            "title": career["title"],
            "description": career["description"],
            "match_score": career["matchScore"],
            "salary_range": career["salaryRange"],
            "job_outlook": career["jobOutlook"],
            "demand_score": career["demandScore"],
            "skills": career["skills"]
        }
        for career in career_data["recommendations"]
    ]
    
    return jsonify({"careers": careers})


@careers_bp.get("/<int:career_id>")
@require_auth
def get_career(career_id):
    db = get_db()
    career = db.execute("SELECT * FROM careers WHERE id = ?", [career_id]).fetchone()
    if not career:
        return jsonify({"message": "Not found"}), 404
    skills = db.execute(
        "SELECT skill_name, required_level FROM career_skill_map WHERE career_id = ?", [career_id]
    ).fetchall()
    return jsonify({**dict(career), "requiredSkills": [dict(s) for s in skills]})
