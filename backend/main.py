"""
Main application entry point
Initializes the RAG system and provides CLI/API interfaces
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.config import load_config
from core.logging_config import RAGLogger
from core.exceptions import RAGException
from rag_orchestrator import RAGOrchestrator


class RAGApplication:
    """Main RAG application"""
    
    def __init__(self):
        # Load configuration
        self.config = load_config()
        
        # Configure logging
        log_dir = Path(__file__).parent.parent / "logs"
        RAGLogger.configure(
            log_level=self.config.log_level,
            log_dir=log_dir
        )
        
        self.logger = RAGLogger.get_logger(__name__)
        self.logger.info("=" * 80)
        self.logger.info("RAG Application Starting...")
        self.logger.info("=" * 80)
        
        # Initialize orchestrator
        self.orchestrator = RAGOrchestrator(self.config)
        
        self.logger.info("RAG Application initialized successfully")
    
    def ask(self, query: str, session_id: str = "default") -> dict:
        """
        Ask a question and get an answer
        
        Args:
            query: User question
            session_id: Session identifier
            
        Returns:
            Dictionary with answer and metadata
        """
        try:
            return self.orchestrator.process_query(query, session_id)
        except RAGException as e:
            self.logger.error(f"RAG error: {str(e)}")
            return {
                "answer": "I encountered an error processing your question. Please try again.",
                "error": str(e),
                "type": "error"
            }
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return {
                "answer": "An unexpected error occurred. Please contact support.",
                "error": "Internal error",
                "type": "error"
            }
    
    def get_session_info(self, session_id: str) -> dict:
        """Get information about a session"""
        return self.orchestrator.get_session_stats(session_id)
    
    def clear_session(self, session_id: str):
        """Clear a conversation session"""
        self.orchestrator.clear_session(session_id)
    
    def run_cli(self):
        """Run interactive CLI"""
        self.logger.info("Starting CLI mode...")
        print("\n" + "=" * 80)
        print("RAG System - Interactive CLI")
        print("=" * 80)
        print("Ask questions about DevOps work items")
        print("Commands: 'exit' to quit, 'clear' to clear session, 'stats' for session info")
        print("=" * 80 + "\n")
        
        session_id = "cli_session"
        
        try:
            while True:
                try:
                    query = input("\n❓ Question: ").strip()
                    
                    if not query:
                        continue
                    
                    if query.lower() in ["exit", "quit"]:
                        print("\n👋 Goodbye!")
                        break
                    
                    if query.lower() == "clear":
                        self.clear_session(session_id)
                        print("✅ Session cleared")
                        continue
                    
                    if query.lower() == "stats":
                        stats = self.get_session_info(session_id)
                        print(f"\n📊 Session Stats:")
                        print(f"   Created: {stats.get('created_at')}")
                        print(f"   Turns: {stats.get('turn_count')}")
                        continue
                    
                    # Process query
                    print("\n🤔 Thinking...")
                    result = self.ask(query, session_id)
                    
                    # Display answer
                    print(f"\n💡 Answer:\n{result['answer']}\n")
                
                except KeyboardInterrupt:
                    print("\n\n👋 Goodbye!")
                    break
                
                except Exception as e:
                    print(f"\n❌ Error: {str(e)}")
                    self.logger.error(f"CLI error: {str(e)}", exc_info=True)
        
        finally:
            self.logger.info("CLI session ended")


def main():
    """Main entry point"""
    app = RAGApplication()
    app.run_cli()


if __name__ == "__main__":
    main()
