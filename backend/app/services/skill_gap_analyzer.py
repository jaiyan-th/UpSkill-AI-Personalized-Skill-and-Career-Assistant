"""
Skill Gap Analyzer - Identify gaps and generate learning paths
"""

import json
from typing import Dict, List
from .llm_service import LLMService

class SkillGapAnalyzer:
    def __init__(self):
        self.llm = LLMService()
    
    def analyze_gaps(
        self, 
        current_skills: List[Dict], 
        target_role: str,
        experience_level: str = "Mid-level",
        job_description: str = None,
        resume_analysis: Dict = None,
        interview_evaluation: Dict = None
    ) -> Dict:
        """
        Analyze skill gaps based on resume, job requirements, and interview performance
        
        Args:
            current_skills: List of current skills from resume
            target_role: Target job role
            experience_level: Current experience level
            job_description: Target job description (optional)
            resume_analysis: Resume analysis results (optional)
            interview_evaluation: Interview evaluation results (optional)
        
        Returns:
            {
                "required_skills": [...],
                "matching_skills": [...],
                "missing_skills": [...],
                "skill_gaps": {...},
                "learning_priority": [...],
                "estimated_time_months": 3-12,
                "resume_vs_job_match": 0-100
            }
        """
        
        system_prompt = """You are a career development expert specializing in skill gap analysis.
Compare resume skills with job requirements and interview performance to identify gaps.
Provide actionable, specific recommendations."""

        # Build context
        context_parts = [
            f"Target Role: {target_role}",
            f"Experience Level: {experience_level}",
            f"\nCurrent Skills from Resume:\n{json.dumps(current_skills, indent=2)}"
        ]
        
        if job_description:
            context_parts.append(f"\nJob Description:\n{job_description}")
        
        if resume_analysis:
            ats_score = resume_analysis.get('score', 0)
            matched_kw = resume_analysis.get('matched_keywords', [])
            missing_kw = resume_analysis.get('missing_keywords', [])
            context_parts.append(f"\nResume ATS Score: {ats_score}/100")
            context_parts.append(f"Matched Keywords: {', '.join(matched_kw[:10])}")
            context_parts.append(f"Missing Keywords: {', '.join(missing_kw[:10])}")
        
        if interview_evaluation:
            context_parts.append(f"\nInterview Performance:")
            context_parts.append(f"- Overall Score: {interview_evaluation.get('overall_score', 0)}/100")
            context_parts.append(f"- Technical Accuracy: {interview_evaluation.get('technical_accuracy', 0)}/10")
            context_parts.append(f"- Communication: {interview_evaluation.get('communication_clarity', 0)}/10")
            context_parts.append(f"- Role Fit: {interview_evaluation.get('role_fit', 0)}/10")
            if interview_evaluation.get('skill_gaps'):
                context_parts.append(f"- Identified Skill Gaps: {json.dumps(interview_evaluation['skill_gaps'])}")
            if interview_evaluation.get('communication_skill_gaps'):
                context_parts.append(f"- Identified Communication Gaps: {json.dumps(interview_evaluation['communication_skill_gaps'])}")

        prompt = f"""{chr(10).join(context_parts)}

Analyze skill gaps comprehensively by comparing:
1. Resume skills vs Job requirements
2. Interview performance vs Role expectations
3. Missing technical and soft skills

Provide detailed JSON analysis:
{{
  "resume_vs_job_match": 0-100 (how well resume matches job),
  
  "required_skills": [
    {{
      "name": "skill name",
      "importance": "Critical/Important/Nice-to-have",
      "current_level": "None/Beginner/Intermediate/Advanced",
      "required_level": "Intermediate/Advanced/Expert",
      "gap_severity": "High/Medium/Low"
    }}
  ],
  
  "matching_skills": [
    {{"name": "skill", "level": "current level", "strength": "why it's a strength"}}
  ],
  
  "missing_skills": [
    {{
      "name": "skill name",
      "priority": 1-10,
      "reason": "why critical for {target_role}",
      "source": "job_description/interview/industry_standard"
    }}
  ],
  
  "skill_gaps": {{
    "critical_gaps": [
      {{"skill": "name", "impact": "why critical", "learn_first": true}}
    ],
    "important_gaps": [
      {{"skill": "name", "impact": "why important"}}
    ],
    "nice_to_have": [
      {{"skill": "name", "benefit": "added advantage"}}
    ]
  }},
  
  "communication_gaps": [
    {{"area": "clarity/fluency/articulation", "feedback": "specific feedback", "improvement": "how to improve"}}
  ],
  
  "learning_priority": [
    {{"rank": 1, "skill": "skill name", "reason": "why learn first", "estimated_weeks": 4}}
  ],
  
  "estimated_time_months": 3-12,
  "readiness_score": 0-100,
  "readiness_assessment": "honest assessment of job readiness",
  
  "immediate_actions": [
    "specific action 1",
    "specific action 2",
    "specific action 3"
  ]
}}

IMPORTANT:
- Be specific about what's missing from resume
- Link gaps to job requirements
- Consider interview performance
- Prioritize based on role criticality
- Include both technical and communication gaps

Return ONLY valid JSON, no other text."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            json_mode=True,
            max_tokens=3000
        )
        
        result = self.llm.parse_json_response(response)
        
        # Add metadata
        result['target_role'] = target_role
        result['analysis_date'] = 'current'
        
        return result
    
    def generate_learning_path(
        self,
        current_skills: List[Dict],
        target_role: str,
        skill_gaps: Dict = None,
        time_available_hours_per_week: int = 10,
        resume_gaps: List[Dict] = None,
        interview_gaps: List[Dict] = None
    ) -> Dict:
        """
        Generate personalized learning path based on skill gap analysis
        
        Args:
            current_skills: Current skills from resume
            target_role: Target job role
            skill_gaps: Skill gap analysis results (from analyze_gaps)
            time_available_hours_per_week: Available study time
            resume_gaps: Gaps identified from resume analysis
            interview_gaps: Gaps identified from interview analysis
        
        Returns:
            {
                "phases": [...],
                "total_duration_weeks": 12-24,
                "milestones": [...],
                "resume_based_resources": [...],
                "interview_based_resources": [...]
            }
        """
        
        system_prompt = """You are a learning path architect for tech professionals.
