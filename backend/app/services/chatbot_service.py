"""
AI Career Coach Chatbot - 24/7 career guidance
Uses: Conversation Memory, Context-Aware Responses
"""

import json
from typing import Dict, List, Optional
from .llm_service import LLMService

class ChatbotService:
    def __init__(self):
        self.llm = LLMService()
        self.conversation_sessions = {}  # In production, use Redis
    
    def get_system_prompt(self, user_context: Dict = None) -> str:
        """
        Build context-aware system prompt
        
        Args:
            user_context: {
                "skills": [...],
                "target_role": "...",
                "experience_level": "...",
                "recent_interviews": [...]
            }
        """
        
        base_prompt = """You are an expert AI Career Coach specializing in tech careers.

Your role:
- Provide career guidance and advice
- Help with interview preparation
- Suggest learning resources
- Review code and technical concepts
- Offer salary insights
- Give job search strategies

Your personality:
- Friendly, warm, and encouraging
- Professional but approachable
- Honest and constructive
- Patient and supportive
- Knowledgeable about tech industry

Communication style:
- Keep responses concise (2-3 sentences for greetings, 3-5 sentences for advice)
- Be conversational and natural
- Ask follow-up questions to understand user needs
- Use examples when helpful but keep them brief
- Avoid overly long explanations unless specifically requested

IMPORTANT Guidelines:
- For simple greetings like "hi" or "hello", respond warmly and briefly, then ask how you can help TODAY
- DO NOT mention the user's target role or profile information unless they specifically ask about it
- DO NOT make assumptions about what they want to discuss
- Let the user lead the conversation
- Only use context information when directly relevant to their question
- Give specific, actionable advice when asked
- Be direct and to the point
- Ask clarifying questions if needed
- Encourage continuous learning"""

        if user_context:
            context_info = f"""

Available User Context (use ONLY when relevant to their question):
- Skills: {', '.join([s['name'] for s in user_context.get('skills', [])][:5])}
- Target Role: {user_context.get('target_role', 'Not set')}
- Experience Level: {user_context.get('experience_level', 'Unknown')}

Remember: Only reference this information if the user's question is directly related to it."""
            
            base_prompt += context_info
        
        return base_prompt
    
    def chat(
        self,
        user_id: str,
        message: str,
        user_context: Dict = None
    ) -> Dict:
        """
        Process chat message and generate response
        
        Args:
            user_id: User identifier
            message: User's message
            user_context: User's profile context
        
        Returns:
            {
                "response": "AI response",
                "suggestions": ["follow-up question 1", "..."],
                "resources": [...]  # If applicable
            }
        """
        
        # Get or create conversation history
        if user_id not in self.conversation_sessions:
            self.conversation_sessions[user_id] = []
        
        history = self.conversation_sessions[user_id]
        
        # Build messages with system prompt
        messages = [
            {
                "role": "system",
                "content": self.get_system_prompt(user_context)
            }
        ]
        
        # Add conversation history (last 6 messages)
        messages.extend(history[-6:])
        
        # Add current message
        messages.append({
            "role": "user",
            "content": message
        })
        
        # Generate response
        response = self.llm.generate_with_history(
            messages=messages,
            temperature=0.7,
            max_tokens=200  # Limit response length
        )
        
        # Update history
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": response})
        
        # Keep only last 20 messages
        if len(history) > 20:
            history = history[-20:]
        
        self.conversation_sessions[user_id] = history
        
        # Generate follow-up suggestions
        suggestions = self._generate_suggestions(message, response, user_context)
        
        return {
            "response": response,
            "suggestions": suggestions
        }
    
    def _generate_suggestions(
        self,
        user_message: str,
        ai_response: str,
        user_context: Dict = None
    ) -> List[str]:
        """Generate follow-up question suggestions"""
        
        # Simple rule-based suggestions
        suggestions = []
        
        message_lower = user_message.lower()
        
        if "interview" in message_lower:
            suggestions = [
                "What are common mistakes to avoid?",
                "How should I prepare for system design?",
                "Can you give me practice questions?"
            ]
        elif "resume" in message_lower:
            suggestions = [
                "How can I improve my resume?",
                "What keywords should I include?",
                "Should I include all my projects?"
            ]
        elif "salary" in message_lower:
            suggestions = [
                "How do I negotiate salary?",
                "What's the market rate for my role?",
                "When should I discuss salary?"
            ]
        elif "learn" in message_lower or "skill" in message_lower:
            suggestions = [
                "What should I learn next?",
                "How long will it take?",
                "What are the best resources?"
            ]
        else:
            suggestions = [
                "Can you explain more?",
                "What resources do you recommend?",
                "How do I get started?"
            ]
        
        return suggestions[:3]
    
    def ask_about_topic(
        self,
        topic: str,
        question: str,
        user_context: Dict = None
    ) -> str:
        """
        Ask specific question about a topic
        
        Args:
            topic: Topic area (e.g., "React", "System Design")
            question: Specific question
            user_context: User context
        
        Returns:
            Detailed answer
        """
        
        system_prompt = f"""You are an expert in {topic}.
Provide clear, practical explanations with examples.
Tailor your answer to the user's level."""

        if user_context:
            level = user_context.get('experience_level', 'Intermediate')
            system_prompt += f"\n\nUser's experience level: {level}"
        
        response = self.llm.generate(
            prompt=question,
            system_prompt=system_prompt,
            temperature=0.6
        )
        
        return response
    
    def review_code(
        self,
        code: str,
        language: str,
        context: str = None
    ) -> Dict:
        """
        Review code and provide feedback
        
        Returns:
            {
                "overall_feedback": "...",
                "strengths": [...],
                "improvements": [...],
                "refactored_code": "...",
                "best_practices": [...]
            }
        """
        
        system_prompt = f"""You are an expert {language} developer and code reviewer.
Provide constructive, specific feedback on code quality."""

        prompt = f"""Review this {language} code:

```{language}
{code}
```

{f"Context: {context}" if context else ""}

Provide JSON feedback:
{{
  "overall_feedback": "Summary of code quality",
  "strengths": ["good point 1", "good point 2"],
  "improvements": [
    {{"issue": "what's wrong", "suggestion": "how to fix", "priority": "High/Medium/Low"}}
  ],
  "refactored_code": "Improved version of the code",
  "best_practices": ["practice 1", "practice 2"],
  "performance_notes": "Performance considerations",
  "security_notes": "Security considerations"
}}

Return ONLY valid JSON, no other text."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.4,
            json_mode=True,
            max_tokens=2000
        )
        
        return self.llm.parse_json_response(response)
    
    def get_career_advice(
        self,
        situation: str,
        user_context: Dict = None
    ) -> Dict:
        """
        Get career advice for specific situation
        
        Returns:
            {
                "advice": "...",
                "action_steps": [...],
                "resources": [...],
                "timeline": "..."
            }
        """
        
        system_prompt = """You are a senior career advisor for tech professionals.
