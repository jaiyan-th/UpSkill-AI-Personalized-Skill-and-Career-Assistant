"""
Skill Gap Analysis Service
Integrates resume analysis, interview performance, and generates personalized learning paths
"""

import json
from typing import Dict, List, Optional
from app.database import get_db
from .llm_service import LLMService


class SkillGapService:
    def __init__(self):
        self.llm = LLMService()
        
    def extract_resume_skills(self, user_id: int) -> Dict:
        """Extract skills from user's latest resume"""
        db = get_db()
        
        resume = db.execute(
            """SELECT resume_text, analysis_data FROM resumes 
               WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT 1""",
            [user_id]
        ).fetchone()
        
        if not resume:
            return {'skills': [], 'experience_level': 'Entry'}
        
        # Parse analysis data if available
        if resume['analysis_data']:
            try:
                analysis = json.loads(resume['analysis_data'])
                return {
                    'skills': analysis.get('skills', []),
                    'experience_level': analysis.get('experience_level', 'Entry'),
                    'resume_text': resume['resume_text']
                }
            except:
                pass
        
        # Extract skills using AI if no analysis exists
        skills = self._extract_skills_with_ai(resume['resume_text'])
        return {
            'skills': skills,
            'experience_level': 'Entry',
            'resume_text': resume['resume_text']
        }
    
    def _extract_skills_with_ai(self, resume_text: str) -> List[str]:
        """Use AI to extract skills from resume text"""
        prompt = f"""Extract all technical skills, tools, and technologies from this resume.
Return ONLY a comma-separated list of skills, nothing else.

Resume:
{resume_text[:2000]}

Skills:"""
        
        try:
            response = self.llm.generate(
                prompt=prompt,
                system_prompt="You are a skill extraction expert. Extract only technical skills.",
                temperature=0.3,
                max_tokens=200
            )
            skills = [s.strip() for s in response.split(',') if s.strip()]
            return skills[:20]  # Limit to 20 skills
        except:
            return []
    
    def get_interview_performance(self, user_id: int) -> Dict:
        """Get user's interview performance data"""
        db = get_db()
        
        # Get latest completed interview
        interview = db.execute(
            """SELECT id, role, level, overall_score, evaluation_data 
               FROM interview_sessions 
               WHERE user_id = ? AND status = 'completed'
               ORDER BY ended_at DESC LIMIT 1""",
            [user_id]
        ).fetchone()
        
        if not interview:
            return {
                'has_interview': False,
                'weak_areas': [],
                'strong_areas': [],
                'overall_score': 0
            }
        
        # Parse evaluation data
        evaluation = {}
        if interview['evaluation_data']:
            try:
                evaluation = json.loads(interview['evaluation_data'])
            except:
                pass
        
        # Get Q&A details
        qa_pairs = db.execute(
            """SELECT question, answer, score, feedback 
               FROM interview_qa WHERE session_id = ?""",
            [interview['id']]
        ).fetchall()
        
        weak_areas = []
        strong_areas = []
        
        for qa in qa_pairs:
            score = qa['score'] or 0
            if score < 6:
                weak_areas.append({
                    'question': qa['question'],
                    'score': score,
                    'feedback': qa['feedback']
                })
            elif score >= 8:
                strong_areas.append({
                    'question': qa['question'],
                    'score': score
                })
        
        return {
            'has_interview': True,
            'role': interview['role'],
            'level': interview['level'],
            'overall_score': interview['overall_score'] or 0,
            'weak_areas': weak_areas,
            'strong_areas': strong_areas,
            'evaluation': evaluation
        }
    
    def get_role_requirements(self, role: str, level: str) -> Dict:
        """Get required skills for a specific role and level"""
        prompt = f"""List the essential technical skills required for a {role} at {level} level.

Categorize skills into:
1. Core Skills (must-have)
2. Important Skills (should-have)
3. Nice-to-have Skills (bonus)

Return as JSON:
{{
    "core_skills": ["skill1", "skill2", ...],
    "important_skills": ["skill1", "skill2", ...],
    "nice_to_have": ["skill1", "skill2", ...]
}}"""
        
        try:
            response = self.llm.generate(
                prompt=prompt,
                system_prompt="You are a technical recruiter. Provide accurate skill requirements.",
                temperature=0.5,
                max_tokens=500
            )
            
            # Try to parse JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # Fallback
            return {
                'core_skills': ['Programming', 'Problem Solving', 'Communication'],
                'important_skills': ['Teamwork', 'Version Control'],
                'nice_to_have': ['Cloud Computing', 'DevOps']
            }
        except:
            return {
                'core_skills': [],
                'important_skills': [],
                'nice_to_have': []
            }
    
    def analyze_skill_gaps(self, user_id: int, target_role: str, target_level: str = 'Mid-level') -> Dict:
        """
        Comprehensive skill gap analysis
        Combines resume skills, interview performance, and role requirements
        """
        print(f"[SKILL GAP] Starting analysis for user {user_id}, role: {target_role}, level: {target_level}")
        
        # Get user data from multiple sources
        resume_data = self.extract_resume_skills(user_id)
        interview_data = self.get_interview_performance(user_id)
        role_requirements = self.get_role_requirements(target_role, target_level)
        
        print(f"[SKILL GAP] Resume skills: {len(resume_data['skills'])}")
        print(f"[SKILL GAP] Has interview data: {interview_data['has_interview']}")
        print(f"[SKILL GAP] Interview score: {interview_data.get('overall_score', 0)}")
        
        # Combine skills from all sources
        user_skills = set()
        
        # Add resume skills
        for skill in resume_data['skills']:
            if isinstance(skill, dict):
                user_skills.add(skill.get('name', '').lower())
            else:
                user_skills.add(str(skill).lower())
        
        # Add skills inferred from interview performance
        if interview_data['has_interview']:
            # Extract skills from strong areas
            for strong in interview_data.get('strong_areas', []):
                question = strong.get('question', '').lower()
                # Simple keyword extraction (can be enhanced)
                for keyword in ['python', 'javascript', 'react', 'node', 'sql', 'java', 'aws', 'docker']:
                    if keyword in question:
                        user_skills.add(keyword)
        
        print(f"[SKILL GAP] Total combined skills: {len(user_skills)}")
        
        # Get all required skills
        all_required = (
            role_requirements.get('core_skills', []) +
            role_requirements.get('important_skills', []) +
            role_requirements.get('nice_to_have', [])
        )
        
        required_skills = set([s.lower() for s in all_required])
        
        # Find gaps with priority
        missing_skills = []
        for skill in all_required:
            if skill.lower() not in user_skills:
                priority = 'High' if skill in role_requirements.get('core_skills', []) else \
                          'Medium' if skill in role_requirements.get('important_skills', []) else 'Low'
                missing_skills.append({
                    'skill': skill,
                    'priority': priority
                })
        
        print(f"[SKILL GAP] Missing skills: {len(missing_skills)}")
        
        # Identify weak skills from interview
        weak_skills = []
        if interview_data['has_interview']:
            for weak in interview_data['weak_areas']:
                weak_skills.append({
                    'area': weak['question'][:100],
                    'score': weak['score'],
                    'feedback': weak.get('feedback', 'Needs improvement')
                })
        
        # Strong skills (from both resume and interview)
        strong_skills = []
        
        # Add resume skills
        for skill in resume_data['skills'][:15]:
            if isinstance(skill, dict):
                strong_skills.append(skill.get('name', str(skill)))
            else:
                strong_skills.append(str(skill))
        
        # Add interview strong areas
        if interview_data['has_interview']:
            for strong in interview_data.get('strong_areas', [])[:5]:
                area = strong.get('question', '')[:50]
                if area and area not in strong_skills:
                    strong_skills.append(f"✓ {area}")
        
        # Generate comprehensive AI-powered analysis
        analysis_summary = self._generate_comprehensive_summary(
            user_skills=list(user_skills),
            missing_skills=missing_skills,
            weak_areas=weak_skills,
            target_role=target_role,
            target_level=target_level,
            interview_score=interview_data.get('overall_score', 0),
            has_resume=len(resume_data['skills']) > 0,
            has_interview=interview_data['has_interview']
        )
        
        # Calculate readiness score
        readiness_score = self._calculate_readiness_score(
            len(user_skills),
            len(missing_skills),
            interview_data.get('overall_score', 0)
        )
        
        print(f"[SKILL GAP] Readiness score: {readiness_score}%")
        
        result = {
            'user_id': user_id,
            'target_role': target_role,
            'target_level': target_level,
            'strong_skills': strong_skills[:15],
            'missing_skills': missing_skills,
            'weak_skills': weak_skills,
            'interview_score': interview_data.get('overall_score', 0),
            'has_interview_data': interview_data['has_interview'],
            'has_resume_data': len(resume_data['skills']) > 0,
            'analysis_summary': analysis_summary,
            'readiness_score': readiness_score,
            'data_sources': {
                'resume': len(resume_data['skills']) > 0,
                'interview': interview_data['has_interview'],
                'ai_analysis': True
            }
        }
        
        # Save to database
        self._save_analysis(user_id, result)
        
        print(f"[SKILL GAP] Analysis complete and saved")
        
        return result
    
    def _generate_comprehensive_summary(self, user_skills, missing_skills, weak_areas, 
                                       target_role, target_level, interview_score,
                                       has_resume, has_interview) -> str:
        """Generate comprehensive AI-powered analysis summary"""
        
        # Build context based on available data
        context_parts = []
        
        if has_resume:
            context_parts.append(f"Resume Analysis: {len(user_skills)} skills identified")
        
        if has_interview:
            context_parts.append(f"Interview Performance: {interview_score}/100 score")
            if weak_areas:
                context_parts.append(f"{len(weak_areas)} areas need improvement")
        
        if not has_resume and not has_interview:
            context_parts.append("No resume or interview data available yet")
        
        context = ". ".join(context_parts)
        
        prompt = f"""Analyze this candidate's readiness for {target_role} ({target_level} level):

Data Sources: {context}
Current Skills: {', '.join(user_skills[:15]) if user_skills else 'None identified yet'}
Missing Skills: {', '.join([s['skill'] for s in missing_skills[:10]])}
High Priority Gaps: {len([s for s in missing_skills if s['priority'] == 'High'])}

Provide a personalized 2-3 sentence assessment that:
1. Acknowledges their current strengths
2. Identifies key areas to focus on
3. Gives encouraging but realistic advice

Be specific and actionable."""
        
        try:
            return self.llm.generate(
                prompt=prompt,
                system_prompt="You are an experienced career advisor. Be encouraging, specific, and actionable.",
                temperature=0.7,
                max_tokens=200
            )
        except Exception as e:
            print(f"Error generating summary: {e}")
            
            # Fallback summary based on data availability
            if has_resume and has_interview:
                return f"Based on your resume and interview performance (score: {interview_score}/100), you have {len(user_skills)} relevant skills for {target_role}. Focus on acquiring {len([s for s in missing_skills if s['priority'] == 'High'])} high-priority skills to increase your readiness. Your interview performance shows good potential with some areas for improvement."
            elif has_resume:
                return f"Your resume shows {len(user_skills)} relevant skills for {target_role}. To strengthen your profile, focus on acquiring {len([s for s in missing_skills if s['priority'] == 'High'])} high-priority skills. Consider taking a mock interview to get comprehensive feedback."
            elif has_interview:
                return f"Your interview performance (score: {interview_score}/100) shows potential for {target_role}. Upload your resume to get a complete skill analysis. Focus on improving the {len(weak_areas)} areas identified in your interview."
            else:
                return f"To get started with your {target_role} journey, upload your resume and complete a mock interview. This will help us identify your strengths and create a personalized learning path for the {len(missing_skills)} skills needed for this role."
    
    def _calculate_readiness_score(self, skills_count, missing_count, interview_score) -> int:
        """Calculate overall readiness score (0-100)"""
        skill_score = min(100, (skills_count / max(skills_count + missing_count, 1)) * 100)
        interview_weight = 0.4 if interview_score > 0 else 0
        skill_weight = 1.0 - interview_weight
        
        readiness = int(skill_score * skill_weight + interview_score * interview_weight)
        return max(0, min(100, readiness))
    
    def generate_learning_path(self, user_id: int, target_role: str, 
                               hours_per_week: int = 10) -> Dict:
        """Generate personalized learning roadmap"""
        # Get skill gap analysis
        db = get_db()
        analysis = db.execute(
            """SELECT gap_data FROM skill_gap_analysis 
               WHERE user_id = ? AND target_role = ?
               ORDER BY created_at DESC LIMIT 1""",
            [user_id, target_role]
        ).fetchone()
        
        if not analysis:
            # Run analysis first
            gap_data = self.analyze_skill_gaps(user_id, target_role)
        else:
            gap_data = json.loads(analysis['gap_data'])
        
        # Generate learning path with AI
        missing_skills = gap_data.get('missing_skills', [])
        weak_skills = gap_data.get('weak_skills', [])
        
        learning_path = self._generate_learning_roadmap(
            missing_skills=missing_skills,
            weak_skills=weak_skills,
            target_role=target_role,
            hours_per_week=hours_per_week
        )
        
        # Save recommendations
        self._save_learning_path(user_id, target_role, learning_path)
        
        return learning_path
    
    def _generate_learning_roadmap(self, missing_skills, weak_skills, 
                                   target_role, hours_per_week) -> Dict:
        """Use AI to generate detailed learning roadmap"""
        skills_to_learn = [s['skill'] for s in missing_skills if s['priority'] in ['High', 'Medium']][:8]
        
        prompt = f"""Create a learning roadmap for {target_role} role.

Skills to learn: {', '.join(skills_to_learn)}
Available time: {hours_per_week} hours/week

Provide a structured learning plan with:
1. Priority order (what to learn first)
2. Estimated time for each skill
3. Recommended resources (courses, tutorials, books)
4. Practical projects to build

Format as JSON:
{{
    "phases": [
        {{
            "phase": 1,
            "duration_weeks": 4,
            "skills": ["skill1", "skill2"],
            "resources": ["resource1", "resource2"],
            "projects": ["project1"]
        }}
    ],
    "total_duration_weeks": 12,
    "next_steps": ["step1", "step2"]
}}"""
        
        try:
            response = self.llm.generate(
                prompt=prompt,
                system_prompt="You are a learning path designer. Create practical, achievable plans.",
                temperature=0.6,
                max_tokens=1000
            )
            
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"Error generating roadmap: {e}")
        
        # Fallback roadmap
        return {
            'phases': [
                {
                    'phase': 1,
                    'duration_weeks': 4,
                    'skills': skills_to_learn[:2],
                    'resources': ['Online tutorials', 'Documentation'],
                    'projects': ['Build a simple project']
                }
            ],
            'total_duration_weeks': 12,
            'next_steps': ['Start with fundamentals', 'Practice daily', 'Build projects']
        }
    
    def get_course_recommendations(self, skills: List[str]) -> List[Dict]:
        """Get course recommendations for specific skills"""
        recommendations = []
        
        for skill in skills[:5]:
            prompt = f"""Recommend 2-3 best online courses/resources to learn {skill}.
Include free and paid options. Format: Course Name - Platform - Price"""
            
            try:
                response = self.llm.generate(
                    prompt=prompt,
                    system_prompt="You are an online learning expert.",
                    temperature=0.5,
                    max_tokens=200
                )
                
                recommendations.append({
                    'skill': skill,
                    'courses': response.strip().split('\n')[:3]
                })
            except:
                recommendations.append({
                    'skill': skill,
                    'courses': [f'Search for "{skill}" courses on Udemy, Coursera, or YouTube']
                })
        
        return recommendations
    
    def _save_analysis(self, user_id: int, analysis_data: Dict):
        """Save skill gap analysis to database"""
        db = get_db()
        
        db.execute(
            """INSERT INTO skill_gap_analysis (user_id, target_role, gap_data, created_at)
               VALUES (?, ?, ?, datetime('now'))""",
            [user_id, analysis_data['target_role'], json.dumps(analysis_data)]
        )
        db.commit()
    
    def _save_learning_path(self, user_id: int, target_role: str, path_data: Dict):
        """Save learning path to database"""
        db = get_db()
        
        # Check if path exists
        existing = db.execute(
            """SELECT id FROM learning_paths 
               WHERE user_id = ? AND target_role = ?""",
            [user_id, target_role]
        ).fetchone()
        
        if existing:
            db.execute(
                """UPDATE learning_paths 
                   SET path_data = ?, updated_at = datetime('now')
                   WHERE id = ?""",
                [json.dumps(path_data), existing['id']]
            )
        else:
            db.execute(
                """INSERT INTO learning_paths (user_id, target_role, path_data, created_at)
                   VALUES (?, ?, ?, datetime('now'))""",
                [user_id, target_role, json.dumps(path_data)]
            )
        
        db.commit()
