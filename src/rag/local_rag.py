#!/usr/bin/env python3
"""
Local RAG System for Synth
Uses Ollama embeddings and Qdrant for vector storage
Integrates with LangChain for orchestration

Author: Project Synth
Version: 2.0 - LangChain Integration
"""

import os
import sys
import hashlib
import requests
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("⚠️  Qdrant not installed. Run: pip install qdrant-client")

try:
    from langchain_community.embeddings import OllamaEmbeddings
    from langchain_community.vectorstores import Qdrant
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️  LangChain not installed. Run: pip install langchain langchain-community")


@dataclass
class DocumentChunk:
    """Represents a chunk of text with metadata"""
    text: str
    source: str
    chunk_id: str
    metadata: Dict
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class SynthRAG:
    """
    Local RAG system using Ollama embeddings + Qdrant vector DB + LangChain
    
    Features:
    - LangChain integration for orchestration
    - Ollama embeddings (3584 dimensions from qwen2.5:7b)
    - Qdrant vector storage (local or server)
    - Web search integration
    - Clipboard content indexing
    - Query with context retrieval
    - DeltaBrain integration
    """
    
    def __init__(self, 
                 brain_client=None,
                 ollama_host: str = "localhost",
                 ollama_port: int = 11435,  # Use balanced mode port (7B model)
                 qdrant_path: str = "./data/qdrant",
                 collection_name: str = "synth_knowledge",
                 chunk_size: int = 500,
                 chunk_overlap: int = 50):
        """
        Initialize RAG system - LOCAL MODE ONLY
        
        Args:
            brain_client: Optional DeltaBrain instance for integration
            ollama_host: Ollama server hostname
            ollama_port: Ollama port (11435 = 7B balanced model)
            qdrant_path: Path to Qdrant storage (local disk mode)
            collection_name: Name of Qdrant collection
            chunk_size: Size of text chunks for splitting
            chunk_overlap: Overlap between chunks
        """
        self.brain_client = brain_client
        self.ollama_host = ollama_host
        self.ollama_port = ollama_port
        self.collection_name = collection_name
        self.embedding_model = "qwen2.5:7b"  # Use existing 7B model for embeddings
        self.embedding_dim = 3584  # Qwen2.5:7b actual embedding dimension
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Simple text splitter (no LangChain needed)
        self.text_splitter = None
        
        # Initialize Qdrant client (LOCAL MODE ONLY)
        if QDRANT_AVAILABLE:
            try:
                # Create data directory if needed
                os.makedirs(qdrant_path, exist_ok=True)
                
                # Initialize local Qdrant client
                self.qdrant = QdrantClient(path=qdrant_path)
                
                # Create collection if doesn't exist
                self._ensure_collection()
                
                print(f"✅ RAG initialized: {collection_name} (local mode)")
            except Exception as e:
                print(f"⚠️  Qdrant initialization failed: {e}")
                self.qdrant = None
        else:
            self.qdrant = None
            print("⚠️  RAG disabled (Qdrant not available)")
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        if not self.qdrant:
            return
            
        try:
            collections = self.qdrant.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                self.qdrant.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                print(f"✅ Created collection: {self.collection_name}")
        except Exception as e:
            print(f"⚠️  Collection creation failed: {e}")
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding vector from Ollama nomic-embed-text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (768 dimensions) or None if failed
        """
        try:
            url = f"http://{self.ollama_host}:{self.ollama_port}/api/embeddings"
            
            response = requests.post(url, json={
                "model": self.embedding_model,
                "prompt": text
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                embedding = data.get('embedding', [])
                
                if len(embedding) == self.embedding_dim:
                    return embedding
                else:
                    print(f"⚠️  Wrong embedding dimension: {len(embedding)} != {self.embedding_dim}")
                    return None
            else:
                print(f"⚠️  Embedding request failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"⚠️  Embedding error: {e}")
            return None
    
    def add_document(self, text: str, source: str, metadata: Optional[Dict] = None) -> bool:
        """
        Add single document to vector store
        
        Args:
            text: Document text
            source: Source identifier (url, file path, "clipboard", etc.)
            metadata: Additional metadata
            
        Returns:
            True if successful
        """
        if not self.qdrant:
            return False
            
        try:
            # Generate chunk ID from content hash
            chunk_id = hashlib.md5(text.encode()).hexdigest()
            
            # Get embedding
            embedding = self.get_embedding(text)
            if not embedding:
                print(f"⚠️  Failed to get embedding for: {text[:50]}...")
                return False
            
            # Prepare metadata
            full_metadata = {
                "source": source,
                "timestamp": datetime.now().isoformat(),
                "text_length": len(text),
                **(metadata or {})
            }
            
            # Create point
            point = PointStruct(
                id=chunk_id,
                vector=embedding,
                payload={
                    "text": text,
                    "source": source,
                    "metadata": full_metadata
                }
            )
            
            # Upsert to Qdrant
            self.qdrant.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            return True
            
        except Exception as e:
            print(f"⚠️  Failed to add document: {e}")
            return False
    
    def add_documents(self, texts: List[str], metadatas: Optional[List[Dict]] = None, sources: Optional[List[str]] = None) -> int:
        """
        Add multiple documents to vector store (batch operation)
        
        Args:
            texts: List of document texts
            metadatas: Optional list of metadata dicts (one per text)
            sources: Optional list of source identifiers (one per text)
            
        Returns:
            Number of documents successfully added
        """
        if not self.qdrant:
            return 0
        
        count = 0
        for i, text in enumerate(texts):
            source = sources[i] if sources and i < len(sources) else f"doc_{i}"
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            
            # Use text splitter to chunk long documents
            if self.text_splitter and len(text) > self.chunk_size:
                chunks = self.text_splitter.split_text(text)
                for j, chunk in enumerate(chunks):
                    chunk_metadata = {
                        **metadata,
                        "chunk_index": j,
                        "total_chunks": len(chunks),
                        "is_chunked": True
                    }
                    if self.add_document(chunk, source, chunk_metadata):
                        count += 1
            else:
                if self.add_document(text, source, metadata):
                    count += 1
        
        return count
    
    def similarity_search(self, query: str, k: int = 5, min_score: float = 0.3) -> List[Dict]:
        """
        Perform similarity search (alias for search() method)
        
        Args:
            query: Search query
            k: Number of results to return
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of similar documents with scores
        """
        return self.search(query, top_k=k, min_score=min_score)
    
    def add_clipboard_content(self, text: str, metadata: Optional[Dict] = None) -> bool:
        """
        Add clipboard content to RAG
        
        Args:
            text: Clipboard text
            metadata: Additional metadata
            
        Returns:
            True if successful
        """
        # Split into chunks if too long
        max_chunk_size = 1000
        
        if len(text) > max_chunk_size:
            # Split by paragraphs
            chunks = []
            current_chunk = ""
            
            for paragraph in text.split('\n\n'):
                if len(current_chunk) + len(paragraph) > max_chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    current_chunk += "\n\n" + paragraph if current_chunk else paragraph
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # Add each chunk
            success_count = 0
            for i, chunk in enumerate(chunks):
                chunk_metadata = {
                    **(metadata or {}),
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
                if self.add_document(chunk, "clipboard", chunk_metadata):
                    success_count += 1
            
            return success_count > 0
        else:
            return self.add_document(text, "clipboard", metadata)
    
    def add_web_results(self, results: List, query: str) -> int:
        """
        Add web search results to RAG
        
        Args:
            results: List of SearchResult objects from web_search.py
            query: Original query
            
        Returns:
            Number of results added
        """
        count = 0
        for result in results:
            text = f"{result.title}\n\n{result.snippet}"
            metadata = {
                "url": result.url,
                "source_type": result.source,
                "query": query
            }
            if self.add_document(text, result.url, metadata):
                count += 1
        
        return count
    
    def search(self, query: str, top_k: int = 5, min_score: float = 0.3) -> List[Dict]:
        """
        Search vector store for relevant documents
        
        Args:
            query: Search query
            top_k: Number of results to return
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of relevant documents with scores
        """
        if not self.qdrant:
            return []
            
        try:
            # Get query embedding
            query_embedding = self.get_embedding(query)
            if not query_embedding:
                return []
            
            # Search Qdrant using query_points (new API)
            results = self.qdrant.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=top_k
            ).points
            
            # Format results and filter by score
            documents = []
            for result in results:
                # Normalize score to 0-1 range (cosine similarity is -1 to 1)
                normalized_score = (result.score + 1) / 2
                
                # Only include results above minimum score
                if normalized_score >= min_score:
                    documents.append({
                        "text": result.payload.get("text", ""),
                        "source": result.payload.get("source", ""),
                        "score": normalized_score,
                        "metadata": result.payload.get("metadata", {})
                    })
            
            return documents
            
        except Exception as e:
            print(f"⚠️  Search failed: {e}")
            return []
    
    def query(self, question: str, context_sources: Optional[List[str]] = None, top_k: int = 5, min_score: float = 0.5) -> Dict:
        """
        Main RAG query function - retrieves relevant context and formats for AI
        
        Args:
            question: User's question
            context_sources: Optional list of sources to filter by
            top_k: Number of context chunks to retrieve
            min_score: Minimum similarity score (0-1, default 0.5)
            
        Returns:
            Dict with context, sources, and formatted prompt
        """
        # Search for relevant documents
        relevant_docs = self.search(question, top_k=top_k, min_score=min_score)
        
        # Filter by sources if specified
        if context_sources:
            relevant_docs = [
                doc for doc in relevant_docs 
                if any(source in doc['source'] for source in context_sources)
            ]
        
        # Build context text
        context_parts = []
        sources = []
        
        for i, doc in enumerate(relevant_docs, 1):
            score = doc['score']
            text = doc['text']
            source = doc['source']
            
            # Already filtered by min_score in search()
            context_parts.append(f"[{i}] (Score: {score:.2f}) {text}")
            sources.append({
                "source": source,
                "score": score,
                "text": text[:100] + "..." if len(text) > 100 else text
            })
        
        # Format context
        context_text = "\n\n".join(context_parts) if context_parts else ""
        
        # Build enhanced prompt
        if context_text:
            enhanced_prompt = f"""CONTEXT FROM KNOWLEDGE BASE:
{context_text}

