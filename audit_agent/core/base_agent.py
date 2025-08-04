"""
Base Agent class for the multi-agent compliance system
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Any, Optional
import openai
import re
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..utils.exceptions import APIKeyError, LLMError
from ..utils.client_pool import OpenAIClientPool


class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, name: str, api_key: str = None, model: str = "gpt-4o-mini"):
        self.name = name
        self.model = model
        # Allow api_key to be passed in or fall back to environment variable
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise APIKeyError("API key must be provided or OPENAI_API_KEY environment variable must be set!")
        # Use client pool for better resource management
        self.client_pool = OpenAIClientPool()
        self.client = self.client_pool.get_client(self.api_key)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((openai.APIError, openai.APITimeoutError)),
        reraise=True
    )
    def call_llm(self, prompt: str, system_prompt: str) -> str:
        """Make LLM API call with error handling and retry logic"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            return response.choices[0].message.content.strip()
        except openai.APIError as e:
            raise LLMError(self.name, str(e))
        except Exception as e:
            raise LLMError(self.name, f"Unexpected error: {str(e)}")
    
    def extract_json(self, text: str) -> Any:
        """Extract JSON from LLM response"""
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            # Try to extract JSON from markdown
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError as inner_e:
                    print(f"[{self.name}] JSON parsing error in markdown block: {inner_e}")
                    print(f"[{self.name}] Problematic JSON (first 500 chars): {json_match.group(1)[:500]}")
                    raise
            # Try to find any JSON structure
            json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError as inner_e:
                    print(f"[{self.name}] JSON parsing error: {inner_e}")
                    print(f"[{self.name}] Problematic JSON (first 500 chars): {json_match.group(1)[:500]}")
                    raise
            print(f"[{self.name}] Could not find JSON in response. Response preview: {text[:500]}")
            raise ValueError(f"Could not extract JSON from response: {text[:200]}...")
    
    @abstractmethod
    async def process(self, **kwargs) -> Any:
        """Process method to be implemented by each agent"""
        pass
    
    async def cleanup(self) -> None:
        """Cleanup resources - can be overridden by subclasses"""
        # Just remove reference, client pool manages actual clients
        if hasattr(self, 'client'):
            self.client = None