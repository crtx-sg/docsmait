# backend/app/ai_service.py
"""
AI Service for Docsmait

This module handles AI/LLM integration for document assistance including:
- Ollama integration
- Error handling and timeouts
- Response formatting
- Usage tracking
"""
import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, Tuple, List
import httpx
from .ai_config import ai_config
from .config import config

logger = logging.getLogger(__name__)

class AIService:
    """AI Service for document assistance using Ollama"""
    
    def __init__(self):
        self.settings = ai_config.get_ai_settings()
        self.base_url = self.settings.get("ollama_base_url", config.OLLAMA_BASE_URL)
        self.default_model = self.settings.get("default_model", config.GENERAL_PURPOSE_LLM)
        self.timeout = self.settings.get("ai_timeout", config.AI_TIMEOUT)
        self.max_response_length = self.settings.get("max_response_length", config.MAX_RESPONSE_LENGTH)
        self.context_window = self.settings.get("ai_context_window", config.AI_CONTEXT_WINDOW)
    
    def refresh_settings(self):
        """Refresh AI settings from config"""
        self.settings = ai_config.get_ai_settings()
        self.base_url = self.settings.get("ollama_base_url", config.OLLAMA_BASE_URL)
        self.default_model = self.settings.get("default_model", config.GENERAL_PURPOSE_LLM)
        self.timeout = self.settings.get("ai_timeout", config.AI_TIMEOUT)
        self.max_response_length = self.settings.get("max_response_length", config.MAX_RESPONSE_LENGTH)
        self.context_window = self.settings.get("ai_context_window", config.AI_CONTEXT_WINDOW)
    
    async def check_ollama_health(self) -> bool:
        """Check if Ollama service is available"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    async def list_available_models(self) -> Tuple[bool, List[str], Optional[str]]:
        """Get list of available models from Ollama"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                
                if response.status_code == 200:
                    data = response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    return True, models, None
                else:
                    error_msg = f"Failed to fetch models: HTTP {response.status_code}"
                    logger.error(error_msg)
                    return False, [], error_msg
        except httpx.TimeoutException:
            error_msg = "Timeout while fetching available models"
            logger.error(error_msg)
            return False, [], error_msg
        except Exception as e:
            error_msg = f"Error fetching available models: {str(e)}"
            logger.error(error_msg)
            return False, [], error_msg
    
    def truncate_content(self, content: str) -> str:
        """Truncate document content to fit context window"""
        if len(content) <= self.context_window:
            return content
        
        # Take from the beginning and add indicator
        truncated = content[:self.context_window - 100]
        return truncated + "\n\n[Content truncated to fit context window...]"
    
    async def generate_document_assistance(
        self, 
        user_id: int,
        document_type: str, 
        document_content: str, 
        user_input: str,
        custom_prompt: Optional[str] = None,
        model: Optional[str] = None,
        debug_mode: bool = False
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Generate AI assistance for document editing
        
        Returns:
            Tuple[bool, str, Dict]: (success, response/error_message, metadata)
        """
        start_time = time.time()
        debug_log = {}
        
        try:
            # Refresh settings in case they were updated
            self.refresh_settings()
            
            if debug_mode:
                debug_log["1_settings"] = {
                    "base_url": self.base_url,
                    "default_model": self.default_model,
                    "timeout": self.timeout,
                    "max_response_length": self.max_response_length,
                    "context_window": self.context_window
                }
            
            # Check Ollama availability
            health_check_start = time.time()
            is_healthy = await self.check_ollama_health()
            health_check_time = time.time() - health_check_start
            
            if debug_mode:
                debug_log["2_health_check"] = {
                    "healthy": is_healthy,
                    "check_time_ms": round(health_check_time * 1000, 2)
                }
            
            if not is_healthy:
                return False, "AI service is currently unavailable. Please try again later.", {"debug_log": debug_log} if debug_mode else {}
            
            # Get or use custom prompt
            prompt_fetch_start = time.time()
            if custom_prompt:
                prompt_template = custom_prompt
                prompt_source = "custom"
            else:
                prompt_template = ai_config.get_document_prompt(document_type)
                prompt_source = "config"
                if not prompt_template:
                    prompt_template = "Help improve this document. Consider the following requirements: [configurable_item]"
                    prompt_source = "fallback"
            
            prompt_fetch_time = time.time() - prompt_fetch_start
            
            if debug_mode:
                debug_log["3_prompt_preparation"] = {
                    "document_type": document_type,
                    "prompt_source": prompt_source,
                    "original_prompt": prompt_template,
                    "user_input": user_input,
                    "fetch_time_ms": round(prompt_fetch_time * 1000, 2)
                }
            
            # Replace configurable item
            full_prompt = prompt_template.replace("[configurable_item]", user_input)
            
            # Truncate document content if needed
            content_processing_start = time.time()
            original_content_length = len(document_content)
            truncated_content = self.truncate_content(document_content)
            content_truncated = len(truncated_content) < original_content_length
            content_processing_time = time.time() - content_processing_start
            
            if debug_mode:
                debug_log["4_content_processing"] = {
                    "original_length": original_content_length,
                    "truncated_length": len(truncated_content),
                    "was_truncated": content_truncated,
                    "processing_time_ms": round(content_processing_time * 1000, 2)
                }
            
            # Prepare the complete prompt
            system_prompt = full_prompt
            user_prompt = f"Current document content:\n\n{truncated_content}\n\nPlease provide suggestions or improvements based on the requirements above."
            
            # Use specified model or default
            model_to_use = model or self.default_model
            
            if debug_mode:
                debug_log["5_final_prompts"] = {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt[:500] + "..." if len(user_prompt) > 500 else user_prompt,
                    "model_to_use": model_to_use
                }
            
            # Prepare request payload
            payload = {
                "model": model_to_use,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {
                    "num_predict": self.max_response_length,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
            
            if debug_mode:
                debug_log["6_api_request"] = {
                    "url": f"{self.base_url}/api/chat",
                    "payload_size_bytes": len(json.dumps(payload)),
                    "timeout": self.timeout,
                    "num_predict": self.max_response_length
                }
            
            # Make API call to Ollama
            api_call_start = time.time()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if debug_mode:
                    debug_log["7_api_call_timing"] = {"start_time": api_call_start}
                
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                
                api_call_time = time.time() - api_call_start
                processing_time = time.time() - start_time
                
                if debug_mode:
                    debug_log["8_api_response"] = {
                        "status_code": response.status_code,
                        "api_call_time_ms": round(api_call_time * 1000, 2),
                        "total_processing_time_ms": round(processing_time * 1000, 2),
                        "response_headers": dict(response.headers)
                    }
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data.get("message", {}).get("content", "")
                    
                    if debug_mode:
                        debug_log["9_response_data"] = {
                            "raw_response_keys": list(data.keys()),
                            "message_keys": list(data.get("message", {}).keys()) if data.get("message") else [],
                            "response_length": len(ai_response),
                            "response_preview": ai_response[:200] + "..." if len(ai_response) > 200 else ai_response
                        }
                    
                    # Validate response
                    if not ai_response.strip():
                        error_msg = "AI service returned an empty response. Please try again."
                        return False, error_msg, {"debug_log": debug_log} if debug_mode else {}
                    
                    # Truncate response if too long
                    response_truncated = False
                    if len(ai_response) > self.max_response_length:
                        ai_response = ai_response[:self.max_response_length] + "\n\n[Response truncated due to length limit]"
                        response_truncated = True
                    
                    if debug_mode:
                        debug_log["10_response_processing"] = {
                            "response_truncated": response_truncated,
                            "final_response_length": len(ai_response)
                        }
                    
                    # Log usage
                    ai_config.log_ai_usage(
                        user_id=user_id,
                        document_type=document_type,
                        prompt_used=full_prompt,
                        response_length=len(ai_response),
                        processing_time=processing_time
                    )
                    
                    metadata = {
                        "model_used": model_to_use,
                        "processing_time": processing_time,
                        "response_length": len(ai_response),
                        "content_truncated": len(document_content) > self.context_window,
                        "prompt_used": full_prompt if ai_config.get_ai_settings().get("show_prompt", True) else None
                    }
                    
                    if debug_mode:
                        metadata["debug_log"] = debug_log
                    
                    return True, ai_response, metadata
                    
                else:
                    error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                    error_msg = error_data.get("error", f"HTTP {response.status_code}")
                    
                    if debug_mode:
                        debug_log["11_api_error"] = {
                            "status_code": response.status_code,
                            "error_data": error_data,
                            "error_message": error_msg,
                            "response_text": response.text[:500] if hasattr(response, 'text') else "N/A"
                        }
                    
                    logger.error(f"Ollama API error: {error_msg}")
                    
                    if response.status_code == 404:
                        error_msg = f"Model '{model_to_use}' not found. Please check available models."
                    elif response.status_code == 429:
                        error_msg = "AI service is busy. Please try again in a moment."
                    else:
                        error_msg = f"AI service error: {error_msg}"
                    
                    return False, error_msg, {"debug_log": debug_log} if debug_mode else {}
        
        except httpx.TimeoutException:
            processing_time = time.time() - start_time
            error_msg = f"AI request timed out after {self.timeout} seconds. Please try again with a shorter document or different requirements."
            
            if debug_mode:
                debug_log["12_timeout_error"] = {
                    "timeout_seconds": self.timeout,
                    "processing_time_ms": round(processing_time * 1000, 2),
                    "error_type": "TimeoutException"
                }
            
            logger.error(f"AI timeout: {processing_time}s")
            return False, error_msg, {"debug_log": debug_log} if debug_mode else {}
            
        except httpx.ConnectError as e:
            error_msg = "Cannot connect to AI service. Please check if the service is running."
            
            if debug_mode:
                debug_log["13_connection_error"] = {
                    "error_type": "ConnectError",
                    "error_details": str(e),
                    "base_url": self.base_url
                }
            
            logger.error("Ollama connection error")
            return False, error_msg, {"debug_log": debug_log} if debug_mode else {}
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Unexpected error during AI processing: {str(e)}"
            
            if debug_mode:
                debug_log["14_unexpected_error"] = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "processing_time_ms": round(processing_time * 1000, 2)
                }
            
            logger.error(f"AI service error: {e}")
            return False, error_msg, {"debug_log": debug_log} if debug_mode else {}
    
    async def get_model_info(self, model_name: str) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Get information about a specific model"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/show",
                    json={"name": model_name}
                )
                
                if response.status_code == 200:
                    return True, response.json(), None
                else:
                    error_msg = f"Model info error: HTTP {response.status_code}"
                    return False, {}, error_msg
                    
        except Exception as e:
            error_msg = f"Error getting model info: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg
    
    def generate_response(self, prompt: str, max_tokens: int = None) -> Dict[str, Any]:
        """
        Simplified synchronous method for generating responses
        Used by training system and other simple use cases
        """
        try:
            # Use asyncio to run the async method
            import asyncio
            
            # Create a simple prompt without document context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Use a simplified version that doesn't require document context
                success, response, metadata = loop.run_until_complete(
                    self._simple_generate(prompt, max_tokens or self.max_response_length)
                )
                
                if success:
                    return {
                        "success": True,
                        "response": response,
                        "metadata": metadata
                    }
                else:
                    return {
                        "success": False,
                        "error": response,
                        "response": ""
                    }
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error in generate_response: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": ""
            }
    
    async def _simple_generate(self, prompt: str, max_tokens: int) -> Tuple[bool, str, Dict[str, Any]]:
        """Simple async generation without document context"""
        try:
            # Refresh settings
            self.refresh_settings()
            
            # Check Ollama availability
            is_healthy = await self.check_ollama_health()
            if not is_healthy:
                return False, "AI service is currently unavailable. Please try again later.", {}
            
            # Prepare request payload
            payload = {
                "model": self.default_model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
            
            # Make API call to Ollama
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data.get("message", {}).get("content", "")
                    
                    if not ai_response.strip():
                        return False, "AI service returned an empty response. Please try again.", {}
                    
                    # Truncate response if too long
                    if len(ai_response) > max_tokens:
                        ai_response = ai_response[:max_tokens] + "\n\n[Response truncated due to length limit]"
                    
                    return True, ai_response, {"model_used": self.default_model}
                    
                else:
                    error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                    error_msg = error_data.get("error", f"HTTP {response.status_code}")
                    return False, f"AI service error: {error_msg}", {}
        
        except httpx.TimeoutException:
            return False, f"AI request timed out after {self.timeout} seconds. Please try again.", {}
        except httpx.ConnectError:
            return False, "Cannot connect to AI service. Please check if the service is running.", {}
        except Exception as e:
            logger.error(f"Simple generate error: {e}")
            return False, f"Unexpected error during AI processing: {str(e)}", {}

# Create global AI service instance
ai_service = AIService()