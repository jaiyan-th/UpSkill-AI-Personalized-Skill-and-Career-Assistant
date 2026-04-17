"""
Skill Gap Analysis Routes V2 - Production-Ready
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
    LLMError,
    DatabaseError
)
from app.validators import validate_request
from app.services.llm_service_v2 import LLMServiceV2
import json

skill_gap_v2_bp = Blueprint('skill_gap_v2', __name__, url_prefix='/api/ai/skills')

# Initialize LLM service
llm = LLMServiceV2()


# Validation schemas
SKILL_GAP_SCHEMA = {
    "current_skills": {"type": "string", "required": True, "min_length": 2},
    "target_role": {"type": "string", "required": True, "min_length": 2, "max_length": 100},
    "experience_level": {"type": "enum", "required": True, "allowed_values": ["Entry", "Mid-level", "Senior"]}
}

LEARNING_PATH_SCHEMA = {
    "current_skills": {"type": "string", "required": True, "min_length": 2},
    "target_role": {"type": "string", "required": True, "min_length": 2, "max_length": 100},
    "hours_per_week": {"type": "integer", "required": False, "min_val": 1, "max_val": 168}
}


@skill_gap_v2_bp.post('/analyze-gaps')
@require_auth
@validate_request(SKILL_GAP_SCHEMA)
def analyze_skill_gaps():
    """
    Analyze skill gaps for target role
    
    Request Body:
        {
            "current_skills": "Python, JavaScript, React" (required),
            "target_role": "Full Stack Developer" (required),
            "experience_level": "Entry|Mid-level|Senior" (required)
        }
    
    Returns:
        200: {
            success: true,
            data: {
                strong_skills, missing_skills, weak_skills,
                readiness_score, analysis_summary
            },
            message
        }
    """
    try:
        data = request.validated_data
        user_id = request.user['id']
        
        current_skills = data["current_skills"]
        target_role = data["target_role"]
        experience_level = data["experience_level"]
        
        # Check if user has resume and interview data for enhanced analysis
        db = get_db()
        
        resume = db.execute(
            "SELECT id, analysis_data FROM resumes WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT 1",
            [user_id]
        ).fetchone()
        
        interview = db.execute(
            """SELECT id, evaluation_data FROM interview_sessions 
               WHERE user_id = ? AND status = 'completed' 
               ORDER BY ended_at DESC LIMIT 1""",
            [user_id]
        ).fetchone()
        
        # Build context for LLM
        context = f"Current Skills: {current_skills}\n"
        
        if resume:
            context += "Resume data available for analysis.\n"
        
        if interview:
            context += "Interview performance data available.\n"
        
        # Analyze skill gaps using LLM
        try:
            system_prompt = f"""You are an expert career coach analyzing skill gaps for {target_role} at {experience_level} level.

Provide comprehensive, actionable analysis."""

            prompt = f"""Analyze skill gaps for this candidate:

{context}
Target Role: {target_role}
Experience Level: {experience_level}

Provide JSON with:
1. "strong_skills": Array of skills the candidate has (with proficiency)
2. "missing_skills": Critical skills needed for the role (prioritized)
3. "weak_skills": Skills that need improvement
4. "readiness_score": Overall readiness (0-100)
5. "analysis_summary": 2-3 sentence summary
6. "recommended_focus": Top 3 skills to focus on
7. "estimated_time_to_ready": Estimated months to become job-ready

Be specific and actionable. Consider the experience level.

