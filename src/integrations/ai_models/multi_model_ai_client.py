"""
Project-S Multi-Model AI Client (Async Version)
------------------------------------------------
This module provides async multi-model AI integration for the Project-S system.
Capable of communicating with different AI providers and intelligently selecting
the appropriate model based on task type.
"""

import os
import logging
import asyncio
import yaml
import json
from typing import Dict, Any, List, Optional, Union, Tuple
import httpx
from pathlib import Path

logger = logging.getLogger(__name__)

class ModelNotAvailableError(Exception):
    """Exception when the requested model is not available."""
    pass

class AIClient:
    """
    Multi-model AI client capable of communicating with different providers.
    Supported providers: OpenAI, Anthropic, Ollama, OpenRouter
    """
    
    def __init__(self):
        """Initialize AI client and configure models."""
        # Load API keys from environment variables OR files
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "")
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        
        # Load OpenRouter API key (environment or file)
        openrouter_env = os.environ.get("OPENROUTER_API_KEY", "")
        if openrouter_env:
            self.openrouter_api_key = openrouter_env
        else:
            # Try to load from file
            try:
                from docs.openrouter_api_key import OPENROUTER_API_KEY
                self.openrouter_api_key = OPENROUTER_API_KEY or ""
            except ImportError:
                self.openrouter_api_key = ""
        
        # Load model configurations
        # Path: src/integrations/ai_models/multi_model_ai_client.py -> config/models.yaml (canonical)
        self.config_path = Path(__file__).parent.parent.parent.parent / "config" / "models.yaml"
        self.config = self._load_config()
        
        # Set timeout for API calls
        self.timeout = 60
        
        # Check API key availability and update config
        self._check_api_availability()
        
        logger.info(f"Model configurations loaded successfully: {len(self.config)} providers")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load model configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            return {}
    
    def _check_api_availability(self):
        """Check API key availability and disable unavailable providers."""
        # OpenAI availability
        if not self.openai_api_key:
            if self.config.get("openai", {}).get("enabled", False):
                logger.warning("OpenAI service enabled but no API key found")
                self.config["openai"]["enabled"] = False
        
        # Anthropic availability
        if not self.anthropic_api_key:
            if self.config.get("anthropic", {}).get("enabled", False):
                logger.warning("Anthropic service enabled but no API key found")
                self.config["anthropic"]["enabled"] = False
                
        # OpenRouter availability
        if not self.openrouter_api_key:
            if self.config.get("openrouter", {}).get("enabled", False):
                logger.warning("OpenRouter service enabled but no API key found")
                self.config["openrouter"]["enabled"] = False
        
        # Local Ollama availability check will be added later
        
    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available models grouped by provider."""
        available_models = []
        
        # Go through all providers and their models
        for provider, provider_config in self.config.items():
            if provider in ["openai", "anthropic", "ollama", "openrouter"] and provider_config.get("enabled", False):
                for model_id, model_config in provider_config.get("models", {}).items():
                    available_models.append({
                        "provider": provider,
                        "model_id": model_id,
                        "name": model_config.get("name", model_config.get("display_name", model_id)),
                        "display_name": model_config.get("display_name", model_config.get("name", model_id)),
                        "description": model_config.get("description", f"{provider} model: {model_id}"),
                        "strengths": model_config.get("strengths", model_config.get("capabilities", [])),
                        "capabilities": model_config.get("capabilities", model_config.get("strengths", [])),
                        "max_tokens": model_config.get("max_tokens", 4096)
                    })
        
        return available_models
    
    def get_recommended_model(self, task_type: str = "general") -> Optional[str]:
        """Get recommended model for a specific task type."""
        task_models = self.config.get("task_model_mapping", {}).get(task_type, [])
        
        for model_id in task_models:
            provider = self._get_provider_for_model(model_id)
            if provider and self.config.get(provider, {}).get("enabled", False):
                return model_id
        
        # Fallback to first available model
        available_models = self.list_available_models()
        if available_models:
            return available_models[0]["model_id"]
        
        return None
    
    def suggest_model_for_task(self, task_type: str) -> str:
        """
        Suggest the best model for a specific task type based on configuration.
        
        Args:
            task_type: The type of task (e.g., 'tervezés', 'kódolás', etc.)
            
        Returns:
            str: The recommended model ID
        """
        # Get task model mapping from config
        task_mapping = self.config.get("task_model_mapping", {})
        
        # Get models for this task type
        suggested_models = task_mapping.get(task_type, [])
        
        # Try each suggested model in order of preference
        for model_id in suggested_models:
            provider = self._get_provider_for_model(model_id)
            if provider and self.config.get(provider, {}).get("enabled", False):
                logger.info(f"Task '{task_type}' mapped to model: {model_id}")
                return model_id
        
        # Check if config is empty (no valid config file found)
        if not self.config:
            logger.warning(f"No valid configuration found, returning mock model for task '{task_type}'")
            return "mock-model"

        # Fallback: try 'defaults' block (e.g. defaults.model in models.yaml) — GAP_012 fix
        defaults_model = self.config.get("defaults", {}).get("model")
        if defaults_model:
            provider = self._get_provider_for_model(defaults_model)
            if provider and self.config.get(provider, {}).get("enabled", False):
                logger.info(f"Task '{task_type}' not in task_model_mapping, using defaults.model: {defaults_model} ({provider})")
                return defaults_model

        # Fallback: try 'defaults' block (e.g. defaults.model in models.yaml) — GAP_012 fix
        defaults_model = self.config.get("defaults", {}).get("model")
        if defaults_model:
            provider = self._get_provider_for_model(defaults_model)
            if provider and self.config.get(provider, {}).get("enabled", False):
                logger.info(f"Task '{task_type}' not in task_model_mapping, using defaults.model: {defaults_model} ({provider})")
                return defaults_model

        # Fallback to default model from config
        default_model = self.config.get("default_model", "deepseek-v3")
        provider = self._get_provider_for_model(default_model)
        if provider and self.config.get(provider, {}).get("enabled", False):
            logger.info(f"Using default model for task '{task_type}': {default_model}")
            return default_model
        
        # Last resort: use first available model
        available_models = self.list_available_models()
        if available_models:
            fallback_model = available_models[0]["model_id"]
            logger.warning(f"No suitable model found for task '{task_type}', using fallback: {fallback_model}")
            return fallback_model
        
        # If no models are available, return mock model instead of failing
        logger.error(f"No models available for task '{task_type}', returning mock model")
        return "mock-model"
    
    def _get_provider_for_model(self, model_id: str) -> Optional[str]:
        """Get the provider for a specific model."""
        # Check if it's an OpenRouter model (contains slash)
        if "/" in model_id:
            return "openrouter"
        
        # Check in config for explicit mappings
        for provider, provider_config in self.config.items():
            if provider in ["openai", "anthropic", "ollama", "openrouter"]:
                if model_id in provider_config.get("models", {}):
                    return provider
        
        # Default fallback for unknown models
        return "openrouter"
    
    def _get_model_api_id(self, model_id: str) -> str:
        """Get the actual API model ID to use for API calls."""
        # If it's already a full model ID (contains slash), use it as is
        if "/" in model_id:
            return model_id
            
        provider = self._get_provider_for_model(model_id)
        if provider and provider in self.config:
            model_config = self.config[provider].get("models", {}).get(model_id, {})
            # Return the model_id field from config if it exists, otherwise use the key
            return model_config.get("model_id", model_id)
        return model_id
    
    async def generate_response(
        self, 
        prompt: str, 
        model: Optional[str] = None, 
        provider: Optional[str] = None,
        system_message: Optional[str] = None,
        task_type: str = "general",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Optional[str]:
        """
        Generate response using the specified or recommended model.
        
        Args:
            prompt: The user prompt
            model: Optional specific model to use
            provider: Optional specific provider to use
            system_message: Optional system message
            task_type: Optional task type for model selection
            temperature: Optional temperature setting for response variability
            max_tokens: Optional maximum tokens for response
            
        Returns:
            Optional[str]: Response content or None if failed
        """
        
        # Model selection logic
        if not model:
            model = self.get_recommended_model(task_type)
            if not model:
                logger.error("No available models found")
                return None
        
        # Return mock response for offline/testing mode
        if model == "mock-model":
            return f"Mock AI response for task: {task_type}\nPrompt analyzed: {prompt[:50]}..."
        
        selected_model = model
        selected_provider = provider or self._get_provider_for_model(model)
        
        if not selected_provider:
            logger.error(f"Provider not found for model: {model}")
            return None
        
        # Check if provider is enabled
        if not self.config.get(selected_provider, {}).get("enabled", False):
            logger.error(f"Provider {selected_provider} is not enabled")
            return None
        
        try:
            # Route to appropriate provider
            if selected_provider == "openai":
                return await self._call_openai(selected_model, prompt, system_message, temperature, max_tokens)
            elif selected_provider == "anthropic":
                return await self._call_anthropic(selected_model, prompt, system_message, temperature, max_tokens)
            elif selected_provider == "openrouter":
                return await self._call_openrouter(selected_model, prompt, system_message, temperature, max_tokens)
            elif selected_provider == "ollama":
                return await self._call_ollama(selected_model, prompt, system_message, temperature, max_tokens)
            else:
                logger.error(f"Unsupported provider: {selected_provider}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating response with {selected_provider}/{selected_model}: {e}")
            return None
    
    async def _call_openai(self, model: str, prompt: str, system_message: Optional[str] = None,
                          temperature: float = 0.7, max_tokens: Optional[int] = None) -> Optional[str]:
        """Call OpenAI API using modern SDK."""
        try:
            try:
                import openai
            except ImportError:
                logger.error("OpenAI package not available")
                return f"Mock OpenAI response for {model}: {prompt[:50]}..."
            
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=model,                messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=self.timeout
                )
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None
    
    async def _call_openrouter(self, model: str, prompt: str, system_message: Optional[str] = None,
                              temperature: float = 0.7, max_tokens: Optional[int] = None) -> Optional[str]:
        """Call OpenRouter API using OpenAI SDK approach."""
        try:
            try:
                import openai
            except ImportError:
                logger.error("OpenAI package not available for OpenRouter calls")
                return f"Mock OpenRouter response for {model}: {prompt[:50]}..."
            
            # Use OpenAI SDK with OpenRouter endpoint
            client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.openrouter_api_key,
                default_headers={
                    "HTTP-Referer": "https://project-s-agent.local",
                    "X-Title": "Project-S Multi-AI System"
                }
            )
            
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            # Get the actual model ID from config
            model_id = self._get_model_api_id(model)
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=model_id,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens or 4096,
                    timeout=self.timeout
                )
            )
            
            # Add proper null checking for the response
            if response is None:
                logger.error("OpenRouter API returned None response")
                return None
                
            if not hasattr(response, 'choices') or response.choices is None:
                logger.error("OpenRouter API response has no choices")
                return None
                
            if len(response.choices) == 0:
                logger.error("OpenRouter API response has empty choices")
                return None
                
            choice = response.choices[0]
            if choice is None:
                logger.error("OpenRouter API first choice is None")
                return None
                
            if not hasattr(choice, 'message') or choice.message is None:
                logger.error("OpenRouter API choice has no message")
                return None
                
            if not hasattr(choice.message, 'content'):
                logger.error("OpenRouter API message has no content")
                return None
                
            content = choice.message.content
            if content is None:
                logger.error("OpenRouter API message content is None")
                return ""
                
            return content
            
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            return None
    
    async def _call_anthropic(self, model: str, prompt: str, system_message: Optional[str] = None,
                             temperature: float = 0.7, max_tokens: Optional[int] = None) -> Optional[str]:
        """Call Anthropic API."""
        try:
            try:
                import httpx
            except ImportError:
                logger.error("httpx package not available for Anthropic calls")
                return f"Mock Anthropic response for {model}: {prompt[:50]}..."
            
            # Using httpx for async HTTP calls since anthropic client may not be available
            async with httpx.AsyncClient() as client:
                headers = {
                    "anthropic-version": "2023-06-01",
                    "x-api-key": self.anthropic_api_key,
                    "content-type": "application/json"
                }
                
                messages = []
                if system_message:
                    messages.append({"role": "system", "content": system_message})
                messages.append({"role": "user", "content": prompt})
                
                data = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens or 4096,
                    "temperature": temperature
                }
                
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("content", [{}])[0].get("text", "")
                else:
                    logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
                    return None
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return None
    
    async def _call_ollama(self, model: str, prompt: str, system_message: Optional[str] = None,
                          temperature: float = 0.7, max_tokens: Optional[int] = None) -> Optional[str]:
        """Call Ollama API."""
        try:
            try:
                import httpx
            except ImportError:
                logger.error("httpx package not available for Ollama calls")
                return f"Mock Ollama response for {model}: {prompt[:50]}..."
            
            async with httpx.AsyncClient() as client:
                url = "http://localhost:11434/api/generate"
                
                full_prompt = prompt
                if system_message:
                    full_prompt = f"{system_message}\n\n{prompt}"
                
                data = {
                    "model": model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens or 4096
                    }
                }
                
                response = await client.post(url, json=data, timeout=self.timeout)
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
                else:
                    logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                    return None
            
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return None

# Initialize the global multi_model_ai_client instance
multi_model_ai_client = AIClient()