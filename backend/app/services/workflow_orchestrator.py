"""
Workflow Orchestrator - Complete User Journey Flow
Implements: Resume Upload → Skill Graph → Interview → Gap Analysis → Learning Path
"""

import json
from typing import Dict, List, Optional
from .resume_analyzer import ResumeAnalyzer
from .interview_engine import InterviewEngine
from .skill_gap_analyzer import SkillGapAnalyzer
from .chatbot_service import ChatbotService
from app.database import get_db

class WorkflowOrchestrator:
    """
    Orchestrates the complete user journey:
    1. Resume Upload & Analysis
    2. Skill Graph Building
    3. Mock Interview
    4. Skill Gap Analysis
    5. Learning Path Generation
    6. Dashboard & Feedback
    """
    
    def __init__(self):
        self.resume_analyzer = ResumeAnalyzer()
        self.interview_engine = InterviewEngine()
        self.skill_analyzer = SkillGapAnalyzer()
        self.chatbot = ChatbotService()
    
    # ==================== STEP 1: RESUME INTELLIGENCE ====================
    
    def process_resume_upload(
        self, 
        user_id: int, 
        pdf_file, 
        job_description: str = None
    ) -> Dict:
        """
        Complete resume processing pipeline
        
        Returns:
            {
                "resume_id": int,
                "analysis": {...},
                "skills": [...],
                "skill_graph": {...},
                "next_step": "interview"
            }
        """
        
        # Extract text from PDF
        resume_text = self.resume_analyzer.extract_text_from_pdf(pdf_file)
        
        # Comprehensive analysis
        analysis = self.resume_analyzer.analyze_resume(resume_text, job_description)
        
        # Extract skills
        skills = self.resume_analyzer.extract_skills(resume_text)
        
        # Build skill graph
        skill_graph = self.resume_analyzer.build_skill_graph(skills)
        
        # Save to database
        db = get_db()
        cursor = db.execute(
            """INSERT INTO resumes 
               (user_id, resume_text, file_name, analysis_data, ats_score) 
               VALUES (?, ?, ?, ?, ?)""",
            (
                user_id,
                resume_text,
                getattr(pdf_file, 'filename', 'resume.pdf'),
                json.dumps(analysis),
                analysis.get('ats_score', 0)
            )
        )
        db.commit()
        resume_id = cursor.lastrowid
        
        # Save skill graph
        for category, category_skills in skill_graph.items():
            for skill in category_skills:
                db.execute(
                    """INSERT INTO user_skill_graph 
                       (user_id, skill_name, skill_level, years_experience, category) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        user_id,
                        skill.get('name'),
                        skill.get('level', 'Intermediate'),
                        skill.get('years', 0),
                        category
                    )
                )
        db.commit()
        
        return {
            "resume_id": resume_id,
            "analysis": analysis,
            "skills": skills,
            "skill_graph": skill_graph,
            "next_step": "interview",
            "message": "Resume analyzed successfully! Ready to start mock interview?"
        }
    
    # ==================== STEP 2: SKILL GRAPH ====================
    
    def get_user_skill_graph(self, user_id: int) -> Dict:
        """
        Retrieve user's complete skill graph
        
        Returns:
            {
                "frontend": [...],
                "backend": [...],
                "database": [...],
                "devops": [...],
                "tools": [...],
                "soft_skills": [...]
            }
        """
        
        db = get_db()
        skills = db.execute(
            """SELECT skill_name, skill_level, years_experience, category 
               FROM user_skill_graph 
               WHERE user_id = ?""",
            (user_id,)
        ).fetchall()
        
        skill_graph = {
            "frontend": [],
            "backend": [],
            "database": [],
            "devops": [],
            "tools": [],
            "soft_skills": []
        }
        
        for skill in skills:
            category = skill['category'] or 'tools'
            skill_graph[category].append({
                "name": skill['skill_name'],
                "level": skill['skill_level'],
                "years": skill['years_experience']
            })
        
        return skill_graph
    
    # ==================== STEP 3: MOCK INTERVIEW ====================
    
    def start_complete_interview(
        self,
        user_id: int,
        target_role: str,
        experience_level: str,
        job_description: str = None
    ) -> Dict:
        """
        Start interview with user's skills from resume and job requirements
        
        Returns:
            {
                "session_id": int,
                "first_question": "...",
                "context": {...}
            }
        """
        
        # Get user skills
        skill_graph = self.get_user_skill_graph(user_id)
        all_skills = []
        for category_skills in skill_graph.values():
            all_skills.extend(category_skills)
        
        # Get resume summary and analysis
        db = get_db()
        resume = db.execute(
            """SELECT resume_text, analysis_data FROM resumes 
               WHERE user_id = ? 
               ORDER BY uploaded_at DESC LIMIT 1""",
            (user_id,)
        ).fetchone()
        
        resume_text = None
        if resume:
            # We will pass the full raw text and analysis to ensure deep context.
            resume_text = resume['resume_text']
        
        # Start interview with job description
        engine = InterviewEngine()
        result = engine.start_interview(
            role=target_role,
            level=experience_level,
            skills=all_skills,
            resume_summary=resume_text, # Using full resume text now
            job_description=job_description
        )
        
        # Save session with job description
        cursor = db.execute(
            """INSERT INTO interview_sessions 
               (user_id, role, level, status) 
               VALUES (?, ?, ?, 'active')""",
            (user_id, target_role, experience_level)
        )
        db.commit()
        session_id = cursor.lastrowid
        
        # Save first question
        db.execute(
            """INSERT INTO interview_qa 
               (session_id, question) 
               VALUES (?, ?)""",
            (session_id, result['question'])
        )
        db.commit()
        
        return {
            "session_id": session_id,
            "first_question": result['question'],
            "context": result['context'],
            "question_number": 1,
            "target_role": target_role
        }
    
    def complete_interview_cycle(
        self,
        session_id: int,
        user_id: int
    ) -> Dict:
        """
        Complete interview and generate comprehensive evaluation
        Links resume analysis + interview performance + skill gaps
        
        Returns:
            {
                "evaluation": {...},
                "skill_gaps": {...},
                "learning_path": {...},
                "next_step": "learning"
            }
        """
        
        db = get_db()
        
        # Get interview data
        session = db.execute(
            """SELECT * FROM interview_sessions WHERE id = ?""",
            (session_id,)
        ).fetchone()
        
        # Get interview evaluation data
        evaluation_data = json.loads(session['evaluation_data']) if session.get('evaluation_data') else {}
        
        # Get user skills
        skill_graph = self.get_user_skill_graph(user_id)
        all_skills = []
        for category_skills in skill_graph.values():
            all_skills.extend(category_skills)
        
        # Get resume analysis
        resume = db.execute(
            """SELECT analysis_data FROM resumes 
               WHERE user_id = ? 
               ORDER BY uploaded_at DESC LIMIT 1""",
            (user_id,)
        ).fetchone()
        
        resume_analysis = None
        if resume:
            resume_analysis = json.loads(resume['analysis_data'])
        
        # Analyze skill gaps with ALL context
        gap_analysis = self.skill_analyzer.analyze_gaps(
            current_skills=all_skills,
            target_role=session['role'],
            experience_level=session['level'],
            job_description=None,  # Can be added if stored
            resume_analysis=resume_analysis,
            interview_evaluation=evaluation_data
        )
        
        # Generate learning path BASED ON SKILL GAPS
        learning_path = self.skill_analyzer.generate_learning_path(
            current_skills=all_skills,
            target_role=session['role'],
            skill_gaps=gap_analysis.get('skill_gaps'),  # Pass the skill gaps!
            time_available_hours_per_week=10
        )
        
        # Assess readiness
        interview_scores = [evaluation_data.get('overall_score', 0)]
        readiness = self.skill_analyzer.assess_readiness(
            current_skills=all_skills,
            target_role=session['role'],
            interview_scores=interview_scores
        )
        
        # Save gap analysis
        db.execute(
            """INSERT INTO skill_gap_analysis 
               (user_id, target_role, gap_data) 
               VALUES (?, ?, ?)""",
            (user_id, session['role'], json.dumps(gap_analysis))
        )
        
        # Save learning path
        db.execute(
            """INSERT INTO learning_paths 
               (user_id, target_role, path_data) 
               VALUES (?, ?, ?)""",
            (user_id, session['role'], json.dumps(learning_path))
        )
        
        db.commit()
        
        return {
            "evaluation": {
                "overall_score": sum(interview_scores) / len(interview_scores) * 10 if interview_scores else 50,
                "questions_answered": len(qa_pairs),
                "average_score": sum(interview_scores) / len(interview_scores) if interview_scores else 5
            },
            "skill_gaps": gap_analysis,
            "learning_path": learning_path,
            "readiness": readiness,
            "next_step": "learning",
            "message": "Interview complete! Here's your personalized learning path."
        }
    
    # ==================== STEP 4: DASHBOARD & INSIGHTS ====================
    
    def get_user_dashboard(self, user_id: int) -> Dict:
        """
        Get complete user dashboard with all insights
        
        Returns:
            {
                "profile": {...},
                "skill_graph": {...},
                "recent_interviews": [...],
                "skill_gaps": {...},
                "learning_path": {...},
                "progress": {...}
            }
        """
        
        db = get_db()
        
        # Get latest resume analysis
        resume = db.execute(
            """SELECT analysis_data, ats_score, uploaded_at 
               FROM resumes 
               WHERE user_id = ? 
               ORDER BY uploaded_at DESC LIMIT 1""",
            (user_id,)
        ).fetchone()
        
        resume_data = None
        if resume:
            resume_data = {
                "analysis": json.loads(resume['analysis_data']),
                "ats_score": resume['ats_score'],
                "uploaded_at": resume['uploaded_at']
            }
        
        # Get skill graph
        skill_graph = self.get_user_skill_graph(user_id)
        
        # Get recent interviews
        interviews = db.execute(
            """SELECT id, role, level, overall_score, started_at, ended_at 
               FROM interview_sessions 
               WHERE user_id = ? 
               ORDER BY started_at DESC LIMIT 5""",
            (user_id,)
        ).fetchall()
        
        interview_list = []
        for interview in interviews:
            interview_list.append({
                "id": interview['id'],
                "role": interview['role'],
                "level": interview['level'],
                "score": interview['overall_score'],
                "date": interview['started_at']
            })
        
        # Get latest skill gap analysis
        gap = db.execute(
            """SELECT gap_data, created_at 
               FROM skill_gap_analysis 
               WHERE user_id = ? 
               ORDER BY created_at DESC LIMIT 1""",
            (user_id,)
        ).fetchone()
        
        gap_data = json.loads(gap['gap_data']) if gap else None
        
        # Get learning path
        path = db.execute(
            """SELECT path_data, progress, created_at 
               FROM learning_paths 
               WHERE user_id = ? 
               ORDER BY created_at DESC LIMIT 1""",
            (user_id,)
        ).fetchone()
        
        learning_path = None
        if path:
            learning_path = {
                "path": json.loads(path['path_data']),
                "progress": path['progress'],
                "created_at": path['created_at']
            }
        
        return {
            "resume": resume_data,
            "skill_graph": skill_graph,
            "recent_interviews": interview_list,
            "skill_gaps": gap_data,
            "learning_path": learning_path,
            "stats": {
                "total_skills": sum(len(skills) for skills in skill_graph.values()),
                "interviews_completed": len(interview_list),
                "average_interview_score": sum(i['score'] for i in interview_list if i['score']) / len(interview_list) if interview_list else 0
            }
        }
    
    # ==================== CHATBOT INTEGRATION ====================
    
    def chat_with_context(
        self,
        user_id: int,
        message: str
    ) -> Dict:
        """
        Chat with full user context
        
        Returns:
            {
                "response": "...",
                "suggestions": [...]
            }
        """
        
        # Build user context
        dashboard = self.get_user_dashboard(user_id)
        
        user_context = {
            "skills": [],
            "target_role": None,
            "experience_level": None,
            "recent_activity": []
        }
        
        # Extract skills
        for category_skills in dashboard['skill_graph'].values():
            user_context['skills'].extend(category_skills)
        
        # Extract target role from latest interview
        if dashboard['recent_interviews']:
            user_context['target_role'] = dashboard['recent_interviews'][0]['role']
        
        # Extract experience level from resume
        if dashboard.get('resume'):
            user_context['experience_level'] = dashboard['resume']['analysis'].get('experience_level')
        
        db = get_db()
        resume = db.execute(
            "SELECT resume_text FROM resumes WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT 1",
            (user_id,)
        ).fetchone()
        
        if resume:
            user_context['resume_text'] = resume['resume_text']
        
        # Chat with context
        response = self.chatbot.chat(
            user_id=str(user_id),
            message=message,
            user_context=user_context
        )
        
        return response
