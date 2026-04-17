"""
LLM Service v2 - Production-Ready AI Integration
Features: Retry logic, timeout handling, fallback responses, comprehensive error handling
Supports: OpenAI GPT-4, Groq Llama, Anthropic Claude
"""

import os
import json
import time
from groq import Groq
import openai
from typing import Dict, List, Optional
import logging

from app.exceptions import LLMError, LLMTimeoutError, LLMRateLimitError

logger = logging.getLogger(__name__)


class LLMServiceV2:
    """Production-ready LLM service with reliability features"""
    
    # Configuration
    MAX_RETRIES = 2
    RETRY_DELAY = 0.5  # seconds
    TIMEOUT = 20  # seconds
    
    def __init__(self):
        self.groq_key = os.getenv('GROQ_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        # Initialize clients
        if self.groq_key:
            self.groq_client = Groq(api_key=self.groq_key)
        if self.openai_key:
            openai.api_key = self.openai_key
        
        logger.info("LLM Service V2 initialized")
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: str = None,
        model: str = "llama-3.1-8b-instant",
        temperature: float = 0.7,
        max_tokens: int = 800,
        json_mode: bool = False,
        retries: int = None,
        timeout: int = None
    ) -> str:
        """
        Generate response using LLM with retry logic and error handling
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            model: Model to use (groq/openai/claude)
            temperature: Creativity (0-1)
            max_tokens: Max response length
            json_mode: Force JSON output
            retries: Number of retry attempts (default: MAX_RETRIES)
            timeout: Request timeout in seconds (default: TIMEOUT)
        
        Returns:
            Generated text response
        
        Raises:
            LLMError: When LLM request fails after retries
            LLMTimeoutError: When request times out
            LLMRateLimitError: When rate limit is exceeded
        """
        retries = retries if retries is not None else self.MAX_RETRIES
        timeout = timeout if timeout is not None else self.TIMEOUT
        
        last_error = None
        
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"LLM request attempt {attempt}/{retries} - Model: {model}")
                
                # Route to appropriate provider
                if self.groq_key and model.startswith("llama"):
                    result = self._groq_generate(
                        prompt, system_prompt, model, temperature, max_tokens, json_mode, timeout
                    )
                elif self.openai_key and model.startswith("gpt"):
                    result = self._openai_generate(
                        prompt, system_prompt, model, temperature, max_tokens, json_mode, timeout
                    )
                else:
                    raise LLMError("No LLM API key configured or invalid model")
                
                logger.info(f"LLM request successful on attempt {attempt}")
                return result
                
            except LLMRateLimitError as e:
                last_error = e
                if attempt < retries:
                    delay = self.RETRY_DELAY * (2 ** (attempt - 1))  # Exponential backoff
                    logger.warning(f"Rate limit hit, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                raise
                
            except LLMTimeoutError as e:
                last_error = e
                if attempt < retries:
                    logger.warning(f"Request timeout, retrying (attempt {attempt}/{retries})...")
                    time.sleep(self.RETRY_DELAY)
                    continue
                raise
                
            except Exception as e:
                last_error = e
                logger.error(f"LLM error on attempt {attempt}: {str(e)}")
                
                if attempt < retries:
                    delay = self.RETRY_DELAY * attempt
                    logger.warning(f"Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                
                # Final attempt failed
                raise LLMError(f"LLM request failed after {retries} attempts: {str(e)}")
        
        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise LLMError("LLM request failed")
    
    def _groq_generate(
        self, 
        prompt: str, 
        system_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool,
        timeout: int
    ) -> str:
        """Generate using Groq (Llama models) with error handling"""
        try:
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
                response_format={"type": "json_object"} if json_mode else {"type": "text"},
                timeout=timeout
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if 'rate limit' in error_msg or '429' in error_msg:
                raise LLMRateLimitError("Groq rate limit exceeded")
            elif 'timeout' in error_msg:
                raise LLMTimeoutError("Groq request timed out")
            else:
                raise LLMError(f"Groq error: {str(e)}")
    
    def _openai_generate(
        self,
        prompt: str,
        system_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool,
        timeout: int
    ) -> str:
        """Generate using OpenAI with error handling"""
        try:
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
                response_format={"type": "json_object"} if json_mode else None,
                timeout=timeout
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if 'rate limit' in error_msg or '429' in error_msg:
                raise LLMRateLimitError("OpenAI rate limit exceeded")
            elif 'timeout' in error_msg:
                raise LLMTimeoutError("OpenAI request timed out")
            else:
                raise LLMError(f"OpenAI error: {str(e)}")
    
    def generate_with_history(
        self,
        messages: List[Dict],
        model: str = "llama-3.1-8b-instant",
        temperature: float = 0.7,
        max_tokens: int = 500,
        retries: int = None,
        timeout: int = None
    ) -> str:
        """
        Generate with conversation history (for chatbot/interview) with retry logic
        
        Args:
            messages: List of {"role": "user/assistant", "content": "..."}
            model: Model to use
            temperature: Creativity
            max_tokens: Max response length
            retries: Number of retry attempts
            timeout: Request timeout
        
        Returns:
            Generated response
        
        Raises:
            LLMError: When LLM request fails
        """
        retries = retries if retries is not None else self.MAX_RETRIES
        timeout = timeout if timeout is not None else self.TIMEOUT
        
        last_error = None
        
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"LLM history request attempt {attempt}/{retries}")
                
                if self.groq_key and model.startswith("llama"):
                    response = self.groq_client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        timeout=timeout
                    )
                    return response.choices[0].message.content
                
                elif self.openai_key and model.startswith("gpt"):
                    response = openai.ChatCompletion.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        timeout=timeout
                    )
                    return response.choices[0].message.content
                
                else:
                    raise LLMError("No LLM API key configured")
                    
            except Exception as e:
                last_error = e
                logger.error(f"LLM history error on attempt {attempt}: {str(e)}")
                
                if attempt < retries:
                    delay = self.RETRY_DELAY * attempt
                    logger.warning(f"Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                
                raise LLMError(f"LLM history request failed: {str(e)}")
        
        if last_error:
            raise last_error
        raise LLMError("LLM history request failed")
    
    def parse_json_response(self, response: str, fallback: dict = None):
        """
        Parse JSON from LLM response with fallback
        Handles cases where LLM adds extra text
        
        Args:
            response: LLM response string
            fallback: Fallback dict to return if parsing fails
        
        Returns:
            Dict or List depending on the JSON structure, or fallback
        """
        try:
            # Try direct parse
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        try:
            # Extract JSON from markdown code blocks
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass
        
        try:
            # Try to find array first
            if response.strip().startswith("["):
                start = response.find("[")
                end = response.rfind("]") + 1
                if start != -1 and end != 0:
                    json_str = response[start:end]
                    return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass
        
        try:
            # Extract JSON object from text
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != 0:
                json_str = response[start:end]
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # All parsing attempts failed
        logger.error(f"Failed to parse JSON from LLM response: {response[:200]}...")
        
        if fallback is not None:
            logger.warning("Using fallback response")
            return fallback
        
        raise LLMError("Could not parse JSON from LLM response")
    
    def generate_with_fallback(
        self,
        prompt: str,
        fallback_response: str,
        **kwargs
    ) -> str:
        """
        Generate with graceful fallback on failure
        
        Args:
            prompt: User prompt
            fallback_response: Response to return if LLM fails
            **kwargs: Additional arguments for generate()
        
        Returns:
            LLM response or fallback
        """
        try:
            return self.generate(prompt, **kwargs)
        except Exception as e:
            logger.error(f"LLM failed, using fallback: {str(e)}")
            return fallback_response
