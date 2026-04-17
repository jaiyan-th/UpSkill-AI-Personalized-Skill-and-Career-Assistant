from flask import Blueprint, request, jsonify
from app.services.recommend import recommend_careers, get_skill_gap, get_learning_path, market_insights, mentor_reply
from app.services.resume_generator import generate_resume
from app.services.ats_analyzer import ATSAnalyzer
from app.database import get_db

ai_bp = Blueprint("ai", __name__)
ats_analyzer = ATSAnalyzer()


@ai_bp.get("/career-recommend")
def career_recommend():
    user_id = int(request.args.get("user_id", 1))
    return jsonify(recommend_careers(user_id))


@ai_bp.get("/skill-gap-analysis")
def skill_gap_analysis():
    """Get skill gap analysis for a specific career"""
    user_id = int(request.args.get("user_id", 1))
    career_id = int(request.args.get("career_id", 1))
    return jsonify(get_skill_gap(user_id, career_id))


@ai_bp.get("/learning-path")
def learning_path():
    user_id = int(request.args.get("user_id", 1))
    career_id = int(request.args.get("career_id", 1))
    return jsonify(get_learning_path(user_id, career_id))


@ai_bp.get("/market-insights")
def get_market_insights():
    return jsonify(market_insights())


@ai_bp.post("/chat")
def chat():
    data = request.get_json() or {}
    return jsonify(mentor_reply(data.get("message", "")))


@ai_bp.post("/resume/generate")
def resume_generate():
    data = request.get_json() or {}
    required = ["name", "headline", "education", "skills", "projects", "experience"]
    if not all(data.get(f) for f in required):
        return jsonify({"message": "Missing required fields"}), 400
    try:
        result = generate_resume(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@ai_bp.post("/ats/analyze")
def ats_analyze():
    if "file" not in request.files:
        return jsonify({"message": "No file provided"}), 400

    file = request.files["file"]
    job_description = request.form.get("job_description", "")
    user_id = request.form.get("user_id")  # Optional: if user wants to save to profile
    auto_update_profile = request.form.get("auto_update_profile", "false").lower() == "true"

    allowed = [".pdf", ".docx", ".txt"]
    if not any(file.filename.lower().endswith(ext) for ext in allowed):
        return jsonify({"message": "Only PDF, DOCX, and TXT files are allowed"}), 400

    content = file.read()
    if len(content) == 0:
        return jsonify({"message": "File is empty"}), 400
    if len(content) > 10 * 1024 * 1024:
        return jsonify({"message": "File too large. Max 10MB"}), 400

    try:
        result = ats_analyzer.analyze_resume(file.filename, content, job_description)
        
        # Auto-update user profile if requested
        if auto_update_profile and user_id:
            try:
                _update_profile_from_ats(int(user_id), result["extracted_data"])
                result["profile_updated"] = True
                result["message"] = "Profile automatically updated with extracted skills"
            except Exception as e:
                result["profile_updated"] = False
                result["profile_update_error"] = str(e)
        
        # Generate personalized recommendations based on extracted skills
        if user_id:
            result["recommendations"] = _generate_recommendations_from_skills(
                result["extracted_data"]["skills"],
                result["missing_keywords"]
            )
        
        # Add ats_score field for frontend compatibility
        result["ats_score"] = result.get("score", 0)
        result["feedback"] = result.get("suggestions", ["Analysis complete!"])[0] if result.get("suggestions") else "Analysis complete!"
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"message": str(e)}), 500


def _update_profile_from_ats(user_id: int, extracted_data: dict):
    """Update user profile with skills extracted from resume"""
    db = get_db()
    
    # Update education level if extracted
    if extracted_data.get("education_level"):
        db.execute(
            """INSERT INTO profiles (user_id, education_level, updated_at)
               VALUES (?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(user_id) DO UPDATE SET
                   education_level=excluded.education_level,
                   updated_at=CURRENT_TIMESTAMP""",
            [user_id, extracted_data["education_level"]]
        )
    
    # Clear existing skills and add extracted ones
    db.execute("DELETE FROM student_skills WHERE user_id = ?", [user_id])
    
    for skill in extracted_data.get("skills", []):
        db.execute(
            "INSERT INTO student_skills (user_id, skill_name, level) VALUES (?, ?, ?)",
            [user_id, skill["name"], skill["level"]]
        )
    
    db.commit()


