"""
Custom exceptions for RAG system
Provides structured error handling across all components
"""

class RAGException(Exception):
    """Base exception for all RAG-related errors"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(RAGException):
    """Raised when configuration is invalid or missing"""
    pass


class AuthenticationError(RAGException):
    """Raised when authentication fails"""
    pass


class EmbeddingError(RAGException):
    """Raised when embedding generation fails"""
    pass


class SearchError(RAGException):
    """Raised when search operation fails"""
    pass


class LLMError(RAGException):
    """Raised when LLM API call fails"""
    pass


class MemoryError(RAGException):
    """Raised when memory operations fail"""
    pass


class ValidationError(RAGException):
    """Raised when input validation fails"""
    pass


class TimeoutError(RAGException):
    """Raised when operation times out"""
    pass
