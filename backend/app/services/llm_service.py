"""
LLM Service - Core AI Integration
Supports: OpenAI GPT-4, Groq Llama, Anthropic Claude
"""

import os
import json
from groq import Groq
import openai
from typing import Dict, List, Optional

class LLMService:
    def __init__(self):
        self.groq_key = os.getenv('GROQ_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        # Initialize clients
        if self.groq_key:
            self.groq_client = Groq(api_key=self.groq_key)
        if self.openai_key:
            openai.api_key = self.openai_key
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: str = None,
        model: str = "llama-3.1-8b-instant",
        temperature: float = 0.7,
        max_tokens: int = 600,
        json_mode: bool = False
    ) -> str:
        """
        Generate response using LLM
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            model: Model to use (groq/openai/claude)
            temperature: Creativity (0-1)
            max_tokens: Max response length
            json_mode: Force JSON output
        
        Returns:
            Generated text response
        """
        try:
            # Use Groq (free and fast)
            if self.groq_key and model.startswith("llama"):
                return self._groq_generate(
                    prompt, system_prompt, model, temperature, max_tokens, json_mode
                )
            
            # Use OpenAI
            elif self.openai_key and model.startswith("gpt"):
                return self._openai_generate(
                    prompt, system_prompt, model, temperature, max_tokens, json_mode
                )
            
            else:
                raise Exception("No LLM API key configured")
                
        except Exception as e:
            print(f"LLM Error: {e}")
            raise
    
    def _groq_generate(
        self, 
        prompt: str, 
        system_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool
    ) -> str:
        """Generate using Groq (Llama models)"""
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        response = self.groq_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"} if json_mode else {"type": "text"}
        )
        
        return response.choices[0].message.content
    
    def _openai_generate(
        self,
        prompt: str,
        system_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool
    ) -> str:
        """Generate using OpenAI"""
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"} if json_mode else None
        )
        
        return response.choices[0].message.content
    
    def generate_with_history(
        self,
        messages: List[Dict],
        model: str = "llama-3.1-8b-instant",
        temperature: float = 0.7,
        max_tokens: int = 400
    ) -> str:
        """
        Generate with conversation history (for chatbot/interview)
        
        Args:
            messages: List of {"role": "user/assistant", "content": "..."}
            model: Model to use
            temperature: Creativity
            max_tokens: Max response length
        
        Returns:
            Generated response
        """
        try:
            if self.groq_key and model.startswith("llama"):
                response = self.groq_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            
            elif self.openai_key and model.startswith("gpt"):
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
                
        except Exception as e:
            print(f"LLM History Error: {e}")
            raise
    
    def parse_json_response(self, response: str):
        """
        Parse JSON from LLM response
        Handles cases where LLM adds extra text
        Returns Dict or List depending on the JSON structure
        """
        try:
            # Try direct parse
            return json.loads(response)
        except:
            # Extract JSON from markdown code blocks
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
                return json.loads(json_str)
            
            # Try to find array first
            if response.strip().startswith("["):
                start = response.find("[")
                end = response.rfind("]") + 1
                if start != -1 and end != 0:
                    json_str = response[start:end]
                    return json.loads(json_str)
            
            # Extract JSON object from text
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != 0:
                json_str = response[start:end]
                return json.loads(json_str)
            
            raise Exception("Could not parse JSON from response")
