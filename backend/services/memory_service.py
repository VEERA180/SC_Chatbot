"""
Memory service for conversation management
Handles session memory, summaries, and conversation history
"""
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from threading import Lock
from collections import defaultdict


from langchain_core.messages import HumanMessage, AIMessage

from core.config import MemoryConfig
from core.exceptions import MemoryError
from core.logging_config import get_logger

logger = get_logger(__name__)


class ConversationTurn:
    """Represents a single conversation turn"""
    def __init__(self, question: str, answer: str, timestamp: Optional[datetime] = None):
        self.question = question
        self.answer = answer
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "answer": self.answer,
            "timestamp": self.timestamp.isoformat()
        }


class SessionMemory:
    """Memory for a single conversation session"""
    
    def __init__(self, session_id: str, config: MemoryConfig):
        self.session_id = session_id
        self.config = config
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        
        # In-memory windowed history (replaces LangChain memory)
        self.windowed_history: List[Tuple[str, str]] = []
        
        # Full transcript
        self.transcript: List[ConversationTurn] = []
        
        # Rolling summary
        self.summary: str = ""
        self.summary_cursor: int = 0
        
        # User profile
        self.profile: Dict[str, str] = {}
    
    def add_turn(self, question: str, answer: str):
        """Add a conversation turn"""
        self.last_accessed = datetime.now()
        
        # Add to windowed history (keep last k turns)
        self.windowed_history.append((question, answer))
        if len(self.windowed_history) > self.config.window_size:
            self.windowed_history.pop(0)
        
        # Add to transcript
        turn = ConversationTurn(question, answer)
        self.transcript.append(turn)
        
        logger.debug(f"Added turn to session {self.session_id}: {len(self.transcript)} turns total")
    
    def get_recent_turns(self, n: int = 5) -> List[Tuple[str, str]]:
        """Get last N question-answer pairs"""
        recent = self.transcript[-n:] if self.transcript else []
        return [(t.question, t.answer) for t in recent]
    
    def is_expired(self, timeout_hours: int) -> bool:
        """Check if session has expired"""
        expiry_time = self.last_accessed + timedelta(hours=timeout_hours)
        return datetime.now() > expiry_time
    
    def to_dict(self) -> dict:
        """Serialize session to dict"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "turn_count": len(self.transcript),
            "summary": self.summary,
            "profile": self.profile
        }

class MemoryService:
    """Manages conversation memory across multiple sessions"""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self._sessions: Dict[str, SessionMemory] = {}
        self._lock = Lock()
        
        logger.info(
            f"MemoryService initialized: window_size={config.window_size}, "
            f"timeout={config.session_timeout_hours}h"
        )
    
    def get_session(self, session_id: str) -> SessionMemory:
        """Get or create session memory"""
        with self._lock:
            if session_id not in self._sessions:
                logger.info(f"Creating new session: {session_id}")
                self._sessions[session_id] = SessionMemory(session_id, self.config)
            
            session = self._sessions[session_id]
            session.last_accessed = datetime.now()
            return session
    
    def add_conversation_turn(self, session_id: str, question: str, answer: str):
        """Add a conversation turn to session"""
        session = self.get_session(session_id)
        session.add_turn(question, answer)
    
    def get_conversation_history(self, session_id: str, n_turns: int = None) -> List[Tuple[str, str]]:
        """Get recent conversation history"""
        n_turns = n_turns or self.config.window_size
        session = self.get_session(session_id)
        return session.get_recent_turns(n_turns)
    
    def update_summary(self, session_id: str, summary: str):
        """Update rolling summary for session"""
        session = self.get_session(session_id)
        session.summary = summary[:self.config.summary_max_chars]
        session.summary_cursor = len(session.transcript)
        logger.debug(f"Updated summary for session {session_id}")
    
    def get_summary(self, session_id: str) -> str:
        """Get rolling summary for session"""
        session = self.get_session(session_id)
        return session.summary
    
    def should_update_summary(self, session_id: str) -> bool:
        """Check if summary should be updated"""
        session = self.get_session(session_id)
        new_turns = len(session.transcript) - session.summary_cursor
        return new_turns >= self.config.summary_frequency
    
    def update_profile(self, session_id: str, key: str, value: str):
        """Update user profile in session"""
        session = self.get_session(session_id)
        session.profile[key] = value
        logger.debug(f"Updated profile for session {session_id}: {key}={value}")
    
    def get_profile(self, session_id: str) -> Dict[str, str]:
        """Get user profile for session"""
        session = self.get_session(session_id)
        return session.profile.copy()
    
    def clear_session(self, session_id: str):
        """Clear a session"""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"Cleared session: {session_id}")
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        with self._lock:
            expired = [
                sid for sid, session in self._sessions.items()
                if session.is_expired(self.config.session_timeout_hours)
            ]
            
            for sid in expired:
                del self._sessions[sid]
            
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    def get_active_session_count(self) -> int:
        """Get number of active sessions"""
        return len(self._sessions)
    
    def get_session_stats(self, session_id: str) -> dict:
        """Get statistics for a session"""
        session = self.get_session(session_id)
        return session.to_dict()