def _generate_recommendations_from_skills(skills: list, missing_keywords: list) -> dict:
    """Generate career recommendations based on extracted skills"""
    skill_names = {s["name"].lower() for s in skills}
    
    # Career matching logic
    career_matches = []
    
    # AI Engineer match
    ai_skills = {"python", "machine learning", "ai", "tensorflow", "pytorch", "data"}
    ai_match = len(skill_names & ai_skills)
    if ai_match > 0:
        career_matches.append({
            "career": "AI Engineer",
            "match_score": min(ai_match * 20 + 50, 95),
            "matched_skills": list(skill_names & ai_skills),
            "missing_skills": ["Machine Learning", "Deep Learning", "Neural Networks"][:3-ai_match] if ai_match < 3 else []
        })
    
    # Data Analyst match
    data_skills = {"sql", "python", "excel", "tableau", "power bi", "data", "pandas"}
    data_match = len(skill_names & data_skills)
    if data_match > 0:
        career_matches.append({
            "career": "Data Analyst",
            "match_score": min(data_match * 18 + 45, 90),
            "matched_skills": list(skill_names & data_skills),
            "missing_skills": ["SQL", "Data Visualization", "Statistics"][:3-data_match] if data_match < 3 else []
        })
    
    # UI/UX Designer match
    design_skills = {"figma", "sketch", "adobe xd", "photoshop", "illustrator", "ui", "ux"}
    design_match = len(skill_names & design_skills)
    if design_match > 0:
        career_matches.append({
            "career": "UI/UX Designer",
            "match_score": min(design_match * 20 + 40, 85),
            "matched_skills": list(skill_names & design_skills),
            "missing_skills": ["User Research", "Wireframing", "Prototyping"][:3-design_match] if design_match < 3 else []
        })
    
    # Web Developer match
    web_skills = {"javascript", "react", "html", "css", "node", "typescript", "vue", "angular"}
    web_match = len(skill_names & web_skills)
    if web_match > 0:
        career_matches.append({
            "career": "Web Developer",
            "match_score": min(web_match * 15 + 50, 90),
            "matched_skills": list(skill_names & web_skills),
            "missing_skills": ["React", "Node.js", "REST APIs"][:3-web_match] if web_match < 3 else []
        })
    
    # Sort by match score
    career_matches.sort(key=lambda x: x["match_score"], reverse=True)
    
    # Generate learning recommendations based on missing keywords
    learning_recommendations = []
    priority_skills = missing_keywords[:5] if missing_keywords else []
    
    for skill in priority_skills:
        learning_recommendations.append({
            "skill": skill.title(),
            "priority": "High",
            "reason": "Required by target job description",
            "estimated_time": "2-4 weeks"
        })
    
    return {
        "top_careers": career_matches[:3],
        "learning_recommendations": learning_recommendations,
        "overall_readiness": _calculate_readiness(len(skills), missing_keywords)
    }


def _calculate_readiness(skills_count: int, missing_keywords: list) -> dict:
    """Calculate overall job readiness score"""
    base_score = min(skills_count * 5, 70)
    penalty = len(missing_keywords) * 2
    final_score = max(base_score - penalty, 0)
    
    if final_score >= 80:
        status = "Excellent"
        message = "You're well-prepared for your target roles!"
    elif final_score >= 60:
        status = "Good"
        message = "You're on the right track. Focus on filling key skill gaps."
    elif final_score >= 40:
        status = "Fair"
        message = "Build more skills to improve your competitiveness."
    else:
        status = "Needs Improvement"
        message = "Focus on developing core skills for your target career."
    
    return {
        "score": final_score,
        "status": status,
        "message": message
    }
