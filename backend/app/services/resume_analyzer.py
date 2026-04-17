"""
Resume Analyzer - Extract skills and analyze resume using LLM
"""

import PyPDF2
import io
import json
from typing import Dict, List
from .llm_service import LLMService

class ResumeAnalyzer:
    def __init__(self):
        self.llm = LLMService()
    
    def extract_text_from_pdf(self, pdf_file) -> str:
        """Extract text from PDF resume"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text.strip()
        except Exception as e:
            print(f"PDF extraction error: {e}")
            raise Exception("Failed to extract text from PDF")
    
    def analyze_resume(self, resume_text: str, job_description: str = None) -> Dict:
        """
        Comprehensive resume analysis using LLM
        
        Returns:
            {
                "skills": [...],
                "experience_level": "Junior/Mid/Senior",
                "strongest_areas": [...],
                "weakest_areas": [...],
                "ats_score": 0-100,
                "recommendations": [...]
            }
        """
        
        system_prompt = """You are an expert technical recruiter and resume analyst.
Analyze resumes thoroughly and provide structured, actionable feedback.
Always return valid JSON format."""

        prompt = f"""Analyze this resume and provide a comprehensive evaluation.

Resume:
{resume_text}

{f"Job Description: {job_description}" if job_description else ""}

Provide a JSON response with:
1. "skills": Array of technical skills with format [{{"name": "Python", "level": "Advanced", "years": 3}}]
2. "experience_level": "Junior" (0-2 years), "Mid-level" (2-5 years), or "Senior" (5+ years)
3. "strongest_areas": Top 3 technical strengths
4. "weakest_areas": Areas that need improvement
5. "ats_score": Score 0-100 for ATS compatibility
6. "recommendations": List of specific improvements
7. "missing_keywords": Keywords missing if job description provided
8. "match_score": 0-100 match with job description (if provided)

Return ONLY valid JSON, no other text."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,  # Lower for more consistent analysis
            json_mode=True
        )
        
        return self.llm.parse_json_response(response)
    
    def extract_skills(self, resume_text: str) -> List[Dict]:
        """
        Extract just the skills from resume with enhanced NLP
        
        Returns:
            [{"name": "Python", "level": "Advanced", "years": 3}, ...]
        """
        system_prompt = """You are an expert at extracting technical skills from resumes.
Extract ALL technical skills with their proficiency levels.
IMPORTANT: Return a JSON object with a "skills" array, not just an array."""

        prompt = f"""Extract all technical skills from this resume:

{resume_text}

Return JSON object with skills array:
{{
  "skills": [
    {{"name": "Python", "level": "Advanced", "years": 3, "category": "Programming"}},
    {{"name": "React", "level": "Intermediate", "years": 2, "category": "Frontend"}},
    {{"name": "JavaScript", "level": "Advanced", "years": 4, "category": "Programming"}},
    {{"name": "HTML/CSS", "level": "Advanced", "years": 4, "category": "Frontend"}},
    {{"name": "Java", "level": "Intermediate", "years": 2, "category": "Backend"}}
  ]
}}

Categories: Programming, Frontend, Backend, Database, Cloud, DevOps, Tools, Soft Skills

Extract ALL skills mentioned in the resume. Be thorough.
Return ONLY valid JSON object with "skills" key, no other text."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            json_mode=True
        )
        
        try:
            result = self.llm.parse_json_response(response)
            # Handle both array and object with "skills" key
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and "skills" in result:
                return result["skills"]
            else:
                print(f"[WARNING] Unexpected skills format: {result}")
                return []
        except Exception as e:
            print(f"[ERROR] Failed to parse skills: {e}")
            print(f"[DEBUG] Raw response: {response}")
            return []
    
    def calculate_ats_score(self, resume_text: str, job_description: str = None) -> Dict:
        """
        Calculate detailed ATS score with breakdown
        
        Returns:
            {
                "overall_score": 75,
                "keyword_match": 80,
                "formatting": 70,
                "section_completeness": 75,
                "readability": 80,
                "details": {...}
            }
        """
        
        system_prompt = """You are a technical skill extraction expert.
Extract all technical skills accurately with proficiency levels."""

        prompt = f"""Extract all technical skills from this resume.

Resume:
{resume_text}

For each skill, determine:
- name: Skill name (e.g., "Python", "React", "AWS")
- level: "Beginner", "Intermediate", or "Advanced"
- years: Estimated years of experience (0-10)

Return JSON array:
[
  {{"name": "Python", "level": "Advanced", "years": 3}},
  {{"name": "React", "level": "Intermediate", "years": 2}}
]

Return ONLY valid JSON array, no other text."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            json_mode=True
        )
        
        result = self.llm.parse_json_response(response)
        
        # Handle both array and object with "skills" key
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and "skills" in result:
            return result["skills"]
        else:
            return []
    
    def build_skill_graph(self, skills: List[Dict]) -> Dict:
        """
        Build skill graph categorizing skills by domain
        
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
        
        system_prompt = """You are a technical skill categorization expert.