Create structured, achievable learning roadmaps based on identified skill gaps.
Prioritize critical gaps first, then important gaps.
Provide SPECIFIC platforms and courses for each skill gap."""

        # Build context with skill gaps
        context_parts = [
            f"Target Role: {target_role}",
            f"Time Available: {time_available_hours_per_week} hours/week",
            f"\nCurrent Skills:\n{json.dumps(current_skills, indent=2)}"
        ]
        
        # Add resume gaps
        if resume_gaps:
            context_parts.append(f"\n=== GAPS FROM RESUME ANALYSIS ===")
            context_parts.append(json.dumps(resume_gaps, indent=2))
        
        # Add interview gaps
        if interview_gaps:
            context_parts.append(f"\n=== GAPS FROM INTERVIEW ANALYSIS ===")
            context_parts.append(json.dumps(interview_gaps, indent=2))
        
        if skill_gaps:
            context_parts.append(f"\n=== SKILL GAPS TO ADDRESS ===")
            
            if skill_gaps.get('critical_gaps'):
                context_parts.append(f"\nCRITICAL GAPS (Learn First):")
                context_parts.append(json.dumps(skill_gaps['critical_gaps'], indent=2))
            
            if skill_gaps.get('important_gaps'):
                context_parts.append(f"\nIMPORTANT GAPS (Learn Next):")
                context_parts.append(json.dumps(skill_gaps['important_gaps'], indent=2))
            
            if skill_gaps.get('nice_to_have'):
                context_parts.append(f"\nNICE-TO-HAVE (Optional):")
                context_parts.append(json.dumps(skill_gaps['nice_to_have'], indent=2))
            
            if skill_gaps.get('communication_gaps'):
                context_parts.append(f"\nCOMMUNICATION GAPS:")
                context_parts.append(json.dumps(skill_gaps['communication_gaps'], indent=2))
            
            if skill_gaps.get('learning_priority'):
                context_parts.append(f"\nRECOMMENDED LEARNING PRIORITY:")
                context_parts.append(json.dumps(skill_gaps['learning_priority'], indent=2))

        prompt = f"""{chr(10).join(context_parts)}

