from flask import Blueprint, request, jsonify
from app.database import get_db
from app.auth_utils import require_auth
from app.services.recommend import recommend_careers, get_skill_gap, get_learning_path, market_insights

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/")
@require_auth
def dashboard():
    uid = request.user["id"]
    db = get_db()

    # Get user profile
    profile = db.execute("SELECT * FROM profiles WHERE user_id = ?", [uid]).fetchone()
    
    # Get user's skills
    user_skills = db.execute("SELECT * FROM student_skills WHERE user_id = ?", [uid]).fetchall()
    
    # Get user's interests
    user_interests = db.execute("SELECT * FROM student_interests WHERE user_id = ?", [uid]).fetchall()
    
    # Get resume count
    resume_count = db.execute("SELECT COUNT(*) as count FROM resumes WHERE user_id = ?", [uid]).fetchone()['count']
    
    # Get recent progress
    recent_progress = db.execute(
        "SELECT * FROM progress_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT 6", [uid]
    ).fetchall()

    # Only calculate recommendations if user has skills
    recommended_careers = []
    readiness_score = None
    skill_gap_data = None
    learning_path_data = None
    
    if user_skills:
        # User has skills - calculate personalized recommendations
        career_recs = recommend_careers(uid)
        recommended_careers = career_recs["recommendations"][:4]  # Top 4
        
        # Calculate readiness score based on user's skills
        if recommended_careers:
            top_career_id = recommended_careers[0]["id"]
            skill_gap_data = get_skill_gap(uid, top_career_id)
            
            # Calculate readiness: (acquired skills / total skills) * 100
            if skill_gap_data["skills"]:
                total_skills = len(skill_gap_data["skills"])
                acquired_skills = skill_gap_data["acquired"]
                readiness_score = int((acquired_skills / total_skills) * 100) if total_skills > 0 else 0
            
            # Get learning path for top career
            learning_path_data = get_learning_path(uid, top_career_id)

    return jsonify({
        "success": True,
        "data": {
            "user": {
                "name": request.user["name"],
                "email": request.user["email"],
                "hasProfile": profile is not None,
                "hasSkills": len(user_skills) > 0,
                "hasInterests": len(user_interests) > 0,
                "skillCount": len(user_skills),
                "interestCount": len(user_interests),
                "resumeCount": resume_count
            },
            "readinessScore": readiness_score,
            "recommendedCareers": recommended_careers,
            "skillGap": skill_gap_data,
            "nextLearningStep": learning_path_data["path"][0] if learning_path_data and learning_path_data.get("path") else None,
            "recentProgress": [dict(p) for p in recent_progress],
        }
    })