USER QUESTION: {question}

Using the context above, answer the user's question. If the context doesn't contain enough information, say so and provide what you know from general knowledge."""
        else:
            enhanced_prompt = f"""USER QUESTION: {question}

(No relevant context found in knowledge base. Answer from general knowledge.)"""
        
        return {
            "question": question,
            "context": context_text,
            "prompt": enhanced_prompt,
            "sources": sources,
            "num_sources": len(sources),
            "has_context": len(sources) > 0
        }
    
    def get_stats(self) -> Dict:
        """Get RAG statistics"""
        if not self.qdrant:
            return {"status": "disabled"}
            
        try:
            collection_info = self.qdrant.get_collection(self.collection_name)
            return {
                "status": "active",
                "collection": self.collection_name,
                "vector_count": collection_info.points_count,
                "embedding_model": self.embedding_model,
                "embedding_dim": self.embedding_dim
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def clear_collection(self) -> bool:
        """Clear all vectors from collection"""
        if not self.qdrant:
            return False
            
        try:
            self.qdrant.delete_collection(self.collection_name)
            self._ensure_collection()
            print(f"✅ Cleared collection: {self.collection_name}")
            return True
        except Exception as e:
            print(f"⚠️  Failed to clear collection: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Test RAG system
    print("🧪 Testing SynthRAG...")
    
    rag = SynthRAG()
    
    # Test embedding
    print("\n1️⃣  Testing embeddings...")
    embedding = rag.get_embedding("This is a test sentence")
    if embedding:
        print(f"   ✅ Got embedding: {len(embedding)} dimensions")
    else:
        print(f"   ❌ Embedding failed")
    
    # Test adding documents
    print("\n2️⃣  Testing document addition...")
    success = rag.add_document(
        "Python is a high-level programming language known for its simplicity",
        "test_doc_1",
        {"category": "programming"}
    )
    print(f"   {'✅' if success else '❌'} Add document 1")
    
    success = rag.add_document(
        "Machine learning is a subset of artificial intelligence",
        "test_doc_2",
        {"category": "ai"}
    )
    print(f"   {'✅' if success else '❌'} Add document 2")
    
    # Test search
    print("\n3️⃣  Testing search...")
    results = rag.search("What is Python?", top_k=2)
    print(f"   Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"   {i}. Score: {result['score']:.3f} - {result['text'][:60]}...")
    
    # Test query
    print("\n4️⃣  Testing RAG query...")
    rag_result = rag.query("Tell me about Python programming")
    print(f"   Has context: {rag_result['has_context']}")
    print(f"   Sources: {rag_result['num_sources']}")
    if rag_result['sources']:
        print(f"   Top source: {rag_result['sources'][0]['source']}")
    
    # Get stats
    print("\n5️⃣  RAG Statistics:")
    stats = rag.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ RAG test complete!")
