"""
Logging configuration for RAG system
Provides structured logging with rotation and different handlers
Supports JSON format for Azure Monitor and text format for local development
"""
import logging
import sys
import json
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
from datetime import datetime
from contextvars import ContextVar

# Context variable for correlation ID (thread-safe)
_correlation_id: ContextVar[str] = ContextVar('correlation_id', default='')


def set_correlation_id(correlation_id: str):
    """Set the correlation ID for the current request context"""
    _correlation_id.set(correlation_id)


def get_correlation_id() -> str:
    """Get the correlation ID for the current request context"""
    return _correlation_id.get()


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging (Azure Monitor compatible)"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation ID if available
        correlation_id = get_correlation_id()
        if correlation_id:
            log_data["correlation_id"] = correlation_id
        
        # Add extra fields from record
        if hasattr(record, 'correlation_id'):
            log_data["correlation_id"] = record.correlation_id
        if hasattr(record, 'method'):
            log_data["method"] = record.method
        if hasattr(record, 'path'):
            log_data["path"] = record.path
        if hasattr(record, 'status_code'):
            log_data["status_code"] = record.status_code
        if hasattr(record, 'duration_ms'):
            log_data["duration_ms"] = record.duration_ms
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class RAGLogger:
    """Centralized logging manager"""
    
    _loggers = {}
    _configured = False
    
    @classmethod
    def configure(
        cls,
        log_level: str = "INFO",
        log_dir: Optional[Path] = None,
        log_format: str = "text"  # 'text' or 'json'
    ):
        """Configure root logger with console and file handlers"""
        if cls._configured:
            return
        
        # Create log directory if specified
        if log_dir:
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # Choose formatter based on format setting
        if log_format.lower() == "json":
            console_formatter = JSONFormatter()
            file_formatter = JSONFormatter()
        else:
            # Text format for local development
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler with rotation if log_dir specified
        if log_dir:
            file_handler = RotatingFileHandler(
                log_dir / "rag_system.log",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        
        # Suppress noisy third-party loggers
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("azure").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        
        cls._configured = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get or create a logger for a module"""
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
        return cls._loggers[name]


def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger"""
    return RAGLogger.get_logger(name)
