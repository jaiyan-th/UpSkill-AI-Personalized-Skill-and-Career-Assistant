"""
Mock Interview Engine - AI-powered technical interviews
Uses: Prompt Chaining, Role-based Prompting, Memory Injection
"""

import json
from typing import Dict, List, Optional
from .llm_service import LLMService

class InterviewEngine:
    def __init__(self):
        self.llm = LLMService()
        self.conversation_history = []
        self.interview_context = {}
        self.questions_asked = []
        self.answers_given = []
    
    def start_interview(
        self, 
        role: str, 
        level: str, 
        skills: List[Dict],
        resume_summary: str = None,
        job_description: str = None
    ) -> Dict:
        """
        Start a new mock interview based on target job role
        
        Args:
            role: Target role (e.g., "Business Analyst", "Product Manager")
            level: "Entry", "Mid-level", or "Senior"
            skills: List of candidate skills from resume
            resume_summary: Resume summary
            job_description: Target job description
        
        Returns:
            {
                "question": "First interview question",
                "context": "Interview context",
                "session_id": "unique_id"
            }
        """
        
        # Reset state
        self.conversation_history = []
        self.questions_asked = []
        self.answers_given = []
        
        # Store context
        self.interview_context = {
            "role": role,
            "level": level,
            "skills": skills,
            "resume_summary": resume_summary,
            "job_description": job_description
        }
        
        # Build skills summary
        skill_names = [s.get('name', s) if isinstance(s, dict) else s for s in skills]
        skills_text = ', '.join(skill_names) if skill_names else 'No specific skills listed'
        
        system_prompt = f"""You are an experienced technical interviewer conducting a {level} level interview for a {role} position.

INTERVIEW OBJECTIVES:
1. Ask DIVERSE question types: behavioral, coding, problem-solving, aptitude, and code review
2. Tailor questions to the candidate's resume and target role
3. Evaluate both CONTENT and COMMUNICATION skills
4. Assess clarity, fluency, and articulation
5. Check if candidate's skills match job requirements

QUESTION TYPES TO USE:
- BEHAVIORAL: "Tell me about a time when..." (situational questions)
- CODING: "Write a function that..." (implementation questions)
- PROBLEM SOLVING: "How would you solve..." (aptitude/logic questions)
- CODE REVIEW: "Find the error in this code..." (debugging questions)

CANDIDATE PROFILE:
- Target Role: {role}
- Experience Level: {level}
- Current Skills: {skills_text}

=== CANDIDATE RESUME ===
{resume_summary if resume_summary else "No resume text provided."}
========================
{f"- Target Job Requirements: {job_description}" if job_description else ""}

COMMUNICATION EVALUATION:
- Note clarity and structure of answers
- Assess fluency and confidence
- Evaluate ability to explain complex concepts simply
- Check for relevant examples and experience

Start with a warm introduction and your first question. Mix question types throughout the interview."""

        # Generate first question
        prompt = f"""Begin the interview for {role} position. 

1. Introduce yourself briefly as the interviewer
2. Ask your first question (choose from: behavioral, coding, problem-solving, or code review)
3. The question should be relevant to {role} and test both knowledge AND communication
4. Make it realistic - something they would face in this role

Keep it conversational and professional."""

        self.conversation_history.append({
            "role": "system",
            "content": system_prompt
        })
        
        self.conversation_history.append({
            "role": "user",
            "content": prompt
        })
        
        try:
            response = self.llm.generate_with_history(
                messages=self.conversation_history,
                temperature=0.7
            )
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            return {
                "question": response,
                "context": self.interview_context,
                "question_number": 1
            }
        except Exception as e:
            print(f"LLM Error in start_interview: {e}")
            # Fallback to predefined questions
            fallback_questions = {
                "Software Developer": "Hello! I'm excited to interview you for the Software Developer position. Let's start with a behavioral question: Can you tell me about a challenging project you worked on and how you approached solving the technical problems you encountered?",
                "Full Stack Developer": "Welcome! I'll be conducting your interview for the Full Stack Developer role. To begin, can you describe a time when you had to optimize both frontend and backend performance in an application? What strategies did you use?",
                "Data Scientist": "Hello! Let's begin your Data Scientist interview. Can you walk me through a data analysis project where you had to clean messy data and extract meaningful insights? What tools and techniques did you use?",
                "Business Analyst": "Welcome! I'm here to interview you for the Business Analyst position. Let's start: Can you describe a situation where you had to gather requirements from multiple stakeholders with conflicting priorities? How did you handle it?",
                "Product Manager": "Hello! Let's begin your Product Manager interview. Can you tell me about a time when you had to make a difficult product decision with limited data? What was your approach?",
                "default": f"Hello! I'm excited to interview you for the {role} position. Let's start with a behavioral question: Can you tell me about a challenging situation you faced in your previous role and how you handled it?"
            }
            
            fallback_question = fallback_questions.get(role, fallback_questions["default"])
            
            self.conversation_history.append({
                "role": "assistant",
                "content": fallback_question
            })
            
            return {
                "question": fallback_question,
                "context": self.interview_context,
                "question_number": 1
            }
    
    def process_answer(self, user_answer: str, audio_transcript: str = None, speech_metrics: Dict = None) -> Dict:
        """
        Process candidate's answer and generate next question
        Evaluates BOTH content AND communication skills
        NOW INCLUDES: Fluency and pronunciation analysis from speech
        
        Args:
            user_answer: Candidate's answer (text)
            audio_transcript: Raw transcript from speech recognition (optional)
            speech_metrics: Speech analysis metrics (optional) {
                "words_per_minute": 120-180,
                "pause_count": 5,
                "filler_words": ["um", "uh", "like"],
                "pronunciation_clarity": 0-100
            }
        
        Returns:
            {
                "feedback": "Brief feedback on answer",
                "next_question": "Next question or follow-up",
                "score": 0-10 for this answer,
                "communication_score": 0-10 for communication quality,
                "content_score": 0-10 for content quality,
                "fluency_score": 0-10 for speech fluency,
                "pronunciation_score": 0-10 for pronunciation clarity,
                "speech_analysis": {...}
            }
        """
        
        # Add user answer to history
        self.conversation_history.append({
            "role": "user",
            "content": user_answer
        })
        
        self.answers_given.append(user_answer)
        
        # Analyze speech metrics if provided
        fluency_analysis = self._analyze_fluency(user_answer, audio_transcript, speech_metrics)
        
        # Prompt for evaluation - FOCUS ON COMMUNICATION + CONTENT + FLUENCY
        evaluation_prompt = f"""The candidate just answered. Now evaluate BOTH content and communication:

CONTENT EVALUATION (0-10):
- Is the answer relevant and accurate?
- Does it show understanding of the role?
- Are examples provided?
- Is reasoning clear?
- For coding: Is the solution correct and efficient?
- For problem-solving: Is the approach logical?
- For code review: Did they identify the error correctly?

COMMUNICATION EVALUATION (0-10):
- Clarity: Is the answer well-structured and easy to understand?
- Fluency: Does it flow naturally without confusion?
- Articulation: Are ideas expressed clearly?
- Confidence: Does the answer show confidence in knowledge?
- Conciseness: Is it appropriately detailed without rambling?

{f'''
SPEECH ANALYSIS (from audio):
- Words per minute: {speech_metrics.get("words_per_minute", "N/A")}
- Pause count: {speech_metrics.get("pause_count", "N/A")}
- Filler words used: {", ".join(speech_metrics.get("filler_words", []))}
- Pronunciation clarity: {speech_metrics.get("pronunciation_clarity", "N/A")}%
''' if speech_metrics else ''}

Provide feedback and ask your next question. VARY THE QUESTION TYPE:
- If last was behavioral, try coding or problem-solving
- If last was coding, try behavioral or code review
- Mix it up to test different skills

Format your response as:
CONTENT_SCORE: [0-10]
COMMUNICATION_SCORE: [0-10]
FEEDBACK: [2-3 sentences covering both content and communication]
NEXT: [your next question - choose from: BEHAVIORAL, CODING, PROBLEM SOLVING, or CODE REVIEW for {self.interview_context.get('role', 'this role')}]

Be encouraging but honest. Focus on helping them improve both knowledge and communication."""

        self.conversation_history.append({
            "role": "user",
            "content": evaluation_prompt
        })
        
        try:
            response = self.llm.generate_with_history(
                messages=self.conversation_history,
                temperature=0.7
            )
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
        except Exception as e:
            print(f"LLM Error in process_answer: {e}")
            # Fallback response
            response = f"""CONTENT_SCORE: 7
COMMUNICATION_SCORE: 7
FEEDBACK: Thank you for your answer. You provided good insights and explained your approach clearly. For your next question, let's explore a different aspect.
NEXT: Can you describe how you would handle a situation where you need to learn a new technology quickly for a project deadline?"""
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
        
        # Parse response
        feedback = ""
        content_score = 5
        communication_score = 5
        next_question = response
        
        if "CONTENT_SCORE:" in response:
            parts = response.split("CONTENT_SCORE:")
            if len(parts) > 1:
                score_part = parts[1].split("COMMUNICATION_SCORE:")[0].strip()
                try:
                    content_score = int(score_part)
                except:
                    content_score = 5
        
        if "COMMUNICATION_SCORE:" in response:
            parts = response.split("COMMUNICATION_SCORE:")
            if len(parts) > 1:
                score_part = parts[1].split("FEEDBACK:")[0].strip()
                try:
                    communication_score = int(score_part)
                except:
                    communication_score = 5
        
        if "FEEDBACK:" in response:
            parts = response.split("FEEDBACK:")
            if len(parts) > 1:
                feedback_part = parts[1].split("NEXT:")[0].strip()
                feedback = feedback_part
        
        if "NEXT:" in response:
            parts = response.split("NEXT:")
            if len(parts) > 1:
                next_question = parts[1].strip()
        
        # Overall score is average of content and communication
        overall_score = int((content_score + communication_score) / 2)
        
        self.questions_asked.append(next_question)
        
        return {
            "feedback": feedback,
            "next_question": next_question,
            "score": overall_score,
            "content_score": content_score,
            "communication_score": communication_score,
            "fluency_score": fluency_analysis.get("fluency_score", 5),
            "pronunciation_score": fluency_analysis.get("pronunciation_score", 5),
            "speech_analysis": fluency_analysis,
            "question_number": len(self.questions_asked)
        }
    
    def _analyze_fluency(self, text_answer: str, audio_transcript: str = None, speech_metrics: Dict = None) -> Dict:
        """
        Analyze fluency and pronunciation from speech
        
        Args:
            text_answer: The written/typed answer
            audio_transcript: Raw transcript from speech recognition
            speech_metrics: Speech analysis metrics
        
        Returns:
            {
                "fluency_score": 0-10,
                "pronunciation_score": 0-10,
                "words_per_minute": 120-180,
                "pause_analysis": {...},
                "filler_word_count": 5,
                "clarity_percentage": 85,
                "feedback": "Detailed fluency feedback"
            }
        """
        
        if not speech_metrics and not audio_transcript:
            # No speech data, return neutral scores
            return {
                "fluency_score": 5,
                "pronunciation_score": 5,
                "words_per_minute": 0,
                "pause_analysis": {"count": 0, "average_duration": 0},
                "filler_word_count": 0,
                "clarity_percentage": 0,
                "feedback": "No speech data available for analysis",
                "has_speech_data": False
            }
        
        # Calculate basic metrics
        word_count = len(text_answer.split())
        
        # Analyze filler words
        filler_words = ["um", "uh", "like", "you know", "actually", "basically", "literally"]
        filler_count = sum(text_answer.lower().count(filler) for filler in filler_words)
        filler_ratio = filler_count / max(word_count, 1)
        
        # Get speech metrics
        wpm = speech_metrics.get("words_per_minute", 0) if speech_metrics else 0
        pause_count = speech_metrics.get("pause_count", 0) if speech_metrics else 0
        pronunciation_clarity = speech_metrics.get("pronunciation_clarity", 80) if speech_metrics else 80
        
        # Calculate fluency score (0-10)
        fluency_score = 10
        
        # Deduct for too slow or too fast
        if wpm > 0:
            if wpm < 100:  # Too slow
                fluency_score -= min(3, (100 - wpm) / 20)
            elif wpm > 200:  # Too fast
                fluency_score -= min(3, (wpm - 200) / 20)
        
        # Deduct for excessive pauses
        if pause_count > 5:
            fluency_score -= min(2, (pause_count - 5) / 3)
        
        # Deduct for filler words
        if filler_ratio > 0.05:  # More than 5% filler words
            fluency_score -= min(3, filler_ratio * 20)
        
        fluency_score = max(0, min(10, fluency_score))
        
        # Calculate pronunciation score (0-10)
        pronunciation_score = (pronunciation_clarity / 100) * 10
        
        # Generate feedback
        feedback_parts = []
        
        if wpm > 0:
            if wpm < 100:
                feedback_parts.append(f"Speaking pace is slow ({wpm} WPM). Try to speak more confidently.")
            elif wpm > 200:
                feedback_parts.append(f"Speaking pace is fast ({wpm} WPM). Slow down for clarity.")
            else:
                feedback_parts.append(f"Good speaking pace ({wpm} WPM).")
        
        if pause_count > 5:
            feedback_parts.append(f"Frequent pauses detected ({pause_count}). Practice to improve flow.")
        elif pause_count > 0:
            feedback_parts.append(f"Natural pauses ({pause_count}). Good pacing.")
        
        if filler_count > 3:
            feedback_parts.append(f"Reduce filler words ({filler_count} detected: {', '.join(speech_metrics.get('filler_words', []))}).")
        elif filler_count > 0:
            feedback_parts.append(f"Minimal filler words ({filler_count}). Good!")
        
        if pronunciation_clarity < 70:
            feedback_parts.append(f"Pronunciation clarity needs improvement ({pronunciation_clarity}%).")
        elif pronunciation_clarity < 85:
            feedback_parts.append(f"Pronunciation is good ({pronunciation_clarity}%).")
        else:
            feedback_parts.append(f"Excellent pronunciation clarity ({pronunciation_clarity}%).")
        
        return {
            "fluency_score": round(fluency_score, 1),
            "pronunciation_score": round(pronunciation_score, 1),
            "words_per_minute": wpm,
            "pause_analysis": {
                "count": pause_count,
                "severity": "high" if pause_count > 8 else "medium" if pause_count > 5 else "low"
            },
            "filler_word_count": filler_count,
            "filler_word_ratio": round(filler_ratio * 100, 1),
            "clarity_percentage": pronunciation_clarity,
            "feedback": " ".join(feedback_parts),
            "has_speech_data": True
        }
    
    def end_interview(self) -> Dict:
        """
        End interview and provide comprehensive evaluation
        Includes detailed communication, fluency, and pronunciation assessment
        
        Returns:
            {
                "overall_score": 0-100,
                "technical_accuracy": 0-10,
                "communication_clarity": 0-10,
                "fluency": 0-10,
                "pronunciation": 0-10,
                "confidence": 0-10,
                "role_fit": 0-10,
                "strengths": [...],
                "weaknesses": [...],
                "communication_feedback": "...",
                "fluency_feedback": "...",
                "pronunciation_feedback": "...",
                "skill_gaps": [...],
                "recommendations": [...],
                "speech_metrics_summary": {...}
            }
        """
        
        # Build conversation summary
        qa_pairs = []
        for i in range(1, len(self.conversation_history), 2):
            if i < len(self.conversation_history):
                if self.conversation_history[i]["role"] == "user":
                    question = self.conversation_history[i-1]["content"] if i > 0 else ""
                    answer = self.conversation_history[i]["content"]
                    qa_pairs.append({
                        "question": question,
                        "answer": answer
                    })
        
        system_prompt = """You are an expert HR interviewer providing final evaluation.
Analyze the interview comprehensively focusing on BOTH technical knowledge AND communication skills.
Always return valid JSON format."""

        role = self.interview_context.get('role', 'the position')
        level = self.interview_context.get('level', 'Mid-level')
        skills = self.interview_context.get('skills', [])
        
        prompt = f"""Evaluate this complete interview for {role} position:

CANDIDATE PROFILE:
- Target Role: {role}
- Experience Level: {level}
- Resume Skills: {json.dumps(skills)}

INTERVIEW TRANSCRIPT:
{json.dumps(qa_pairs[-10:], indent=2)}

Provide comprehensive evaluation as JSON:
{{
  "overall_score": 0-100 (overall performance),
  "technical_accuracy": 0-10 (correctness and depth of answers),
  "communication_clarity": 0-10 (how clearly they expressed ideas),
  "fluency": 0-10 (natural flow, no confusion or rambling),
  "confidence": 0-10 (confidence level in responses),
  "role_fit": 0-10 (suitability for {role} position),
  "articulation": 0-10 (ability to explain complex concepts),
  
  "strengths": ["specific strength 1", "specific strength 2", "specific strength 3"],
  "weaknesses": ["specific weakness 1", "specific weakness 2"],
  
  "communication_feedback": "2-3 sentences on communication quality, fluency, clarity",
  "technical_feedback": "2-3 sentences on technical knowledge and role fit",
  
  "skill_gaps": [
    {{"skill": "technology or concept", "reason": "why it's needed based on answers and {role}"}}
  ],
  
  "communication_skill_gaps": [
    {{"aspect": "fluency/clarity/structure", "reason": "why they need to improve this communication trait"}}
  ],
  
  "recommendations": [
    "specific actionable advice 1",
    "specific actionable advice 2",
    "specific actionable advice 3"
  ],
  
  "topics_covered": ["topic1", "topic2", "topic3"],
  "topics_to_practice": ["topic1", "topic2"],
  "ready_for_role": true/false,
  "detailed_feedback": "3-4 paragraph comprehensive summary covering technical skills, communication ability, and readiness for {role}"
}}

IMPORTANT:
- Be honest about skill gaps compared to {role} requirements
- Evaluate communication separately from technical knowledge
- Provide specific, actionable feedback
- Identify missing skills needed for {role}

Return ONLY valid JSON, no other text."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            json_mode=True,
            max_tokens=3000
        )
        
        evaluation = self.llm.parse_json_response(response)
        
        # Add interview metadata
        evaluation["questions_asked"] = len(self.questions_asked)
        evaluation["duration_minutes"] = len(self.conversation_history) * 2  # Estimate
        evaluation["target_role"] = role
        evaluation["experience_level"] = level
        
        return evaluation
    
    def generate_question(
        self, 
        topic: str, 
        difficulty: str,
        question_type: str = "technical"
    ) -> Dict:
        """
        Generate a specific interview question
        
        Args:
            topic: Topic (e.g., "React Hooks", "System Design")
            difficulty: "Easy", "Medium", "Hard"
            question_type: "technical", "behavioral", "system_design", "coding"
        
        Returns:
            {
                "question": "The question",
                "expected_points": ["point1", "point2"],
                "difficulty": "Medium",
                "type": "technical"
            }
        """
        
        system_prompt = f"""You are a technical interviewer creating {question_type} interview questions.
