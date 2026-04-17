"""
AI Routes - Resume Analysis and Career Recommendations
Refactored with structured responses, validation, and error handling
"""

from flask import Blueprint, request
from app.auth_utils import require_auth
from app.database import get_db
from app.error_handlers import success_response, error_response
from app.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    LLMError,
    DatabaseError
)
from app.validators import Validator
from app.services.ats_analyzer import ATSAnalyzer
from app.services.llm_service_v2 import LLMServiceV2
import PyPDF2
from io import BytesIO
import json

ai_routes_bp = Blueprint("ai_routes", __name__, url_prefix="/api/ai")

# Initialize services
ats_analyzer = ATSAnalyzer()
llm = LLMServiceV2()


@ai_routes_bp.post("/resume/upload")
@require_auth
def upload_resume():
    """
    Upload and analyze resume
    
    Form Data:
        - resume: PDF file (required, max 10MB)
        - job_description: string (optional)
    
    Returns:
        200: { success: true, data: { analysis, extracted_data }, message }
        400: { success: false, error: { code, message } }
    """
    try:
        # Validate file upload
        if "resume" not in request.files:
            raise ValidationError("Resume file is required", field="resume")
        
        file = request.files["resume"]
        
        if not file.filename:
            raise ValidationError("No file selected", field="resume")
        
        # Validate file extension
        allowed_extensions = [".pdf", ".docx", ".txt"]
        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            raise ValidationError(
                f"Only {', '.join(allowed_extensions)} files are allowed",
                field="resume"
            )
        
        # Read and validate file size
        content = file.read()
        
        if len(content) == 0:
            raise ValidationError("File is empty", field="resume")
        
        max_size = 10 * 1024 * 1024  # 10MB
        if len(content) > max_size:
            raise ValidationError(
                f"File too large. Maximum size is 10MB",
                field="resume"
            )
        
        # Get optional job description
        job_description = request.form.get("job_description", "").strip()
        
        # Analyze resume with retry logic
        try:
            result = ats_analyzer.analyze_resume(
                filename=file.filename,
                content=content,
                job_description=job_description
            )
        except Exception as e:
            # Handle PDF parsing errors gracefully
            if "PDF" in str(e) or "extract" in str(e).lower():
                raise ValidationError(
                    "Failed to parse PDF file. Please ensure it's a valid, text-based PDF",
                    field="resume"
                )
            raise LLMError(f"Resume analysis failed: {str(e)}")
        
        # Save to database
        try:
            user_id = request.user["id"]
            db = get_db()
            
            cursor = db.execute(
                """INSERT INTO resumes 
                   (user_id, resume_text, file_name, analysis_data, ats_score, target_role, uploaded_at)
                   VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
                [
                    user_id,
                    content.decode('utf-8', errors='ignore')[:5000],
                    file.filename,
                    json.dumps(result),
                    result.get("score", 0),
                    job_description or ''
                ]
            )
            db.commit()
            
            resume_id = cursor.lastrowid
            
        except Exception as e:
            raise DatabaseError(f"Failed to save resume: {str(e)}")
        
        # Format response
        response_data = {
            "resume_id": resume_id,
            "ats_score": result.get("score", 0),
            "matched_keywords": result.get("matched_keywords", []),
            "missing_keywords": result.get("missing_keywords", []),
            "suggestions": result.get("suggestions", []),
            "breakdown": result.get("breakdown", {}),
            "extracted_data": result.get("extracted_data", {})
        }
        
        return success_response(
            data=response_data,
            message="Resume analyzed successfully"
        )
        
    except (ValidationError, LLMError, DatabaseError):
        raise
    except Exception as e:
        raise LLMError(f"Resume upload failed: {str(e)}")


@ai_routes_bp.post("/resume/ats-optimization")
@require_auth
def ats_optimization():
    """
    Get ATS optimization suggestions for resume text
    
    Request Body:
        {
            "resume_text": "string (required)"
        }
    
    Returns:
        200: { success: true, data: { ats_score, suggestions }, message }
        400: { success: false, error: { code, message } }
    """
    try:
        data = request.get_json() or {}
        
        # Validate input
        resume_text = data.get("resume_text", "").strip()
        
        if not resume_text:
            raise ValidationError("Resume text is required", field="resume_text")
        
        if len(resume_text) < 100:
            raise ValidationError(
                "Resume text is too short (minimum 100 characters)",
                field="resume_text"
            )
        
        # Generate optimization suggestions using LLM
        try:
            system_prompt = """You are an ATS optimization expert.
Provide specific, actionable advice to improve ATS compatibility."""

            prompt = f"""Analyze this resume for ATS compatibility:

Resume:
{resume_text[:3000]}

Provide JSON with:
1. "ats_score": Overall ATS score (0-100)
2. "keyword_density": Percentage of relevant keywords
3. "format_issues": List of formatting problems for ATS
4. "missing_sections": Important sections missing
5. "suggestions": List of specific improvements (prioritized)

Return ONLY valid JSON, no other text."""

            response = llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                json_mode=True,
                retries=3
            )
            
            optimization = llm.parse_json_response(
                response,
                fallback={
                    "ats_score": 70,
                    "suggestions": ["Add more keywords", "Improve formatting"]
                }
            )
            
        except LLMError as e:
            # Provide fallback response
            optimization = {
                "ats_score": 70,
                "keyword_density": 50,
                "format_issues": ["Unable to analyze at this time"],
                "missing_sections": [],
                "suggestions": [
                    "Use standard section headings (Experience, Education, Skills)",
                    "Include relevant keywords from job descriptions",
                    "Use bullet points for achievements",
                    "Keep formatting simple and clean"
                ]
            }
        
        return success_response(
            data=optimization,
            message="ATS optimization analysis complete"
        )
        
    except ValidationError:
        raise
    except Exception as e:
        raise LLMError(f"ATS optimization failed: {str(e)}")


@ai_routes_bp.post("/resume/compare-job")
@require_auth
def compare_with_job():
    """
    Compare resume with job description
    
    Request Body:
        {
            "resume_text": "string (required)",
            "job_description": "string (required)"
        }
    
    Returns:
        200: { success: true, data: { match_score, analysis }, message }
        400: { success: false, error: { code, message } }
    """
    try:
        data = request.get_json() or {}
        
        # Validate inputs
        resume_text = data.get("resume_text", "").strip()
        job_description = data.get("job_description", "").strip()
        
        if not resume_text:
            raise ValidationError("Resume text is required", field="resume_text")
        
        if not job_description:
            raise ValidationError("Job description is required", field="job_description")
        
        if len(resume_text) < 100:
            raise ValidationError(
                "Resume text is too short",
                field="resume_text"
            )
        
        if len(job_description) < 50:
            raise ValidationError(
                "Job description is too short",
                field="job_description"
            )
        
        # Compare using LLM
        try:
            system_prompt = """You are an ATS expert analyzing resume-job matches.
Provide detailed, actionable comparison analysis."""

            prompt = f"""Compare this resume with the job description:

Resume:
{resume_text[:2000]}

Job Description:
{job_description[:2000]}

Provide JSON with:
1. "match_score": Overall match percentage (0-100)
2. "matching_skills": Skills that match the job requirements
3. "missing_skills": Required skills not in resume (prioritized)
4. "keyword_match": Percentage of job keywords found in resume
5. "recommendations": Specific suggestions to improve match
6. "strengths": What the candidate does well
7. "gaps": Critical gaps to address

Return ONLY valid JSON, no other text."""

            response = llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                json_mode=True,
                retries=3
            )
            
            comparison = llm.parse_json_response(
                response,
                fallback={
                    "match_score": 60,
                    "matching_skills": [],
                    "missing_skills": [],
                    "recommendations": ["Review job requirements carefully"]
                }
            )
            
        except LLMError:
            # Provide basic comparison as fallback
            comparison = {
                "match_score": 60,
                "matching_skills": ["General experience"],
                "missing_skills": ["Specific technical skills"],
                "keyword_match": 50,
                "recommendations": [
                    "Add more keywords from the job description",
                    "Highlight relevant experience",
                    "Quantify your achievements"
                ],
                "strengths": ["Professional experience"],
                "gaps": ["Technical skills alignment"]
            }
        
        return success_response(
            data=comparison,
            message="Resume comparison complete"
        )
        
    except ValidationError:
        raise
    except Exception as e:
        raise LLMError(f"Resume comparison failed: {str(e)}")


@ai_routes_bp.get("/resume/history")
@require_auth
def resume_history():
    """
    Get user's resume upload history
    
    Returns:
        200: { success: true, data: { resumes: [...] } }
    """
    try:
        user_id = request.user["id"]
        db = get_db()
        
        resumes = db.execute(
            """SELECT id, file_name, ats_score, uploaded_at
               FROM resumes
               WHERE user_id = ?
               ORDER BY uploaded_at DESC
               LIMIT 10""",
            [user_id]
        ).fetchall()
        
        resume_list = [
            {
                "id": r["id"],
                "file_name": r["file_name"],
                "ats_score": r["ats_score"],
                "uploaded_at": r["uploaded_at"]
            }
            for r in resumes
        ]
        
        return success_response(
            data={"resumes": resume_list}
        )
        
    except Exception as e:
        raise DatabaseError(f"Failed to fetch resume history: {str(e)}")


# ─── Career Coach Chat ────────────────────────────────────────────────────────

from app.services.workflow_orchestrator import WorkflowOrchestrator as _WorkflowOrchestrator
import sqlite3 as _sqlite3

_orchestrator = _WorkflowOrchestrator()


@ai_routes_bp.post("/chat/message")
@require_auth
def chat_message():
    """
    Send a message to the AI Career Coach

    Request Body:
        {
            "message": "string (required)",
            "context": {} (optional)
        }

    Returns:
        200: { success: true, data: { response, suggestions } }
    """
    try:
        data = request.get_json() or {}
        message = data.get("message", "").strip()

        if not message:
            raise ValidationError("Message is required", field="message")

        user_id = request.user["id"]

        response = _orchestrator.chat_with_context(
            user_id=user_id,
            message=message
        )

        # Persist to chat history (non-critical)
        try:
            db = get_db()
            db.execute(
                "INSERT INTO chat_messages (user_id, role, message) VALUES (?, 'user', ?)",
                (user_id, message)
            )
            db.execute(
                "INSERT INTO chat_messages (user_id, role, message) VALUES (?, 'assistant', ?)",
                (user_id, response["response"])
            )
            db.commit()
        except Exception:
            pass  # Don't fail the request if history save fails

        return success_response(
            data=response,
            message="Response generated"
        )

    except ValidationError:
        raise
    except Exception as e:
        raise LLMError(f"Chat failed: {str(e)}")


@ai_routes_bp.post("/chat/clear")
@require_auth
def chat_clear():
    """
    Clear the user's chat history

    Returns:
        200: { success: true, message: "Chat history cleared" }
    """
    try:
        user_id = request.user["id"]
        db = get_db()
        db.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,))
        db.commit()

        # Also clear in-memory session if orchestrator holds one
        try:
            chatbot = _orchestrator.chatbot
            if hasattr(chatbot, "conversation_sessions"):
                chatbot.conversation_sessions.pop(str(user_id), None)
        except Exception:
            pass

        return success_response(message="Chat history cleared")

    except Exception as e:
        raise DatabaseError(f"Failed to clear chat history: {str(e)}")
