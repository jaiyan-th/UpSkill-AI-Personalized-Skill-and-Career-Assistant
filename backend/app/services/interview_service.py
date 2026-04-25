"""
Enhanced Interview Service - Complete Mock Interview System
Features: Dynamic questions, adaptive difficulty, voice analysis, code evaluation
"""

import json
import time
from typing import Dict, List, Optional
from .llm_service import LLMService
from app.database import get_db

class InterviewService:
    def __init__(self):
        self.llm = LLMService()
        self.question_types = ['behavioral', 'technical', 'coding', 'problem_solving']
        
    def create_session(self, user_id: int, role: str, level: str) -> Dict:
        """
        Create new interview session in database
        
        Args:
            user_id: User ID
            role: Target role (e.g., "Software Developer")
            level: Experience level (Entry/Mid-level/Senior)
            
        Returns:
            Session data with session_id
        """
        db = get_db()
        
        # Verify user exists
        user = db.execute("SELECT id FROM users WHERE id = ?", [user_id]).fetchone()
        if not user:
            raise ValueError(f"User with id {user_id} does not exist")
        
        # Calculate duration based on level (3-5 minutes)
        duration_minutes = 3 if level == 'Entry' else 4 if level == 'Mid-level' else 5
        
        cursor = db.execute(
            """INSERT INTO interview_sessions 
               (user_id, role, level, duration_minutes, status, started_at)
               VALUES (?, ?, ?, ?, 'in_progress', CURRENT_TIMESTAMP)""",
            [user_id, role, level, duration_minutes]
        )
        db.commit()
        
        session_id = cursor.lastrowid
        
        return {
            'session_id': session_id,
            'role': role,
            'level': level,
            'duration_minutes': duration_minutes,
            'total_questions': 5,  # Fixed 5 questions per interview
            'current_question_index': 0
        }
    
    def generate_question(
        self, 
        role: str, 
        level: str, 
        question_index: int,
        previous_answers: List[Dict] = None
    ) -> Dict:
        # Question type sequence — 5 questions per interview
        # text_required=True means the candidate must type an answer
        question_types_sequence = [
            {'type': 'behavioral',    'text_required': False},  # Q1: Speak/voice
            {'type': 'technical',     'text_required': False},  # Q2: Speak/voice
            {'type': 'coding',        'text_required': True},   # Q3: Must type code
            {'type': 'aptitude',      'text_required': True},   # Q4: Must type solution
            {'type': 'behavioral',    'text_required': False},  # Q5: Speak/voice
        ]
        
        q_meta = question_types_sequence[question_index % 5]
        question_type = q_meta['type']
        text_required = q_meta['text_required']
        
        difficulty_adjustment = ""
        if previous_answers and len(previous_answers) > 0:
            avg_score = sum(a.get('score', 5) for a in previous_answers) / len(previous_answers)
            if avg_score >= 8:
                difficulty_adjustment = "The candidate is performing well. Increase difficulty slightly."
            elif avg_score <= 4:
                difficulty_adjustment = "The candidate is struggling. Keep questions moderate."
        
        system_prompt = f"""You are a technical interviewer for {role} at {level} level.
Generate ONE concise interview question of type: {question_type}.
{difficulty_adjustment}
Return ONLY the question text, nothing else."""

        try:
            question_text = self.llm.generate(
                prompt=f"Generate a {question_type} interview question for {role} ({level} level).",
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=120
            )
            
            return {
                'type': question_type,
                'text': question_text.strip(),
                'index': question_index,
                'text_required': text_required
            }
            
        except Exception as e:
            fallback_questions = {
                'behavioral': "Tell me about a challenging project you worked on and how you overcame obstacles.",
                'technical': f"Explain the key technical concepts and best practices for {role}.",
                'coding': "Write a function that reverses a string without using built-in reverse methods.",
                'aptitude': "Given an array of integers, find the two numbers that add up to a target sum. Write your solution.",
                'writing': "Describe how you would architect a scalable microservices system for an e-commerce platform."
            }
            
            return {
                'type': question_type,
                'text': fallback_questions.get(question_type, "Tell me about your experience."),
                'index': question_index,
                'text_required': text_required
            }
    
    def evaluate_answer(
        self,
        question: str,
        answer: str,
        question_type: str,
        role: str,
        level: str
    ) -> Dict:
        """
        Evaluate answer using Groq AI
        
        Args:
            question: The interview question
            answer: Candidate's answer
            question_type: Type of question
            role: Target role
            level: Experience level
            
        Returns:
            Evaluation with score and feedback
        """
        # Skip evaluation for skipped answers
        if answer.lower().strip() in ['skipped', 'skip', '']:
            return {
                'score': 0,
                'feedback': 'Question was skipped.',
                'content_score': 0,
                'communication_score': 0,
                'technical_accuracy': 0
            }
        
        system_prompt = f"""You are evaluating a {role} candidate ({level} level). Score their answer briefly."""

        evaluation_prompt = f"""Question ({question_type}): {question}
Answer: {answer[:800]}

Return JSON:
{{"score":<0-10>,"content_score":<0-10>,"communication_score":<0-10>,"feedback":"<1-2 sentences>","improvement":"<1 sentence>"}}"""

        try:
            response = self.llm.generate(
                prompt=evaluation_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=200,
                json_mode=True
            )
            
            evaluation = self.llm.parse_json_response(response)
            
            # Ensure all required fields exist
            return {
                'score': evaluation.get('score', 5),
                'content_score': evaluation.get('content_score', 5),
                'communication_score': evaluation.get('communication_score', 5),
                'technical_accuracy': evaluation.get('content_score', 5),
                'feedback': evaluation.get('feedback', 'Good effort.'),
                'improvement': evaluation.get('improvement', 'Keep practicing.')
            }
            
        except Exception as e:
            print(f"Evaluation error: {e}")
            # Fallback evaluation
            return {
                'score': 5,
                'content_score': 5,
                'communication_score': 5,
                'technical_accuracy': 5,
                'feedback': 'Answer received. Keep practicing to improve.',
                'improvement': 'Provide more specific examples and details.'
            }
    
    def save_qa(
        self,
        session_id: int,
        question: str,
        answer: str,
        question_type: str,
        evaluation: Dict
    ) -> None:
        """Save question-answer pair to database"""
        db = get_db()
        
        db.execute(
            """INSERT INTO interview_qa 
               (session_id, question, answer, question_type, score, 
                content_score, communication_score, feedback)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                session_id,
                question,
                answer,
                question_type,
                evaluation.get('score', 0),
                evaluation.get('content_score', 0),
                evaluation.get('communication_score', 0),
                evaluation.get('feedback', '')
            ]
        )
        db.commit()
    
    def generate_final_evaluation(
        self,
        session_id: int,
        role: str,
        level: str
    ) -> Dict:
        """
        Generate comprehensive final evaluation
        
        Args:
            session_id: Interview session ID
            role: Target role
            level: Experience level
            
        Returns:
            Complete evaluation with scores and feedback
        """
        db = get_db()
        
        # Get all Q&A pairs
        qa_pairs = db.execute(
            """SELECT question, answer, question_type, score, content_score, 
                      communication_score, feedback
               FROM interview_qa
               WHERE session_id = ?
               ORDER BY id""",
            [session_id]
        ).fetchall()
        
        if not qa_pairs:
            return self._default_evaluation()
        
        # Calculate scores
        total_score = sum(qa['score'] for qa in qa_pairs)
        avg_score = total_score / len(qa_pairs)
        overall_score = round(avg_score * 10)  # Convert to 0-100 scale
        
        avg_content = sum(qa['content_score'] for qa in qa_pairs) / len(qa_pairs)
        avg_communication = sum(qa['communication_score'] for qa in qa_pairs) / len(qa_pairs)
        
        # Generate comprehensive feedback using AI
        qa_summary = "\n".join([
            f"Q: {qa['question']}\nA: {qa['answer'][:200]}...\nScore: {qa['score']}/10"
            for qa in qa_pairs
        ])
        
        system_prompt = f"""You are a career coach giving final interview feedback for a {role} ({level}) candidate."""

        feedback_prompt = f"""Role: {role} | Level: {level} | Score: {overall_score}/100
Q&A summary:
{qa_summary[:600]}

Return JSON:
{{"strengths":["s1","s2","s3"],"weaknesses":["w1","w2","w3"],"overall_assessment":"<2 sentences>","role_fit":<0-10>}}"""

        try:
            response = self.llm.generate(
                prompt=feedback_prompt,
                system_prompt=system_prompt,
                temperature=0.4,
                max_tokens=300,
                json_mode=True
            )
            
            ai_feedback = self.llm.parse_json_response(response)
            
        except Exception as e:
            print(f"Final evaluation error: {e}")
            ai_feedback = {
                'strengths': ['Completed the interview', 'Provided answers to all questions'],
                'weaknesses': ['Practice more technical questions'],
                'overall_assessment': 'Good effort. Keep practicing to improve.',
                'role_fit': 6
            }
        
        # Build final evaluation
        evaluation = {
            'overall_score': overall_score,
            'technical_accuracy': round(avg_content, 1),
            'communication_clarity': round(avg_communication, 1),
            'role_fit': ai_feedback.get('role_fit', 6),
            'questions_answered': len(qa_pairs),
            'strengths': ai_feedback.get('strengths', []),
            'weaknesses': ai_feedback.get('weaknesses', []),
            'areas_to_improve': ai_feedback.get('weaknesses', []),
            'overall_assessment': ai_feedback.get('overall_assessment', ''),
            'confidence': round(avg_communication, 1),
            'fluency': round(avg_communication, 1)
        }
        
        # Save evaluation to session
        db.execute(
            """UPDATE interview_sessions
               SET overall_score = ?,
                   status = 'completed',
                   ended_at = CURRENT_TIMESTAMP,
                   evaluation_data = ?
               WHERE id = ?""",
            [overall_score, json.dumps(evaluation), session_id]
        )
        db.commit()
        
        return evaluation
    
    def _default_evaluation(self) -> Dict:
        """Return default evaluation when no data available"""
        return {
            'overall_score': 0,
            'technical_accuracy': 0,
            'communication_clarity': 0,
            'role_fit': 0,
            'questions_answered': 0,
            'strengths': [],
            'weaknesses': ['Complete the interview to get feedback'],
            'areas_to_improve': ['Complete the interview to get feedback'],
            'overall_assessment': 'Interview was not completed.',
            'confidence': 0,
            'fluency': 0
        }
    
    def log_proctor_event(
        self,
        session_id: int,
        event_type: str,
        details: str = None
    ) -> None:
        """
        Log proctoring events
        
        Args:
            session_id: Interview session ID
            event_type: Type of event (tab_switch, face_not_detected, etc.)
            details: Additional details
        """
        db = get_db()
        
        db.execute(
            """INSERT INTO proctor_logs 
               (session_id, event_type, details, timestamp)
               VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
            [session_id, event_type, details or '']
        )
        db.commit()
    
    def get_session_status(self, session_id: int) -> Dict:
        """Get current session status"""
        db = get_db()
        
        session = db.execute(
            """SELECT * FROM interview_sessions WHERE id = ?""",
            [session_id]
        ).fetchone()
        
        if not session:
            return None
        
        qa_count = db.execute(
            """SELECT COUNT(*) as count FROM interview_qa WHERE session_id = ?""",
            [session_id]
        ).fetchone()['count']
        
        return {
            'session_id': session['id'],
            'role': session['role'],
            'level': session['level'],
            'status': session['status'],
            'questions_answered': qa_count,
            'total_questions': 5,
            'overall_score': session['overall_score']
        }
