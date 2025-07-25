import os
from typing import List, Dict, Optional, Any
import logging
import chromadb
from chromadb.utils import embedding_functions
from datetime import datetime


class RAGKnowledgeBase:
    """Retrieval-Augmented Generation for Blender and video making knowledge"""
    
    def __init__(self, collection_name: str = "blender_knowledge", 
                 persist_directory: str = "./chroma_db"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Initialize embedding function
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name="text-embedding-ada-002"
        )
        
        # Create or get collection
        self._initialize_collection()
    
    def _initialize_collection(self):
        """Initialize or get existing collection"""
        try:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_fn,
                metadata={"created_at": str(datetime.now())}
            )
            self.logger.info(f"Created new collection: {self.collection_name}")
        except Exception as e:
            if "already exists" in str(e):
                self.collection = self.client.get_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_fn
                )
                self.logger.info(f"Using existing collection: {self.collection_name}")
            else:
                raise
    
    def add_knowledge(self, documents: List[str], 
                     metadatas: Optional[List[Dict]] = None,
                     ids: Optional[List[str]] = None,
                     source_type: str = "general") -> int:
        """Add Blender tutorials and API documentation to knowledge base"""
        
        if not documents:
            return 0
        
        # Generate IDs if not provided
        if ids is None:
            timestamp = int(datetime.now().timestamp())
            ids = [f"{source_type}_{timestamp}_{i}" for i in range(len(documents))]
        
        # Add source type to metadata
        if metadatas is None:
            metadatas = []
        
        for i in range(len(documents)):
            if i < len(metadatas):
                metadatas[i]["source_type"] = source_type
            else:
                metadatas.append({"source_type": source_type})
        
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            self.logger.info(f"Added {len(documents)} documents to knowledge base")
            return len(documents)
        except Exception as e:
            self.logger.error(f"Failed to add documents: {str(e)}")
            raise
    
    def query(self, query_text: str, n_results: int = 5,
             filter_dict: Optional[Dict] = None) -> List[Dict]:
        """Query relevant knowledge for the given context"""
        
        try:
            # Build where clause for filtering
            where_clause = filter_dict if filter_dict else None
            
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_clause
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and len(results['documents']) > 0:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0.0,
                        'id': results['ids'][0][i] if results['ids'] else None
                    })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Query failed: {str(e)}")
            return []
    
    def load_blender_api_docs(self, docs_path: str) -> int:
        """Load Blender API documentation from files"""
        
        documents = []
        metadatas = []
        
        # Walk through documentation directory
        for root, dirs, files in os.walk(docs_path):
            for file in files:
                if file.endswith(('.txt', '.md', '.rst')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # Split large documents into chunks
                        chunks = self._split_document(content, chunk_size=1000)
                        
                        for i, chunk in enumerate(chunks):
                            documents.append(chunk)
                            metadatas.append({
                                "source": file_path,
                                "chunk": i,
                                "type": "api_documentation"
                            })
                    except Exception as e:
                        self.logger.error(f"Failed to load {file_path}: {str(e)}")
        
        if documents:
            return self.add_knowledge(documents, metadatas, source_type="api_docs")
        return 0
    
    def load_video_tutorials(self, tutorials: List[Dict[str, str]]) -> int:
        """Load video tutorial transcripts
        
        Args:
            tutorials: List of dicts with 'title', 'transcript', and optional 'url'
        """
        
        documents = []
        metadatas = []
        
        for tutorial in tutorials:
            if 'transcript' in tutorial:
                # Split transcript into chunks
                chunks = self._split_document(
                    tutorial['transcript'], 
                    chunk_size=500
                )
                
                for i, chunk in enumerate(chunks):
                    documents.append(chunk)
                    metadatas.append({
                        "title": tutorial.get('title', 'Unknown'),
                        "url": tutorial.get('url', ''),
                        "chunk": i,
                        "type": "video_tutorial"
                    })
        
        if documents:
            return self.add_knowledge(documents, metadatas, source_type="tutorials")
        return 0
    
    def _split_document(self, text: str, chunk_size: int = 1000, 
                       overlap: int = 100) -> List[str]:
        """Split document into overlapping chunks"""
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk = ' '.join(chunk_words)
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def clear_collection(self):
        """Clear all documents from the collection"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self._initialize_collection()
            self.logger.info(f"Cleared collection: {self.collection_name}")
        except Exception as e:
            self.logger.error(f"Failed to clear collection: {str(e)}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        try:
            count = self.collection.count()
            
            # Get sample of metadata to analyze
            sample = self.collection.get(limit=100)
            
            source_types = {}
            if sample['metadatas']:
                for metadata in sample['metadatas']:
                    source_type = metadata.get('source_type', 'unknown')
                    source_types[source_type] = source_types.get(source_type, 0) + 1
            
            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "source_types": source_types,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            self.logger.error(f"Failed to get stats: {str(e)}")
            return {}