Generate a structured learning path that addresses the identified skill gaps from BOTH resume and interview analysis:

REQUIREMENTS:
1. Start with CRITICAL GAPS in Phase 1 (especially from resume)
2. Address IMPORTANT GAPS in Phase 2-3
3. Include communication skill improvement if gaps identified in interview
4. Provide SPECIFIC platforms and courses (Udemy, Coursera, LeetCode, HackerRank, YouTube channels, etc.)
5. For coding gaps: suggest LeetCode, HackerRank, CodeSignal, AlgoExpert
6. For communication gaps: suggest Toastmasters, Coursera communication courses, YouTube channels
7. Include hands-on projects for each phase
8. Make it realistic based on available time

Generate as JSON:
{{
  "resume_based_resources": [
    {{
      "gap": "skill name from resume",
      "priority": "high/medium/low",
      "resources": [
        {{
          "type": "course",
          "name": "Complete Python Bootcamp",
          "platform": "Udemy",
          "url": "https://www.udemy.com/course/complete-python-bootcamp/",
          "duration": "22 hours",
          "price": "$84.99",
          "rating": "4.6/5"
        }},
        {{
          "type": "practice",
          "name": "LeetCode",
          "platform": "LeetCode",
          "url": "https://leetcode.com/",
          "focus": "Python coding problems - Easy to Medium",
          "recommended_problems": 50
        }}
      ]
    }}
  ],
  "interview_based_resources": [
    {{
      "gap": "communication clarity",
      "priority": "high/medium/low",
      "resources": [
        {{
          "type": "course",
          "name": "Improving Communication Skills",
          "platform": "Coursera",
          "url": "https://www.coursera.org/learn/wharton-communication-skills",
          "duration": "16 hours",
          "price": "Free (audit)"
        }},
        {{
          "type": "practice",
          "name": "Toastmasters International",
          "platform": "Toastmasters",
          "url": "https://www.toastmasters.org/",
          "focus": "Public speaking and communication",
          "frequency": "Weekly meetings"
        }}
      ]
    }}
  ],
  "phases": [
    {{
      "phase_number": 1,
      "name": "Foundation - Critical Skills",
      "duration_weeks": 4,
      "focus": "Address critical skill gaps from resume",
      "topics": ["topic1", "topic2"],
      "skills_to_learn": [
        {{"skill": "skill name", "reason": "why learning this", "from_gap": "resume/interview"}}
      ],
      "resources": [
        {{
          "type": "course",
          "name": "Specific course name",
          "platform": "Udemy/Coursera/YouTube",
          "url": "actual URL",
          "duration": "10 hours",
          "price": "$49.99 or Free",
          "priority": "high/medium"
        }},
        {{
          "type": "practice",
          "name": "LeetCode/HackerRank/CodeSignal",
          "platform": "LeetCode",
          "url": "https://leetcode.com/",
          "focus": "What to practice",
          "recommended_problems": 30
        }}
      ],
      "projects": [
        {{
          "name": "Project name",
          "description": "What to build",
          "skills_practiced": ["skill1", "skill2"],
          "estimated_hours": 20,
          "difficulty": "beginner/intermediate"
        }}
      ],
      "milestones": [
        "What you'll achieve by end of phase"
      ],
      "success_criteria": [
        "How to know you've mastered this phase"
      ]
    }}
  ],
  "total_duration_weeks": 12-24,
  "total_hours": 120-240,
  "difficulty_progression": "How difficulty increases across phases",
  "communication_improvement_plan": {{
    "activities": ["Join Toastmasters", "Practice mock interviews"],
    "resources": [
      {{
        "name": "Communication course",
        "platform": "Coursera",
        "url": "actual URL"
      }}
    ],
    "practice_schedule": "Weekly practice plan"
  }},
  "milestones": [
    {{
      "week": 4,
      "achievement": "What you should achieve",
      "assessment": "How to test yourself"
    }}
  ],
  "final_readiness_check": [
    "Checklist item 1",
    "Checklist item 2"
  ],
  "estimated_job_readiness": "When you'll be ready for {target_role}"
}}

