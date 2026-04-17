import re
from io import BytesIO
from typing import List, Tuple, Dict
from collections import Counter

try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


class ATSAnalyzer:
    TECHNICAL = ["python", "java", "javascript", "react", "node", "sql", "aws", "docker",
                 "kubernetes", "git", "api", "rest", "machine learning", "ai", "data", "cloud",
                 "devops", "frontend", "backend", "agile", "ci/cd", "typescript", "angular", "vue",
                 "mongodb", "postgresql", "redis", "kafka", "spark", "hadoop", "tensorflow", "pytorch",
                 "scikit-learn", "pandas", "numpy", "flask", "django", "spring", "express", "graphql",
                 "microservices", "linux", "bash", "powershell", "jenkins", "terraform", "ansible",
                 "figma", "sketch", "adobe xd", "photoshop", "illustrator", "html", "css", "sass",
                 "tailwind", "bootstrap", "webpack", "vite", "jest", "cypress", "selenium", "jira",
                 "confluence", "tableau", "power bi", "excel", "r", "matlab", "c++", "c#", "go",
                 "rust", "swift", "kotlin", "flutter", "react native", "unity", "unreal"]
    SOFT = ["leadership", "communication", "teamwork", "problem solving", "analytical", "creative",
            "critical thinking", "time management", "adaptability", "collaboration", "presentation"]
    VERBS = ["developed", "built", "designed", "implemented", "led", "created",
             "managed", "improved", "optimized", "delivered", "achieved", "launched",
             "architected", "deployed", "automated", "streamlined", "spearheaded"]

    def analyze_resume(self, filename: str, content: bytes, job_description: str = "") -> dict:
        text = self._extract_text(filename, content)
        if not text:
            raise Exception("Failed to extract text from file")

        cleaned = self._clean(text)
        resume_kw = self._keywords(cleaned)
        job_kw = self._keywords(self._clean(job_description)) if job_description else []

        kw_score, matched, missing = self._kw_match(resume_kw, job_kw)
        skills_score = self._skills_score(cleaned)
        section_score = self._section_score(text)
        fmt_score = self._fmt_score(text)

        ats_score = int(kw_score * 0.4 + skills_score * 0.3 + section_score * 0.2 + fmt_score * 0.1)

        # Extract skills with proficiency levels
        extracted_skills = self._extract_skills_with_levels(text, cleaned)
        
        # Extract experience and education
        experience_years = self._extract_experience_years(text)
        education_level = self._extract_education(text)

        return {
            "score": ats_score,
            "matched_keywords": matched[:20],
            "missing_keywords": missing[:15],
            "suggestions": self._suggestions(ats_score, matched, missing, text),
            "breakdown": {
                "keyword_match": int(kw_score),
                "skills_match": int(skills_score),
                "section_completeness": int(section_score),
                "formatting": int(fmt_score),
            },
            "extracted_data": {
                "skills": extracted_skills,
                "experience_years": experience_years,
                "education_level": education_level,
                "technical_skills": [s for s in extracted_skills if s["category"] == "technical"],
                "soft_skills": [s for s in extracted_skills if s["category"] == "soft"],
            },
        }

    def _extract_text(self, filename: str, content: bytes) -> str:
        if filename.lower().endswith(".pdf") and HAS_PDF:
            reader = PyPDF2.PdfReader(BytesIO(content))
            return "\n".join(p.extract_text() or "" for p in reader.pages)
        if filename.lower().endswith(".docx") and HAS_DOCX:
            doc = Document(BytesIO(content))
            return "\n".join(p.text for p in doc.paragraphs)
        return content.decode("utf-8", errors="ignore")

    def _clean(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _keywords(self, text: str) -> List[str]:
        words = text.split()
        freq = Counter(words)
        stopwords = {"the", "and", "for", "with", "that", "this", "are", "was", "has", "have"}
        return [w for w, _ in freq.most_common(60) if w not in stopwords and len(w) > 2]

    def _kw_match(self, resume_kw, job_kw) -> Tuple[float, List[str], List[str]]:
        if not job_kw:
            job_kw = [k.replace(" ", "") for k in self.TECHNICAL + self.SOFT]
        r, j = set(resume_kw), set(job_kw)
        matched = list(r & j)
        missing = list(j - r)
        score = (len(matched) / len(j) * 100) if j else 80.0
        return score, matched, missing

    def _skills_score(self, text: str) -> float:
        found = sum(1 for s in self.TECHNICAL + self.SOFT if s in text)
        return min((found / len(self.TECHNICAL + self.SOFT)) * 150, 100)

    def _section_score(self, text: str) -> float:
        t = text.lower()
        found = sum(1 for s in ["experience", "education", "skills", "summary"] if s in t)
        score = (found / 4) * 100
        if any(x in t for x in ["email", "@", "phone", "linkedin"]):
            score = min(score + 10, 100)
        return score

    def _fmt_score(self, text: str) -> float:
        score = 100.0
        if not any(c in text for c in ["•", "-", "*"]):
            score -= 20
        wc = len(text.split())
        if wc < 200:
            score -= 30
        elif wc > 1000:
            score -= 10
        if sum(1 for v in self.VERBS if v in text.lower()) < 3:
            score -= 20
        return max(score, 0)

    def _suggestions(self, score, matched, missing, text) -> List[str]:
        tips = []
        if score < 60:
            tips.append("Your resume needs significant improvement to pass ATS systems.")
        elif score < 80:
            tips.append("Your resume is good but could be further optimized.")
        else:
            tips.append("Your resume is well-optimized for ATS systems.")
        if len(missing) > 10:
            tips.append(f"Add more relevant keywords — {len(missing)} are missing from the job description.")
        if len(matched) < 5:
            tips.append("Include more industry-specific technical skills and keywords.")
        if sum(1 for v in self.VERBS if v in text.lower()) < 5:
            tips.append("Use more action verbs: Developed, Built, Designed, Implemented, Led.")
        if "experience" not in text.lower():
            tips.append("Add a clear 'Experience' section with your work history.")
        if len(text.split()) < 300:
            tips.append("Expand your resume with more details about your achievements.")
        return tips[:6]

    def _extract_skills_with_levels(self, text: str, cleaned: str) -> List[Dict]:
        """Extract skills and estimate proficiency levels based on context"""
        skills = []
        text_lower = text.lower()
        
        # Check technical skills
        for skill in self.TECHNICAL:
            if skill in cleaned:
                level = self._estimate_skill_level(skill, text_lower)
                skills.append({
                    "name": skill.title(),
                    "level": level,
                    "category": "technical"
                })
        
        # Check soft skills
        for skill in self.SOFT:
            if skill in cleaned:
                skills.append({
                    "name": skill.title(),
                    "level": "Intermediate",
                    "category": "soft"
                })
        
        return skills

    def _estimate_skill_level(self, skill: str, text: str) -> str:
        """Estimate skill level based on context clues"""
        skill_context = []
        lines = text.split('\n')
        
        for line in lines:
            if skill in line.lower():
                skill_context.append(line.lower())
        
        context_text = ' '.join(skill_context)
        
        # Advanced indicators
        advanced_keywords = ['expert', 'advanced', 'lead', 'architect', 'senior', 
                            'mastery', 'proficient', '5+ years', '6+ years', '7+ years']
        if any(kw in context_text for kw in advanced_keywords):
            return "Advanced"
        
        # Intermediate indicators
        intermediate_keywords = ['experience', 'worked with', 'developed', 'built',
                                'implemented', '2+ years', '3+ years', '4+ years']
        if any(kw in context_text for kw in intermediate_keywords):
            return "Intermediate"
        
        # Default to beginner if just mentioned
        return "Beginner"

    def _extract_experience_years(self, text: str) -> int:
        """Extract total years of experience from resume"""
        text_lower = text.lower()
        
        # Look for explicit experience statements
        patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'experience[:\s]+(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s+(?:in|as)',
        ]
        
        max_years = 0
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                years = int(match)
                max_years = max(max_years, years)
        
        return max_years

    def _extract_education(self, text: str) -> str:
        """Extract highest education level from resume"""
        text_lower = text.lower()
        
        if any(term in text_lower for term in ['phd', 'ph.d', 'doctorate']):
            return "PhD"
        elif any(term in text_lower for term in ['master', 'msc', 'm.sc', 'mba', 'm.b.a', 'ms', 'm.s']):
            return "Master's"
        elif any(term in text_lower for term in ['bachelor', 'bsc', 'b.sc', 'btech', 'b.tech', 'be', 'b.e', 'ba', 'b.a']):
            return "Bachelor's"
        elif any(term in text_lower for term in ['diploma', 'associate']):
            return "Diploma"
        else:
            return "High School"
