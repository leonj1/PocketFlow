"""
AI Agent service class for LLM interactions using PydanticAI.
"""

import os
import asyncio
from typing import Optional, Dict, Any, Union
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic import BaseModel, Field
import logging

# Set up logging
logger = logging.getLogger(__name__)


class AiAgent:
    """Service class for LLM interactions using PydanticAI."""
    
    def __init__(self, 
                 api_token: Optional[str] = None,
                 provider: Optional[str] = None,
                 model: Optional[str] = None,
                 temperature: Optional[float] = None,
                 max_tokens: Optional[int] = None):
        """
        Initialize the AI Agent.
        
        Args:
            api_token: API token for the LLM provider
            provider: LLM provider (e.g., 'google', 'openai')
            model: Model name to use
            temperature: Temperature for generation (0.0-1.0)
            max_tokens: Maximum tokens to generate
        """
        # Load environment variables
        load_dotenv()
        
        # Use provided values or fall back to env vars
        self.api_token = api_token or os.getenv('GEMINI_API_KEY')
        self.provider = provider or os.getenv('LLM_PROVIDER', 'google')
        self.model = model or os.getenv('LLM_MODEL', 'gemini-2.0-flash-exp')
        self.temperature = temperature or float(os.getenv('LLM_TEMPERATURE', '0.7'))
        self.max_tokens = max_tokens or int(os.getenv('LLM_MAX_TOKENS', '2048'))
        
        # Check if AI is enabled
        self.enabled = os.getenv('DOC_GENERATION_MODE', 'ai_assisted') == 'ai_assisted'
        
        if self.enabled:
            # Validate configuration
            if not self.api_token:
                raise ValueError("API token required. Please set GEMINI_API_KEY in .env file")
            
            # Initialize PydanticAI agent
            self._init_agent()
        else:
            logger.info("AI Agent disabled - running in human_only mode")
            self.agent = None
    
    def _init_agent(self):
        """Initialize the PydanticAI agent based on provider."""
        try:
            if self.provider == 'google':
                # Create Gemini model with configuration
                llm_model = GeminiModel(
                    model_name=self.model,
                    api_key=self.api_token
                )
                
                # Create PydanticAI agent
                self.agent = Agent(
                    model=llm_model,
                    system_prompt="""You are an expert document creation and review assistant. 
                    You help create professional, well-structured documents based on context and requirements.
                    Always maintain a professional tone and ensure accuracy."""
                )
                
                logger.info(f"Initialized {self.provider} AI agent with model {self.model}")
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Failed to initialize AI agent: {e}")
            raise
    
    async def invoke_async(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Invoke the LLM asynchronously.
        
        Args:
            query: The prompt/query to send to the LLM
            context: Optional context dictionary
            
        Returns:
            Response from the LLM as a string
        """
        if not self.enabled or not self.agent:
            return "AI agent is disabled. Please provide manual input."
        
        try:
            # Add context to the query if provided
            if context:
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                full_query = f"Context:\n{context_str}\n\nQuery: {query}"
            else:
                full_query = query
            
            # Run the agent
            result = await self.agent.run(full_query)
            return result.data
            
        except Exception as e:
            logger.error(f"Error invoking AI agent: {e}")
            return f"AI Error: {str(e)}. Please provide manual input."
    
    def invoke(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Invoke the LLM synchronously.
        
        Args:
            query: The prompt/query to send to the LLM
            context: Optional context dictionary
            
        Returns:
            Response from the LLM as a string
        """
        # For sync usage, we'll use asyncio.run
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a task
                task = asyncio.create_task(self.invoke_async(query, context))
                return asyncio.run_until_complete(task)
            else:
                # Otherwise, use asyncio.run
                return asyncio.run(self.invoke_async(query, context))
        except RuntimeError:
            # Fallback for when no event loop exists
            return asyncio.run(self.invoke_async(query, context))
    
    def is_enabled(self) -> bool:
        """Check if the AI agent is enabled."""
        return self.enabled
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        return {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "enabled": self.enabled
        }


# Singleton instance for easy access
_default_agent: Optional[AiAgent] = None


def get_default_agent() -> AiAgent:
    """Get or create the default AI agent instance."""
    global _default_agent
    if _default_agent is None:
        _default_agent = AiAgent()
    return _default_agent


def reset_default_agent():
    """Reset the default agent (useful for testing)."""
    global _default_agent
    _default_agent = None