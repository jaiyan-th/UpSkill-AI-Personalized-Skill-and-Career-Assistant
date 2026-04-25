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

        # Use LLM for analysis
        try:
            from app.services.llm_service_v2 import LLMServiceV2
            llm = LLMServiceV2()
            
            system_prompt = "You are a professional ATS (Applicant Tracking System) resume analyzer. Analyze the given resume for the target role and return a STRICT JSON response matching the UI format."
            
            prompt = f"""You are a recruiter-grade ATS (Applicant Tracking System) resume analyzer.

Analyze the resume deeply for the given target role and return STRICT JSON output.

INPUT:
Resume Text:
{text[:4000]}

Target Role:
{job_description or 'General Software Engineer'}

--------------------------------------

OUTPUT FORMAT (STRICT JSON ONLY):

{{
  "ats_score": number,
  "keywords_matched": number,
  "skills_detected": [],
  "missing_skills": [],
  "improvements": number,
  "suggestions": [],
  "fit_level": ""
}}

--------------------------------------

ANALYSIS LOGIC:

1. ATS SCORE (0–100):

Calculate using:

- Keyword Match (30%)
- Technical Skills Depth (25%)
- Project Strength (20%)
- Resume Structure (15%)
- Action Verbs & Impact (10%)

IMPORTANT SCORING RULES:
- If projects include APIs → +5 score
- If full stack (frontend + backend) → +10 score
- If security features (auth/encryption) → +5 score
- Do NOT over-penalize for missing Node.js if Python backend exists
- Be realistic (typical fresher: 60–75)

--------------------------------------

2. KEYWORDS MATCHED:

- Count relevant keywords using normalization:

Examples:
- "API", "REST", "REST API" → same
- "JS" → JavaScript
- "React.js" → React
- "SQL", "SQLite", "MySQL" → SQL category

Include keywords like:
frontend, backend, react, javascript, api, flask, sql, docker, git

Return total count.

--------------------------------------

3. SKILLS DETECTED:

- Extract ONLY skills present in resume
- Prioritize technical skills first
- Format cleanly:

Example:
["Python", "JavaScript", "React", "SQL", "Flask", "REST API", "Docker", "Git"]

- Include soft skills only if relevant

--------------------------------------

4. MISSING SKILLS:

Return HIGH-IMPACT missing skills for Full Stack:

Backend:
Node.js, Express

Database:
MongoDB / PostgreSQL

Frontend:
JavaScript (if not explicit), Tailwind, State Management

Other:
JWT Authentication, Deployment, CI/CD

Only include important ones (max 10).

--------------------------------------

5. IMPROVEMENTS:

Count major issues:
- Missing experience section
- No measurable results
- No deployment links
- Weak project descriptions

--------------------------------------

6. SUGGESTIONS:

Give 4–6 sharp, resume-specific suggestions:
- Max 12 words each
- Use action verbs

Examples:
- "Add Node.js backend project"
- "Include deployed project links"
- "Quantify project results with metrics"
- "Highlight authentication in backend systems"

--------------------------------------

7. FIT LEVEL:

Based on ATS score:
- 80+ → "Strong"
- 60–79 → "Moderate"
- <60 → "Weak"

--------------------------------------

STRICT RULES:

- Output ONLY JSON (no explanation)
- Do NOT hallucinate skills
- Do NOT include irrelevant technologies
- Prefer practical developer evaluation over keyword stuffing
- Be consistent and realistic
"""
            
            response = llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2,
                json_mode=True,
                retries=3
            )
            
            llm_result = llm.parse_json_response(response, fallback={})
            
            if not llm_result:
                raise Exception("LLM returned empty or invalid JSON")
                
        except Exception as e:
            print(f"LLM ATS Analysis failed, falling back to legacy: {e}")
            # Fallback to old logic
            cleaned = self._clean(text)
            resume_kw = self._keywords(cleaned)
            job_kw = self._keywords(self._clean(job_description)) if job_description else []
            kw_score, matched, missing = self._kw_match(resume_kw, job_kw)
            skills_score = self._skills_score(cleaned)
            section_score = self._section_score(text)
            fmt_score = self._fmt_score(text)
            ats_score = int(kw_score * 0.4 + skills_score * 0.3 + section_score * 0.2 + fmt_score * 0.1)
            extracted_skills = self._extract_skills_with_levels(text, cleaned)
            
            llm_result = {
                "ats_score": ats_score,
                "matched_keywords": matched[:20],
                "missing_skills": missing[:15],
                "suggestions": self._suggestions(ats_score, matched, missing, text),
                "skills_detected": [s["name"] for s in extracted_skills],
                "fit_level": "Strong" if ats_score >= 80 else ("Moderate" if ats_score >= 60 else "Weak")
            }

        return {
            "score": llm_result.get("ats_score", 0),
            "matched_keywords": llm_result.get("skills_detected", []), # UI needs an array
            "missing_keywords": llm_result.get("missing_skills", []),
            "suggestions": llm_result.get("suggestions", []),
            "fit_level": llm_result.get("fit_level", "Moderate"),
            "breakdown": {
                "keyword_match": 0,
                "skills_match": 0,
                "section_completeness": 0,
                "formatting": 0,
            },
            "extracted_data": {
                "skills": llm_result.get("skills_detected", []),
                "experience_years": 0,
                "education_level": "",
                "technical_skills": [],
                "soft_skills": [],
            },
            "extracted_text": text,
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
