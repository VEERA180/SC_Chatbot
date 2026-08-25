"""
LLM service for text generation
Handles chat completions with retry logic and structured prompting
"""
import requests
from typing import List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import LLMConfig
from core.exceptions import LLMError
from core.logging_config import get_logger

logger = get_logger(__name__)


class LLMService:
    """Manages LLM API interactions"""
    
    def __init__(self, config: LLMConfig, verify_ssl: bool = False):
        self.config = config
        self.verify_ssl = verify_ssl
        
        logger.info(f"LLMService initialized: endpoint={config.endpoint}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None
    ) -> str:
        """
        Generate chat completion
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (override config)
            max_tokens: Maximum tokens to generate (override config)
            top_p: Nucleus sampling parameter (override config)
            
        Returns:
            Generated text response
            
        Raises:
            LLMError: If generation fails
        """
        if not messages:
            raise LLMError("Messages cannot be empty")
        
        # Use config defaults if not specified
        max_tokens = max_tokens or self.config.max_tokens
        
        headers = {
            "Content-Type": "application/json",
            "api-key": self.config.api_key
        }
        
        # Build payload with only supported parameters for this model family
        # (messages, max_completion_tokens); temperature and top_p must use
        # defaults (not configurable) - the endpoint rejects them.
        payload = {
            "messages": messages,
            "max_completion_tokens": max_tokens
        }

        # The OpenAI-compatible "v1" endpoint requires the model name in the
        # payload since it's no longer baked into the URL path. Old Azure-native
        # deployment URLs leave LLM_MODEL unset, so this stays backward compatible.
        if self.config.model:
            payload["model"] = self.config.model
        
        try:
            logger.debug(
                f"Calling LLM: {len(messages)} messages, "
                f"max_completion_tokens={max_tokens}"
            )
            
            response = requests.post(
                self.config.endpoint,
                headers=headers,
                json=payload,
                verify=self.verify_ssl,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract content from response
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content")
                if content:
                    logger.debug(f"LLM response: {len(content)} chars")
                    return content.strip()
            
            raise LLMError("Invalid response format", details={"response": result})
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"LLM HTTP error: {e.response.status_code}"
            if e.response.text:
                error_msg += f" - {e.response.text[:200]}"
            logger.error(error_msg)
            raise LLMError(error_msg)
        
        except requests.exceptions.RequestException as e:
            error_msg = f"LLM request error: {str(e)}"
            logger.error(error_msg)
            raise LLMError(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected LLM error: {str(e)}"
            logger.error(error_msg)
            raise LLMError(error_msg)
    
    def generate_answer(
        self,
        system_prompt: str,
        user_query: str,
        context: Optional[str] = None
    ) -> str:
        """
        Generate answer with system prompt and optional context
        
        Args:
            system_prompt: System instructions
            user_query: User question
            context: Additional context to include
            
        Returns:
            Generated answer
        """
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add context if provided
        if context:
            messages.append({
                "role": "system",
                "content": f"Context:\n{context}"
            })
        
        messages.append({
            "role": "user",
            "content": user_query
        })
        
        return self.chat_completion(messages)