IMPORTANT:
- Provide REAL, SPECIFIC platforms and courses with URLs
- For coding gaps: LeetCode, HackerRank, CodeSignal, AlgoExpert, Udemy, Coursera
- For communication: Toastmasters, Coursera, YouTube (Charisma on Command, etc.)
- For system design: System Design Interview courses, Grokking the System Design
- Directly address gaps from BOTH resume and interview
- Prioritize critical gaps first
- Include practical projects

Return ONLY valid JSON, no other text."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5,
            json_mode=True,
            max_tokens=3000
        )
        
        result = self.llm.parse_json_response(response)
        
        # Add metadata
        result['target_role'] = target_role
        result['based_on_skill_gaps'] = True if skill_gaps else False
        result['has_resume_gaps'] = True if resume_gaps else False
        result['has_interview_gaps'] = True if interview_gaps else False
        
        return result
    
    def recommend_resources(
        self,
        skill: str,
        current_level: str,
        target_level: str
    ) -> Dict:
        """
        Recommend learning resources for a specific skill
        
        Returns:
            {
                "courses": [...],
                "books": [...],
                "articles": [...],
                "videos": [...],
                "practice_platforms": [...],
                "projects": [...]
            }
        """
        
        system_prompt = """You are a learning resource curator for tech skills.
Recommend high-quality, practical resources."""

        prompt = f"""Recommend learning resources:

Skill: {skill}
Current Level: {current_level}
Target Level: {target_level}

Provide JSON with specific resources:
{{
  "courses": [
    {{"name": "Course name", "platform": "Udemy/Coursera/etc", "duration": "10 hours", "rating": "4.5/5", "price": "Free/$49"}}
  ],
  "books": [
    {{"title": "Book title", "author": "Author", "level": "Beginner/Advanced"}}
  ],
  "articles": [
    {{"title": "Article title", "source": "Medium/Dev.to", "url": "URL if known"}}
  ],
  "videos": [
    {{"title": "Video/Channel", "platform": "YouTube", "creator": "Creator name"}}
  ],
  "practice_platforms": [
    {{"name": "LeetCode/HackerRank", "focus": "What to practice", "difficulty": "Easy/Medium/Hard"}}
  ],
  "projects": [
    {{"name": "Project idea", "description": "What to build", "difficulty": "Beginner/Advanced"}}
  ],
  "estimated_time": "Time to reach target level"
}}

Recommend real, popular resources.
Return ONLY valid JSON, no other text."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.4,
            json_mode=True
        )
        
        return self.llm.parse_json_response(response)
    
    def assess_readiness(
        self,
        current_skills: List[Dict],
        target_role: str,
        interview_scores: List[int] = None
    ) -> Dict:
        """
        Assess if candidate is ready for target role
        
        Returns:
            {
                "ready": true/false,
                "readiness_score": 0-100,
                "strengths": [...],
                "gaps": [...],
                "recommendation": "..."
            }
        """
        
        system_prompt = """You are a career readiness assessor.
Provide honest, constructive assessment of job readiness."""

        prompt = f"""Assess readiness for this role:

Current Skills:
{json.dumps(current_skills, indent=2)}

Target Role: {target_role}
{f"Recent Interview Scores: {interview_scores}" if interview_scores else ""}

Provide JSON assessment:
{{
  "ready": true/false,
  "readiness_score": 0-100,
  "confidence_level": "Low/Medium/High",
  "strengths": ["strength1", "strength2"],
  "gaps": ["gap1", "gap2"],
  "recommendation": "Detailed recommendation",
  "next_steps": ["step1", "step2"],
  "estimated_time_to_ready": "2-6 months"
}}

Be honest but encouraging.
Return ONLY valid JSON, no other text."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            json_mode=True
        )
        
        return self.llm.parse_json_response(response)
