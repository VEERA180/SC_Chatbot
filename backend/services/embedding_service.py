"""
Embedding service
Handles text embedding generation with retry logic and error handling
"""
import requests
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from core.config import EmbeddingConfig
from core.exceptions import EmbeddingError
from core.logging_config import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Manages text embedding generation"""
    
    def __init__(self, config: EmbeddingConfig, verify_ssl: bool = False):
        self.config = config
        self.verify_ssl = verify_ssl
        self.base_url = config.endpoint.rstrip("/")
        
        logger.info(
            f"EmbeddingService initialized: {config.deployment} "
            f"({config.dimensions} dimensions)"
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException)
    )
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for text with automatic retry
        
        Args:
            text: Input text to embed
            
        Returns:
            List of float values representing the embedding vector
            
        Raises:
            EmbeddingError: If embedding generation fails after retries
        """
        if not text or not text.strip():
            raise EmbeddingError("Input text cannot be empty")
        
        # Truncate if too long (typical limit is ~8k tokens)
        text = text[:32000]  # Conservative character limit
        
        url = (
            f"{self.base_url}/openai/deployments/{self.config.deployment}/embeddings"
            f"?api-version={self.config.api_version}"
        )
        
        headers = {
            "Content-Type": "application/json",
            "api-key": self.config.api_key
        }
        
        payload = {
            "input": text,
            "dimensions": self.config.dimensions
        }
        
        try:
            logger.debug(f"Generating embedding for text ({len(text)} chars)")
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                verify=self.verify_ssl,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract embedding from response
            if "data" in result and len(result["data"]) > 0:
                embedding = result["data"][0].get("embedding")
                if embedding and len(embedding) == self.config.dimensions:
                    logger.debug(f"Embedding generated successfully ({len(embedding)} dims)")
                    return embedding
                else:
                    raise EmbeddingError(
                        f"Invalid embedding dimensions: expected {self.config.dimensions}, "
                        f"got {len(embedding) if embedding else 0}"
                    )
            else:
                raise EmbeddingError(
                    "Unexpected response format",
                    details={"response": result}
                )
                
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error during embedding: {e.response.status_code}"
            if e.response.text:
                error_msg += f" - {e.response.text[:200]}"
            logger.error(error_msg)
            raise EmbeddingError(error_msg, details={"status_code": e.response.status_code})
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed during embedding: {str(e)}"
            logger.error(error_msg)
            raise EmbeddingError(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error during embedding: {str(e)}"
            logger.error(error_msg)
            raise EmbeddingError(error_msg)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for i, text in enumerate(texts):
            try:
                embedding = self.embed_text(text)
                embeddings.append(embedding)
            except EmbeddingError as e:
                logger.warning(f"Failed to embed text {i+1}/{len(texts)}: {str(e)}")
                # Return zero vector as fallback
                embeddings.append([0.0] * self.config.dimensions)
        
        return embeddings
