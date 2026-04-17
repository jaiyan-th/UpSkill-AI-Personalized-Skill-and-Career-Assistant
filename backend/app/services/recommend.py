from flask import g
from app.database import get_db
from typing import List, Dict, Optional


def recommend_careers(user_id: int) -> dict:
    """
    Generate personalized career recommendations based on user's actual skills
    """
    db = get_db()
    
    # Get user's skills from database
    user_skills = db.execute(
        "SELECT skill_name, level FROM student_skills WHERE user_id = ?",
        [user_id]
    ).fetchall()
    
    # Convert to dict for easier lookup
    user_skill_dict = {row["skill_name"].lower(): row["level"] for row in user_skills}
    
    # Get all careers from database
    careers = db.execute(
        "SELECT id, title, description, match_score, demand_score, salary_range, job_outlook FROM careers"
    ).fetchall()
    
    recommendations = []
    
    for career in careers:
        # Get required skills for this career
        required_skills = db.execute(
            "SELECT skill_name, required_level FROM career_skill_map WHERE career_id = ?",
            [career["id"]]
        ).fetchall()
        
        # Calculate match score based on user's skills
        if required_skills:
            matched_skills = 0
            total_skills = len(required_skills)
            
            for req_skill in required_skills:
                skill_name = req_skill["skill_name"].lower()
                if skill_name in user_skill_dict:
                    # User has this skill - check level
                    user_level = user_skill_dict[skill_name]
                    required_level = req_skill["required_level"]
                    
                    # Level scoring: Beginner=1, Intermediate=2, Advanced=3
                    level_map = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
                    user_level_score = level_map.get(user_level, 0)
                    required_level_score = level_map.get(required_level, 0)
                    
                    if user_level_score >= required_level_score:
                        matched_skills += 1
                    elif user_level_score > 0:
                        matched_skills += 0.5  # Partial credit
            
            # Calculate percentage match
            calculated_match_score = int((matched_skills / total_skills) * 100) if total_skills > 0 else 0
        else:
            # No required skills defined, use default score
            calculated_match_score = career["match_score"]
        
        recommendations.append({
            "id": career["id"],
            "title": career["title"],
            "description": career["description"],
            "matchScore": calculated_match_score,
            "skills": [rs["skill_name"] for rs in required_skills],
            "salaryRange": career["salary_range"],
            "jobOutlook": career["job_outlook"],
            "demandScore": career["demand_score"]
        })
    
    # Sort by match score (highest first)
    recommendations.sort(key=lambda x: x["matchScore"], reverse=True)
    
    return {"userId": user_id, "recommendations": recommendations}


def get_skill_gap(user_id: int, career_id: int) -> dict:
    """
    Calculate actual skill gaps between user's current skills and career requirements
    """
    db = get_db()
    
    # Get user's current skills
    user_skills = db.execute(
        "SELECT skill_name, level FROM student_skills WHERE user_id = ?",
        [user_id]
    ).fetchall()
    
    user_skill_dict = {row["skill_name"].lower(): row["level"] for row in user_skills}
    
    # Get required skills for the career
    required_skills = db.execute(
        "SELECT skill_name, required_level FROM career_skill_map WHERE career_id = ?",
        [career_id]
    ).fetchall()
    
    # Level scoring
    level_map = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
    level_percentage = {"Beginner": 33, "Intermediate": 66, "Advanced": 100}
    
    skill_gaps = []
    acquired = 0
    
    for req_skill in required_skills:
        skill_name = req_skill["skill_name"]
        required_level = req_skill["required_level"]
        target_score = level_percentage.get(required_level, 100)
        
        if skill_name.lower() in user_skill_dict:
            # User has this skill
            user_level = user_skill_dict[skill_name.lower()]
            current_score = level_percentage.get(user_level, 0)
            
            user_level_num = level_map.get(user_level, 0)
            required_level_num = level_map.get(required_level, 0)
            
            if user_level_num >= required_level_num:
                status = "Acquired"
                acquired += 1
            else:
                status = "Needs Work"
            
            skill_gaps.append({
                "skill": skill_name,
                "current": current_score,
                "target": target_score,
                "status": status
            })
        else:
            # User doesn't have this skill
            skill_gaps.append({
                "skill": skill_name,
                "current": 0,
                "target": target_score,
                "status": "Missing"
            })
    
    return {
        "userId": user_id,
        "careerId": career_id,
        "skills": skill_gaps,
        "acquired": acquired,
        "missing": len(skill_gaps) - acquired
    }