Categorize skills into appropriate technical domains."""

        prompt = f"""Categorize these skills into technical domains:

Skills:
{json.dumps(skills, indent=2)}

Return JSON with categories:
{{
  "frontend": [skills related to frontend],
  "backend": [skills related to backend],
  "database": [skills related to databases],
  "devops": [skills related to DevOps/Cloud],
  "tools": [development tools, IDEs, etc],
  "soft_skills": [communication, leadership, etc]
}}

Each skill should be: {{"name": "...", "level": "...", "years": ...}}

Return ONLY valid JSON, no other text."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            json_mode=True
        )
        
        return self.llm.parse_json_response(response)
    
    def compare_with_job(self, resume_text: str, job_description: str) -> Dict:
        """
        Compare resume with job description
        
        Returns:
            {
                "match_score": 0-100,
                "matching_skills": [...],
                "missing_skills": [...],
                "recommendations": [...]
            }
        """
        
        system_prompt = """You are an ATS (Applicant Tracking System) expert.
Analyze how well a resume matches a job description."""

        prompt = f"""Compare this resume with the job description:

Resume:
{resume_text}

Job Description:
{job_description}

Provide JSON with:
1. "match_score": Overall match percentage (0-100)
2. "matching_skills": Skills that match the job requirements
3. "missing_skills": Required skills not in resume (prioritized)
4. "keyword_match": Percentage of job keywords found in resume
5. "recommendations": Specific suggestions to improve match

Return ONLY valid JSON, no other text."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            json_mode=True
        )
        
        return self.llm.parse_json_response(response)
    
    def get_ats_optimization(self, resume_text: str) -> Dict:
        """
        Get ATS optimization suggestions
        
        Returns:
            {
                "ats_score": 0-100,
                "issues": [...],
                "suggestions": [...]
            }
        """
        
        system_prompt = """You are an ATS optimization expert.
Provide specific, actionable advice to improve ATS compatibility."""

        prompt = f"""Analyze this resume for ATS compatibility:

Resume:
{resume_text}

Provide JSON with:
1. "ats_score": Overall ATS score (0-100)
2. "keyword_density": Percentage of relevant keywords
3. "format_issues": Formatting problems for ATS
4. "missing_sections": Important sections missing
5. "suggestions": Specific improvements (prioritized)

Return ONLY valid JSON, no other text."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            json_mode=True
        )
        
        return self.llm.parse_json_response(response)

        
        # Calculate scores
        scores = {
            "keyword_match": 0,
            "formatting": 0,
            "section_completeness": 0,
            "readability": 0
        }
        
        # Keyword matching
        if job_description:
            jd_words = set(job_description.lower().split())
            resume_words = set(resume_text.lower().split())
            common_words = jd_words.intersection(resume_words)
            scores["keyword_match"] = min(100, int((len(common_words) / max(len(jd_words), 1)) * 150))
        else:
            scores["keyword_match"] = 70  # Default if no JD
        
        # Check sections
        required_sections = ['experience', 'education', 'skills', 'projects']
        sections_found = sum(1 for section in required_sections if section in resume_text.lower())
        scores["section_completeness"] = int((sections_found / len(required_sections)) * 100)
        
        # Formatting (check for bullet points, proper structure)
        has_bullets = bool(re.search(r'[•\-\*]', resume_text))
        has_dates = bool(re.search(r'\d{4}', resume_text))
        has_proper_length = 500 < len(resume_text) < 5000
        
        formatting_score = 0
        if has_bullets: formatting_score += 35
        if has_dates: formatting_score += 35
        if has_proper_length: formatting_score += 30
        scores["formatting"] = formatting_score
        
        # Readability (sentence length, clarity)
        sentences = [s.strip() for s in re.split(r'[.!?]+', resume_text) if s.strip()]
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if 10 <= avg_sentence_length <= 25:
                scores["readability"] = 90
            elif 8 <= avg_sentence_length <= 30:
                scores["readability"] = 75
            else:
                scores["readability"] = 60
        else:
            scores["readability"] = 50
        
        # Overall score (weighted average)
        overall = int(
            scores["keyword_match"] * 0.35 +
            scores["formatting"] * 0.25 +
            scores["section_completeness"] * 0.25 +
            scores["readability"] * 0.15
        )
        
        return {
            "overall_score": overall,
            "keyword_match": scores["keyword_match"],
            "formatting": scores["formatting"],
            "section_completeness": scores["section_completeness"],
            "readability": scores["readability"],
            "details": {
                "has_bullets": has_bullets,
                "has_dates": has_dates,
                "proper_length": has_proper_length,
                "sections_found": sections_found,
                "total_sections": len(required_sections)
            }
        }