Return ONLY valid JSON, no other text."""

            response = llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.4,
                json_mode=True,
                retries=3
            )
            
            analysis = llm.parse_json_response(
                response,
                fallback={
                    "strong_skills": current_skills.split(',')[:3],
                    "missing_skills": ["Advanced technical skills", "System design", "Leadership"],
                    "weak_skills": [],
                    "readiness_score": 60,
                    "analysis_summary": "You have a good foundation. Focus on building advanced skills.",
                    "recommended_focus": ["System Design", "Advanced Algorithms", "Cloud Technologies"],
                    "estimated_time_to_ready": 6
                }
            )
            
        except LLMError:
            # Provide fallback analysis
            skills_list = [s.strip() for s in current_skills.split(',')]
            analysis = {
                "strong_skills": skills_list[:min(3, len(skills_list))],
                "missing_skills": [
                    "Advanced technical concepts",
                    "System design and architecture",
                    "Leadership and communication"
                ],
                "weak_skills": [],
                "readiness_score": 65,
                "analysis_summary": f"You have foundational skills for {target_role}. Focus on building advanced technical expertise and soft skills.",
                "recommended_focus": [
                    "System Design",
                    "Advanced Programming Concepts",
                    "Communication Skills"
                ],
                "estimated_time_to_ready": 6
            }
        
        # Save analysis to database
        try:
            cursor = db.execute(
                """INSERT INTO skill_gap_analysis 
                   (user_id, target_role, target_level, readiness_score, analysis_data, created_at)
                   VALUES (?, ?, ?, ?, ?, datetime('now'))""",
                [
                    user_id,
                    target_role,
                    experience_level,
                    analysis.get("readiness_score", 0),
                    json.dumps(analysis)
                ]
            )
            db.commit()
            
            analysis['analysis_id'] = cursor.lastrowid
            
        except Exception as e:
            # Don't fail if save fails
            print(f"Warning: Failed to save analysis: {e}")
        
        return success_response(
            data=analysis,
            message="Skill gap analysis complete"
        )
        
    except (ValidationError, LLMError):
        raise
    except Exception as e:
        raise BusinessLogicError(f"Skill gap analysis failed: {str(e)}")


@skill_gap_v2_bp.post('/learning-path')
@require_auth
@validate_request(LEARNING_PATH_SCHEMA)
def generate_learning_path():
    """
    Generate personalized learning path
    
    Request Body:
        {
            "current_skills": "Python, JavaScript" (required),
            "target_role": "Full Stack Developer" (required),
            "hours_per_week": 10 (optional, default: 10)
        }
    
    Returns:
        200: {
            success: true,
            data: {
                phases, total_duration_weeks, next_steps,
                resources
            },
            message
        }
    """
    try:
        data = request.validated_data
        user_id = request.user['id']
        
        current_skills = data["current_skills"]
        target_role = data["target_role"]
        
        # Get hours_per_week from full request data (not validated)
        full_data = request.get_json() or {}
        hours_per_week = full_data.get("hours_per_week", 10)
        
        # Validate hours_per_week manually
        try:
            hours_per_week = int(hours_per_week)
            if hours_per_week < 1 or hours_per_week > 168:
                hours_per_week = 10
        except:
            hours_per_week = 10
        
        # Generate learning path using LLM
        try:
            system_prompt = f"""You are an expert learning path designer for {target_role}.

Create structured, achievable learning paths with realistic timelines."""

            prompt = f"""Create a personalized learning path:

Current Skills: {current_skills}
Target Role: {target_role}
Available Time: {hours_per_week} hours/week

Provide JSON with:
1. "phases": Array of learning phases, each with:
   - "phase_number": 1, 2, 3...
   - "title": Phase name
   - "duration_weeks": Estimated weeks
   - "skills_to_learn": Array of skills
   - "resources": Recommended resources
   - "milestones": What to achieve

2. "total_duration_weeks": Total estimated weeks
3. "next_steps": Immediate actions to take (top 3)
4. "estimated_hours": Total estimated hours
5. "difficulty_level": "Beginner", "Intermediate", or "Advanced"

Be realistic with timelines based on {hours_per_week} hours/week.