def get_learning_path(user_id: int, career_id: int) -> dict:
    """
    Generate personalized learning path based on user's skill gaps
    """
    db = get_db()
    
    # Get skill gaps
    skill_gap_data = get_skill_gap(user_id, career_id)
    
    # Get career info
    career = db.execute(
        "SELECT title FROM careers WHERE id = ?",
        [career_id]
    ).fetchone()
    
    career_title = career["title"] if career else "Unknown Career"
    
    # Create learning path based on missing/weak skills
    learning_path = []
    path_id = 1
    
    # Prioritize missing skills first, then skills that need work
    missing_skills = [s for s in skill_gap_data["skills"] if s["status"] == "Missing"]
    needs_work_skills = [s for s in skill_gap_data["skills"] if s["status"] == "Needs Work"]
    
    # Learning resources mapping
    resource_map = {
        "python": {
            "title": "Python Programming Mastery",
            "provider": "FreeCodeCamp",
            "duration": "3 weeks",
            "resources": ["Syntax & Basics", "Data Structures", "OOP Concepts"]
        },
        "machine learning": {
            "title": "Machine Learning Fundamentals",
            "provider": "Kaggle Learn",
            "duration": "4 weeks",
            "resources": ["Supervised Learning", "Model Training", "Evaluation Metrics"]
        },
        "sql": {
            "title": "SQL Database Mastery",
            "provider": "SQLBolt",
            "duration": "2 weeks",
            "resources": ["Queries", "Joins", "Optimization"]
        },
        "javascript": {
            "title": "Modern JavaScript",
            "provider": "JavaScript.info",
            "duration": "3 weeks",
            "resources": ["ES6+", "Async/Await", "DOM Manipulation"]
        },
        "react": {
            "title": "React Development",
            "provider": "React.dev",
            "duration": "3 weeks",
            "resources": ["Components", "Hooks", "State Management"]
        },
        "figma": {
            "title": "UI/UX Design with Figma",
            "provider": "Figma Learn",
            "duration": "2 weeks",
            "resources": ["Interface Design", "Prototyping", "Components"]
        },
        "data structures": {
            "title": "Data Structures & Algorithms",
            "provider": "GeeksforGeeks",
            "duration": "4 weeks",
            "resources": ["Arrays & Lists", "Trees & Graphs", "Sorting Algorithms"]
        },
        "statistics": {
            "title": "Statistics for Data Science",
            "provider": "Khan Academy",
            "duration": "3 weeks",
            "resources": ["Probability", "Distributions", "Hypothesis Testing"]
        },
        "networking": {
            "title": "Computer Networking Basics",
            "provider": "Cisco NetAcad",
            "duration": "3 weeks",
            "resources": ["TCP/IP", "Protocols", "Security"]
        },
        "linux": {
            "title": "Linux System Administration",
            "provider": "Linux Journey",
            "duration": "2 weeks",
            "resources": ["Command Line", "File Systems", "Permissions"]
        }
    }
    
    # Add courses for missing skills (highest priority)
    for skill in missing_skills[:3]:  # Top 3 missing skills
        skill_lower = skill["skill"].lower()
        resource = resource_map.get(skill_lower, {
            "title": f"Learn {skill['skill']}",
            "provider": "Online Platform",
            "duration": "2-3 weeks",
            "resources": ["Fundamentals", "Practice", "Projects"]
        })
        
        learning_path.append({
            "id": path_id,
            "title": resource["title"],
            "provider": resource["provider"],
            "duration": resource["duration"],
            "resources": resource["resources"],
            "completed": False,
            "priority": "High"
        })
        path_id += 1
    
    # Add courses for skills that need improvement
    for skill in needs_work_skills[:2]:  # Top 2 skills needing work
        skill_lower = skill["skill"].lower()
        resource = resource_map.get(skill_lower, {
            "title": f"Advanced {skill['skill']}",
            "provider": "Online Platform",
            "duration": "2 weeks",
            "resources": ["Advanced Topics", "Best Practices", "Real Projects"]
        })
        
        learning_path.append({
            "id": path_id,
            "title": resource["title"],
            "provider": resource["provider"],
            "duration": resource["duration"],
            "resources": resource["resources"],
            "completed": False,
            "priority": "Medium"
        })
        path_id += 1
    
    # Add a capstone project
    learning_path.append({
        "id": path_id,
        "title": f"{career_title} Capstone Project",
        "provider": "Self-Guided",
        "duration": "2-3 weeks",
        "resources": ["Project Planning", "Implementation", "Portfolio Presentation"],
        "completed": False,
        "priority": "High"
    })
    
    # Calculate estimated completion time
    total_weeks = sum(
        int(course["duration"].split()[0].split("-")[0]) 
        for course in learning_path
    )
    
    return {
        "userId": user_id,
        "careerId": career_id,
        "careerTitle": career_title,
        "path": learning_path,
        "estimatedCompletion": f"{total_weeks} weeks"
    }


