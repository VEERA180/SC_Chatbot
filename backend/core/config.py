"""
Configuration management for RAG system
Handles environment variables, validation, and configuration models
"""
import os
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

load_dotenv()


class AzureConfig(BaseModel):
    """Azure authentication configuration"""
    client_id: str = Field(..., env="AZURE_CLIENT_ID")
    client_secret: str = Field(..., env="AZURE_CLIENT_SECRET")
    tenant_id: str = Field(..., env="AZURE_TENANT_ID")
    
    @field_validator("client_id", "client_secret", "tenant_id", mode="before")
    @classmethod
    def validate_not_empty(cls, v):
        if not v or not str(v).strip():
            raise ValueError("Field cannot be empty")
        return str(v).strip()


class SearchConfig(BaseModel):
    """Azure AI Search configuration"""
    endpoint: str = Field(..., env="AZURE_SEARCH_ENDPOINT")
    index_name: str = Field(..., env="AZURE_SEARCH_INDEX")
    api_key: str = Field(..., env="AZURE_SEARCH_API_KEY")
    api_version: str = Field(default="2023-11-01", env="AZURE_SEARCH_API_VERSION")
    
    # Search parameters
    top_k: int = Field(default=25, ge=1, le=100)
    vector_field: str = Field(default="content_vector")
    
    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, v):
        if not v.startswith("https://"):
            raise ValueError("Search endpoint must be HTTPS")
        return v.rstrip("/")


class EmbeddingConfig(BaseModel):
    """Embedding API configuration"""
    endpoint: str = Field(..., env="OPENAI_SDK_ENDPOINT")
    deployment: str = Field(..., env="EMBEDDING_DEPLOYMENT")
    api_key: str = Field(..., env="EMBEDDING_API_KEY")
    api_version: str = Field(default="2025-01-01-preview", env="EMBEDDING_API_VERSION")
    dimensions: int = Field(default=3072, env="EMBEDDING_DIMENSIONS")
    
    @field_validator("dimensions")
    @classmethod
    def validate_dimensions(cls, v):
        if v not in [1536, 3072]:
            raise ValueError("Dimensions must be 1536 or 3072")
        return v


class LLMConfig(BaseModel):
    """LLM API configuration"""
    endpoint: str = Field(..., env="LLM_NEW_ENDPOINT")
    api_key: str = Field(..., env="LLM_KEY")
    deployment: Optional[str] = Field(None, env="LLM_DEPLOYMENT")
    # Model name required by the OpenAI-compatible "v1" endpoint (not baked into the URL path).
    # Left as None for backward compatibility with the old Azure-native deployment URL style.
    model: Optional[str] = Field(None, env="LLM_MODEL")
    
    # Generation parameters
    # max_tokens: int = Field(default=1024, ge=100, le=4096)
    max_tokens: int = Field(default=5000, ge=1000, le=9000)
    temperature: float = Field(default=0.1, ge=0.0, le=0.6)
    # top_p: float = Field(default=0.80, ge=0.0, le=1.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)


class MemoryConfig(BaseModel):
    """Conversation memory configuration"""
    window_size: int = Field(default=5, ge=1, le=20)
    summary_frequency: int = Field(default=6, ge=3, le=20)
    summary_max_chars: int = Field(default=900, ge=200, le=2000)
    session_timeout_hours: int = Field(default=24, ge=1, le=168)


class AppConfig(BaseModel):
    """Main application configuration"""
    azure: AzureConfig
    search: SearchConfig
    embedding: EmbeddingConfig
    llm: LLMConfig
    memory: MemoryConfig
    
    # Application settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    enable_ssl_verify: bool = Field(default=False, env="ENABLE_SSL_VERIFY")
    request_timeout: int = Field(default=30, ge=5, le=300)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def load_config() -> AppConfig:
    """Load and validate application configuration"""
    try:
        config = AppConfig(
            azure=AzureConfig(
                client_id=os.getenv("AZURE_CLIENT_ID", ""),
                client_secret=os.getenv("AZURE_CLIENT_SECRET", ""),
                tenant_id=os.getenv("AZURE_TENANT_ID", "")
            ),
            search=SearchConfig(
                endpoint=os.getenv("AZURE_SEARCH_ENDPOINT", ""),
                index_name=os.getenv("AZURE_SEARCH_INDEX", ""),
                api_key=os.getenv("AZURE_SEARCH_API_KEY", "")
            ),
            embedding=EmbeddingConfig(
                endpoint=os.getenv("OPENAI_SDK_ENDPOINT", ""),
                deployment=os.getenv("EMBEDDING_DEPLOYMENT", ""),
                api_key=os.getenv("EMBEDDING_API_KEY", "")
            ),
            llm=LLMConfig(
                endpoint=os.getenv("LLM_NEW_ENDPOINT", ""),
                api_key=os.getenv("LLM_KEY", ""),
                model=os.getenv("LLM_MODEL") or None
            ),
            memory=MemoryConfig()
        )
        return config
    except Exception as e:
        raise RuntimeError(f"Configuration validation failed: {str(e)}")


# Global config instance
config = load_config()