Return ONLY valid JSON, no other text."""

            response = llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.5,
                json_mode=True,
                retries=3
            )
            
            learning_path = llm.parse_json_response(
                response,
                fallback={
                    "phases": [
                        {
                            "phase_number": 1,
                            "title": "Foundation Building",
                            "duration_weeks": 4,
                            "skills_to_learn": ["Core concepts", "Best practices"],
                            "resources": ["Online courses", "Documentation"],
                            "milestones": ["Complete basic projects"]
                        }
                    ],
                    "total_duration_weeks": 12,
                    "next_steps": [
                        "Start with online tutorials",
                        "Build small projects",
                        "Join developer communities"
                    ],
                    "estimated_hours": hours_per_week * 12,
                    "difficulty_level": "Intermediate"
                }
            )
            
        except LLMError:
            # Provide fallback learning path
            learning_path = {
                "phases": [
                    {
                        "phase_number": 1,
                        "title": "Foundation Building",
                        "duration_weeks": 4,
                        "skills_to_learn": ["Core programming concepts", "Version control (Git)"],
                        "resources": ["freeCodeCamp", "Codecademy", "GitHub Learning Lab"],
                        "milestones": ["Complete 5 coding challenges", "Create GitHub portfolio"]
                    },
                    {
                        "phase_number": 2,
                        "title": "Intermediate Skills",
                        "duration_weeks": 6,
                        "skills_to_learn": ["Advanced frameworks", "Database design", "API development"],
                        "resources": ["Udemy courses", "Official documentation", "YouTube tutorials"],
                        "milestones": ["Build 2 full-stack projects", "Deploy to cloud"]
                    },
                    {
                        "phase_number": 3,
                        "title": "Advanced & Job Prep",
                        "duration_weeks": 4,
                        "skills_to_learn": ["System design", "Testing", "DevOps basics"],
                        "resources": ["System Design Primer", "LeetCode", "Mock interviews"],
                        "milestones": ["Complete portfolio", "Pass technical interviews"]
                    }
                ],
                "total_duration_weeks": 14,
                "next_steps": [
                    "Enroll in a structured online course",
                    "Set up development environment",
                    "Start building a portfolio project"
                ],
                "estimated_hours": hours_per_week * 14,
                "difficulty_level": "Intermediate"
            }
        
        # Save learning path to database
        try:
            db = get_db()
            cursor = db.execute(
                """INSERT INTO learning_paths 
                   (user_id, target_role, status, estimated_hours, path_data, created_at)
                   VALUES (?, ?, 'not_started', ?, ?, datetime('now'))""",
                [
                    user_id,
                    target_role,
                    learning_path.get("estimated_hours", 0),
                    json.dumps(learning_path)
                ]
            )
            db.commit()
            
            learning_path['path_id'] = cursor.lastrowid
            
        except Exception as e:
            print(f"Warning: Failed to save learning path: {e}")
        
        return success_response(
            data=learning_path,
            message="Learning path generated successfully"
        )
        
    except (ValidationError, LLMError):
        raise
    except Exception as e:
        raise BusinessLogicError(f"Learning path generation failed: {str(e)}")


@skill_gap_v2_bp.post('/assess-readiness')
@require_auth
def assess_readiness():
    """
    Assess job readiness for target role
    
    Request Body:
        {
            "current_skills": "Python, React, SQL" (required),
            "target_role": "Full Stack Developer" (required)
        }
    
    Returns:
        200: {
            success: true,
            data: {
                readiness_score, readiness_level, gaps,
                recommendations, timeline
            },
            message
        }
    """
    try:
        data = request.get_json() or {}
        user_id = request.user['id']
        
        # Validate inputs
        current_skills = data.get("current_skills", "").strip()
        target_role = data.get("target_role", "").strip()
        
        if not current_skills:
            raise ValidationError("Current skills are required", field="current_skills")
        
        if not target_role:
            raise ValidationError("Target role is required", field="target_role")
        
        # Assess readiness using LLM
        try:
            system_prompt = f"""You are an expert career assessor evaluating job readiness for {target_role}.

Provide honest, actionable assessment."""

            prompt = f"""Assess job readiness:

Current Skills: {current_skills}
Target Role: {target_role}

Provide JSON with:
1. "readiness_score": 0-100 score
2. "readiness_level": "Not Ready", "Partially Ready", "Job Ready", or "Highly Qualified"
3. "critical_gaps": Skills absolutely needed
4. "nice_to_have": Skills that would help
5. "recommendations": Top 3 actions to take
6. "estimated_months_to_ready": Months needed to become job-ready
7. "confidence_level": "Low", "Medium", or "High"

Be realistic and constructive.

Return ONLY valid JSON, no other text."""

            response = llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                json_mode=True,
                retries=3
            )
            
            assessment = llm.parse_json_response(
                response,
                fallback={
                    "readiness_score": 60,
                    "readiness_level": "Partially Ready",
                    "critical_gaps": ["System design", "Advanced algorithms"],
                    "nice_to_have": ["Cloud platforms", "CI/CD"],
                    "recommendations": [
                        "Build more complex projects",
                        "Study system design",
                        "Practice coding interviews"
                    ],
                    "estimated_months_to_ready": 4,
                    "confidence_level": "Medium"
                }
            )
            
        except LLMError:
            # Provide fallback assessment
            assessment = {
                "readiness_score": 65,
                "readiness_level": "Partially Ready",
                "critical_gaps": [
                    "Advanced technical skills",
                    "System design knowledge",
                    "Production experience"
                ],
                "nice_to_have": [
                    "Cloud platform experience",
                    "DevOps knowledge",
                    "Open source contributions"
                ],
                "recommendations": [
                    "Build 2-3 substantial portfolio projects",
                    "Study system design fundamentals",
                    "Practice technical interview questions"
                ],
                "estimated_months_to_ready": 4,
                "confidence_level": "Medium"
            }
        
        return success_response(
            data=assessment,
            message="Readiness assessment complete"
        )
        
    except ValidationError:
        raise
    except Exception as e:
        raise BusinessLogicError(f"Readiness assessment failed: {str(e)}")