Create realistic, practical questions that test real understanding."""

        prompt = f"""Generate a {difficulty} level {question_type} interview question about {topic}.

The question should:
1. Be realistic and practical
2. Test understanding, not just memorization
3. Be clear and specific
4. Match the difficulty level
5. Be answerable in 3-5 minutes

Provide JSON:
{{
  "question": "The interview question",
  "expected_points": ["key point 1", "key point 2", "key point 3"],
  "difficulty": "{difficulty}",
  "type": "{question_type}",
  "hints": ["hint if stuck"]
}}

Return ONLY valid JSON, no other text."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            json_mode=True
        )
        
        return self.llm.parse_json_response(response)
    
    def evaluate_single_answer(
        self, 
        question: str, 
        answer: str,
        expected_points: List[str] = None
    ) -> Dict:
        """
        Evaluate a single answer
        
        Returns:
            {
                "score": 0-10,
                "feedback": "Detailed feedback",
                "what_was_good": [...],
                "what_to_improve": [...],
                "better_answer": "Suggested better answer"
            }
        """
        
        system_prompt = """You are an expert technical interviewer evaluating answers.
Provide constructive, specific feedback that helps candidates improve."""

        prompt = f"""Evaluate this interview answer:

Question: {question}
Candidate's Answer: {answer}
{f"Expected Points: {json.dumps(expected_points)}" if expected_points else ""}

Provide JSON evaluation:
{{
  "score": 0-10,
  "feedback": "Detailed feedback paragraph",
  "what_was_good": ["good point 1", "good point 2"],
  "what_to_improve": ["improvement 1", "improvement 2"],
  "missing_points": ["missed point 1"],
  "better_answer": "Example of a strong answer"
}}

Be constructive and specific. Help them learn.
Return ONLY valid JSON, no other text."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.4,
            json_mode=True
        )
        
        return self.llm.parse_json_response(response)
