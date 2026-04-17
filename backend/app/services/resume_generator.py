import re
from typing import Dict, Any
from app.services.groq_client import groq_generate


def generate_resume(user_data: Dict[str, Any]) -> Dict[str, Any]:
    prompt = f"""Generate a professional ATS-friendly resume based on the following details.
Use bullet points, action verbs, and structured formatting.

Name: {user_data.get('name')}
Headline: {user_data.get('headline')}
Email: {user_data.get('email', '')}
Phone: {user_data.get('phone', '')}
Location: {user_data.get('location', '')}
LinkedIn: {user_data.get('linkedin', '')}
Summary: {user_data.get('summary', '')}
Education: {user_data.get('education')}
Skills: {user_data.get('skills')}
Projects: {user_data.get('projects')}
Experience: {user_data.get('experience')}
Certifications: {user_data.get('certifications', '')}
Achievements: {user_data.get('achievements', '')}

Output format:
SUMMARY:
[2-3 sentence professional summary]

SKILLS:
[Bullet list of skills by category]

EXPERIENCE:
[Job Title at Company (Date)
- Action verb bullet points with quantified achievements]

PROJECTS:
[Project Name
- Bullet points with technologies and impact]

EDUCATION:
[Degree, Institution, details]

CERTIFICATIONS:
[List if provided]

ACHIEVEMENTS:
[List if provided]"""

    resume_text = groq_generate(
        prompt,
        system="You are a professional resume writer. Create ATS-optimized resumes.",
        max_tokens=2000,
    )

    if not resume_text:
        raise Exception("Groq API key not configured or request failed")

    return {"success": True, "resume": _parse_resume(resume_text, user_data), "raw_text": resume_text}


def _parse_resume(text: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
    sections: Dict[str, Any] = {
        "name": user_data.get("name", ""),
        "headline": user_data.get("headline", ""),
        "email": user_data.get("email", ""),
        "phone": user_data.get("phone", ""),
        "location": user_data.get("location", ""),
        "linkedin": user_data.get("linkedin", ""),
        "summary": "", "skills": [], "experience": [], "projects": [], "education": "",
        "certifications": [], "achievements": [],
    }

    def extract(pattern):
        m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return m.group(1).strip() if m else ""

    sections["summary"] = extract(r"SUMMARY:?\s*\n(.*?)(?=\n\n|\nSKILLS:|\nEXPERIENCE:|$)")

    skills_text = extract(r"SKILLS:?\s*\n(.*?)(?=\n\n|\nEXPERIENCE:|\nPROJECTS:|$)")
    sections["skills"] = [s.strip("- •*").strip() for s in skills_text.split("\n") if s.strip().startswith(("-", "•", "*"))]

    exp_text = extract(r"EXPERIENCE:?\s*\n(.*?)(?=\n\n|\nPROJECTS:|\nEDUCATION:|$)")
    sections["experience"] = _parse_bullets(exp_text)

    proj_text = extract(r"PROJECTS:?\s*\n(.*?)(?=\n\n|\nEDUCATION:|\nCERTIFICATIONS:|$)")
    sections["projects"] = _parse_bullets(proj_text)

    sections["education"] = extract(r"EDUCATION:?\s*\n(.*?)(?=\n\n|\nCERTIFICATIONS:|$)")

    cert_text = extract(r"CERTIFICATIONS:?\s*\n(.*?)(?=\n\n|\nACHIEVEMENTS:|$)")
    sections["certifications"] = [c.strip("- •*").strip() for c in cert_text.split("\n") if c.strip()]

    ach_text = extract(r"ACHIEVEMENTS:?\s*\n(.*?)$")
    sections["achievements"] = [a.strip("- •*").strip() for a in ach_text.split("\n") if a.strip()]

    return sections


def _parse_bullets(text: str) -> list:
    items, current = [], {"title": "", "bullets": []}
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            if current["title"] or current["bullets"]:
                items.append(current)
                current = {"title": "", "bullets": []}
        elif line.startswith(("-", "•", "*")):
            current["bullets"].append(line.strip("- •*").strip())
        else:
            if current["title"] or current["bullets"]:
                items.append(current)
            current = {"title": line, "bullets": []}
    if current["title"] or current["bullets"]:
        items.append(current)
    return items
