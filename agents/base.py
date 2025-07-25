from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
import logging

from knowledge.rag import RAGKnowledgeBase


class BaseAgent(ABC):    
    def __init__(self, api_key: str, rag_kb: Optional[RAGKnowledgeBase] = None,
                 config: Optional[Dict[str, Any]] = None):
        self.api_key = api_key
        self.rag_kb = rag_kb
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize agent-specific resources
        self._initialize()
    
    @abstractmethod
    def _initialize(self):
        """Initialize agent-specific resources"""
        pass
    
    def get_rag_context(self, query: str, n_results: int = 3) -> str:
        """Get relevant context from RAG knowledge base"""
        if not self.rag_kb:
            return ""
        
        relevant_docs = self.rag_kb.query(query, n_results=n_results)
        context = "\n".join([doc['document'] for doc in relevant_docs])
        return context
    
    @abstractmethod
    def process(self, *args, **kwargs) -> Any:
        """Main processing method for the agent"""
        pass
    
    def log_info(self, message: str):
        self.logger.info(f"[{self.__class__.__name__}] {message}")
    
    def log_error(self, message: str):
        self.logger.error(f"[{self.__class__.__name__}] {message}")
    
    def log_debug(self, message: str):
        self.logger.debug(f"[{self.__class__.__name__}] {message}")