"""
OpenAI client connection pool for better resource management
"""

from typing import Dict, Optional
import openai
from threading import Lock


class OpenAIClientPool:
    """Singleton pool for OpenAI clients to reuse connections"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._clients = {}
                    cls._instance._client_lock = Lock()
        return cls._instance
    
    def get_client(self, api_key: str) -> openai.OpenAI:
        """Get or create a client for the given API key"""
        with self._client_lock:
            if api_key not in self._clients:
                self._clients[api_key] = openai.OpenAI(api_key=api_key)
            return self._clients[api_key]
    
    def cleanup(self) -> None:
        """Cleanup all clients"""
        with self._client_lock:
            self._clients.clear()
    
    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (useful for testing)"""
        with cls._lock:
            if cls._instance:
                cls._instance.cleanup()
            cls._instance = None