Provide practical, actionable career advice."""

        context_str = ""
        if user_context:
            context_str = f"""
User Context:
- Skills: {json.dumps(user_context.get('skills', []))}
- Experience: {user_context.get('experience_level', 'Unknown')}
- Target Role: {user_context.get('target_role', 'Not set')}
"""

        prompt = f"""Provide career advice for this situation:

Situation: {situation}
{context_str}

Provide JSON response:
{{
  "advice": "Detailed career advice (2-3 paragraphs)",
  "action_steps": [
    {{"step": "What to do", "timeline": "When", "priority": "High/Medium/Low"}}
  ],
  "resources": ["resource 1", "resource 2"],
  "potential_challenges": ["challenge 1"],
  "success_indicators": ["how to know you're on track"],
  "timeline": "Expected timeline"
}}

Be specific and actionable.
Return ONLY valid JSON, no other text."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.6,
            json_mode=True
        )
        
        return self.llm.parse_json_response(response)
    
    def explain_concept(
        self,
        concept: str,
        detail_level: str = "intermediate"
    ) -> str:
        """
        Explain a technical concept
        
        Args:
            concept: Concept to explain
            detail_level: "beginner", "intermediate", "advanced"
        
        Returns:
            Clear explanation
        """
        
        system_prompt = f"""You are a technical educator.
Explain concepts clearly at {detail_level} level.
Use analogies and examples."""

        prompt = f"""Explain this concept: {concept}

Requirements:
- Explain at {detail_level} level
- Use simple language
- Include practical examples
- Add analogies if helpful
- Keep it concise but thorough

Provide a clear, structured explanation."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.6
        )
        
        return response
    
    def clear_conversation(self, user_id: str):
        """Clear conversation history for user"""
        if user_id in self.conversation_sessions:
            del self.conversation_sessions[user_id]