def market_insights() -> dict:
    """
    Get market insights from database and generate trending data
    """
    db = get_db()
    
    # Get all careers for salary cards
    careers = db.execute(
        "SELECT title, description, salary_range, job_outlook, demand_score FROM careers ORDER BY demand_score DESC"
    ).fetchall()
    
    salary_cards = [
        {
            "title": c["title"],
            "description": c["description"],
            "salaryRange": c["salary_range"],
            "jobOutlook": c["job_outlook"],
            "demandScore": c["demand_score"]
        }
        for c in careers
    ]
    
    # Get trending skills from career requirements
    skill_demand = {}
    all_skills = db.execute(
        "SELECT skill_name, COUNT(*) as count FROM career_skill_map GROUP BY skill_name ORDER BY count DESC LIMIT 10"
    ).fetchall()
    
    trending_skills = []
    for skill in all_skills:
        # Calculate demand score based on how many careers require it
        demand = min(skill["count"] * 25 + 60, 100)
        trending_skills.append({
            "skill": skill["skill_name"],
            "demand": demand
        })
    
    # Market ticker
    ticker = [
        f"{careers[0]['title']} demand up {careers[0]['demand_score']}%" if careers else "Tech jobs growing",
        "AI and ML skills in high demand",
        "Remote work opportunities increasing",
        "Full-stack developers highly sought after",
    ]
    
    # Future jobs prediction
    future_jobs = [
        {"role": "AI Ethics Specialist", "growth": 85},
        {"role": "Quantum Computing Engineer", "growth": 78},
        {"role": "Blockchain Developer", "growth": 72},
        {"role": "AR/VR Experience Designer", "growth": 68},
        {"role": "Data Privacy Officer", "growth": 65},
    ]
    
    return {
        "ticker": ticker,
        "trendingSkills": trending_skills,
        "salaryCards": salary_cards,
        "futureJobs": future_jobs
    }


def mentor_reply(message: str) -> dict:
    """
    AI mentor chatbot with Groq LLM integration
    """
    from app.services.groq_client import groq_generate
    
    # Try Groq first
    try:
        reply = groq_generate(
            f"You are a career mentor for students. Answer this question concisely and practically: {message}",
            system="You are a helpful career mentor specializing in tech careers and skill development. Be encouraging, practical, and concise. Focus on actionable advice.",
            max_tokens=300,
        )
        if reply:
            return {"reply": reply}
    except Exception as e:
        print(f"Groq API error: {e}")
    
    # Fallback to rule-based responses
    msg = message.lower()
    
    if any(word in msg for word in ["skill gap", "skills", "learn", "improve"]):
        answer = "Focus on building skills that match your target career. Start with fundamentals, practice through projects, and track your progress. Prioritize skills marked as 'Missing' or 'Needs Work' in your skill gap analysis."
    elif any(word in msg for word in ["resume", "cv", "ats"]):
        answer = "Make your resume ATS-friendly: use clear section headers, include relevant keywords from job descriptions, quantify achievements, and use action verbs. Keep formatting simple and avoid images or complex layouts."
    elif any(word in msg for word in ["career", "job", "role", "path"]):
        answer = "Choose a career that aligns with your interests and strengths. Review your career match scores, focus on roles with high demand, and build the required skills systematically. Start with your top match and work towards it."
    elif any(word in msg for word in ["interview", "preparation"]):
        answer = "Prepare for interviews by: reviewing common questions for your role, practicing coding problems (if technical), preparing STAR method examples, researching the company, and preparing thoughtful questions to ask."
    elif any(word in msg for word in ["project", "portfolio"]):
        answer = "Build 2-3 strong projects that demonstrate your skills. Choose projects relevant to your target role, document them well on GitHub, and be ready to explain your design decisions and challenges faced."
    else:
        answer = "I'm here to help with career guidance, skill development, resume tips, interview prep, and learning paths. What specific aspect would you like to discuss?"
    
    return {"reply": answer}
