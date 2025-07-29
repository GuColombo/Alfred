from typing import Dict, Optional, List
import openai
import anthropic
from loguru import logger

from config.settings import ConfigManager

class LLMRouter:
    """Routes tasks to appropriate language models."""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.api_keys = config.get_api_keys()
        
        # Initialize clients
        self.clients = {}
        self._init_clients()
        
        # Model capabilities and preferences
        self.model_preferences = config.get("llm.model_preferences", {})
        self.default_model = config.get("llm.default_model", "auto")
        
        logger.info("LLM router initialized")
    
    def _init_clients(self):
        """Initialize LLM API clients."""
        try:
            if self.api_keys.get("openai"):
                self.clients["openai"] = openai.OpenAI(api_key=self.api_keys["openai"])
                logger.info("OpenAI client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        try:
            if self.api_keys.get("claude"):
                self.clients["claude"] = anthropic.Anthropic(api_key=self.api_keys["claude"])
                logger.info("Claude client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Claude client: {e}")
        
        # Note: Google Gemini client would be initialized here
        # self.clients["gemini"] = ... when available
    
    def select_model(self, requested_model: str, prompt: str) -> str:
        """Select the best model for the given task."""
        if requested_model != "auto":
            # Use explicitly requested model if available
            if self._is_model_available(requested_model):
                return requested_model
            else:
                logger.warning(f"Requested model {requested_model} not available, falling back to auto selection")
        
        # Auto-selection based on task characteristics
        task_type = self._classify_task(prompt)
        preferred_model = self.model_preferences.get(task_type, "claude")
        
        if self._is_model_available(preferred_model):
            return preferred_model
        
        # Fallback to first available model
        available_models = list(self.clients.keys())
        if available_models:
            fallback = available_models[0]
            logger.info(f"Using fallback model: {fallback}")
            return fallback
        
        raise Exception("No LLM models available - check API key configuration")
    
    def _classify_task(self, prompt: str) -> str:
        """Classify task type based on prompt content."""
        prompt_lower = prompt.lower()
        
        # Coding/technical tasks
        if any(keyword in prompt_lower for keyword in [
            "code", "program", "function", "debug", "api", "sql", "python", "javascript"
        ]):
            return "coding"
        
        # Reasoning/analysis tasks
        if any(keyword in prompt_lower for keyword in [
            "analyze", "reason", "logic", "problem", "solve", "strategy", "plan"
        ]):
            return "reasoning"
        
        # Creative tasks
        if any(keyword in prompt_lower for keyword in [
            "write", "create", "story", "poem", "creative", "brainstorm", "imagine"
        ]):
            return "creative"
        
        # Default to reasoning
        return "reasoning"
    
    def _is_model_available(self, model: str) -> bool:
        """Check if a model is available."""
        model_map = {
            "claude": "claude",
            "gpt4": "openai", 
            "openai": "openai",
            "gemini": "gemini"
        }
        
        provider = model_map.get(model)
        return provider in self.clients
    
    def execute(self, model: str, prompt: str) -> str:
        """Execute prompt using selected model."""
        try:
            if model == "claude":
                return self._execute_claude(prompt)
            elif model in ["gpt4", "openai"]:
                return self._execute_openai(prompt)
            elif model == "gemini":
                return self._execute_gemini(prompt)
            else:
                raise ValueError(f"Unsupported model: {model}")
        
        except Exception as e:
            logger.error(f"Model execution failed for {model}: {e}")
            # Try fallback model
            available_models = [m for m in self.clients.keys() if m != model]
            if available_models:
                fallback_model = available_models[0]
                logger.info(f"Trying fallback model: {fallback_model}")
                return self.execute(fallback_model, prompt)
            raise
    
    def _execute_claude(self, prompt: str) -> str:
        """Execute prompt using Claude."""
        client = self.clients["claude"]
        
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=self.config.get("llm.max_tokens", 4000),
            temperature=self.config.get("llm.temperature", 0.1),
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    def _execute_openai(self, prompt: str) -> str:
        """Execute prompt using OpenAI."""
        client = self.clients["openai"]
        
        response = client.chat.completions.create(
            model="gpt-4",
            max_tokens=self.config.get("llm.max_tokens", 4000),
            temperature=self.config.get("llm.temperature", 0.1),
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.choices[0].message.content
    
    def _execute_gemini(self, prompt: str) -> str:
        """Execute prompt using Gemini."""
        # Placeholder for Gemini implementation
        # Would integrate with Google's Gemini API when available
        raise NotImplementedError("Gemini integration not yet implemented")
    
    def get_status(self) -> str:
        """Get router status."""
        available_models = list(self.clients.keys())
        return f"Available models: {', '.join(available_models) if available_models else 'None'}"
    
    def get_model_info(self) -> Dict[str, Dict[str, any]]:
        """Get information about available models."""
        info = {}
        for model in self.clients.keys():
            info[model] = {
                "available": True,
                "preferred_for": [k for k, v in self.model_preferences.items() if v == model]
            }
        return info