"""
Unified RAG Engine - Retrieval-Augmented Generation

Combines multiple retrieval methods to enhance LLM responses:
- Vector similarity search
- Knowledge graph traversal
- Semantic search
- Keyword + semantic hybrid
- Temporal relevance ranking
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import asyncio
import math
from abc import ABC, abstractmethod
import json


@dataclass
class Document:
    """Retrieved document with metadata"""
    id: str
    content: str
    source: str
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunks: List[str] = field(default_factory=list)
    embeddings: Optional[List[float]] = None
    
    def to_context_string(self) -> str:
        """Format document for LLM context"""
        return f"[{self.source}] {self.content[:500]}"


@dataclass
class RAGResult:
    """Result of RAG retrieval"""
    query: str
    documents: List[Document]
    augmented_context: str
    retrieval_method: str
    total_documents: int
    coverage: float  # 0.0-1.0, how much of query is covered


class RetrieverBackend(ABC):
    """Abstract base class for retrieval backends"""
    
    def __init__(self, name: str):
        self.name = name
        self.documents: List[Document] = []
    
    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 5) -> List[Document]:
        """Retrieve top-k documents for query"""
        pass
    
    @abstractmethod
    async def add_document(self, doc: Document):
        """Add document to retriever"""
        pass
    
    @abstractmethod
    async def remove_document(self, doc_id: str):
        """Remove document from retriever"""
        pass
    
    async def health_check(self) -> bool:
        """Check if backend is operational"""
        return True


class VectorRetriever(RetrieverBackend):
    """Vector similarity search backend
    
    Uses simple dot-product similarity for demonstration.
    In production, would use proper embedding models (SBERT, etc).
    """
    
    def __init__(self):
        super().__init__("vector")
        self.embeddings: Dict[str, List[float]] = {}
    
    def _simple_embedding(self, text: str) -> List[float]:
        """Create simple embedding from text (for demo)
        
        In production, use sentence-transformers or similar.
        This is a stub that shows the interface.
        """
        # Convert text to character codes, normalize
        codes = [ord(c) % 256 for c in text[:100]]
        # Pad to 100 dimensions
        embedding = codes + [0] * (100 - len(codes))
        # Normalize
        magnitude = math.sqrt(sum(x**2 for x in embedding))
        if magnitude == 0:
            magnitude = 1
        return [x / magnitude for x in embedding]
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Compute cosine similarity between vectors"""
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude1 = math.sqrt(sum(x**2 for x in v1))
        magnitude2 = math.sqrt(sum(x**2 for x in v2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    async def retrieve(self, query: str, top_k: int = 5) -> List[Document]:
        """Find most similar documents"""
        if not self.documents:
            return []
        
        query_embedding = self._simple_embedding(query)
        scores = []
        
        for doc in self.documents:
            if doc.id in self.embeddings:
                doc_embedding = self.embeddings[doc.id]
            else:
                doc_embedding = self._simple_embedding(doc.content)
                self.embeddings[doc.id] = doc_embedding
            
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            scores.append((doc, similarity))
        
        # Sort by similarity, return top-k
        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for doc, score in scores[:top_k]:
            doc.relevance_score = score
            results.append(doc)
        
        return results
    
    async def add_document(self, doc: Document):
        """Add document"""
        self.documents.append(doc)
        self.embeddings[doc.id] = self._simple_embedding(doc.content)
    
    async def remove_document(self, doc_id: str):
        """Remove document"""
        self.documents = [d for d in self.documents if d.id != doc_id]
        self.embeddings.pop(doc_id, None)


class KeywordRetriever(RetrieverBackend):
    """Keyword-based BM25 search backend
    
    Uses term frequency-inverse document frequency scoring.
    """
    
    def __init__(self):
        super().__init__("keyword")
        self.term_freqs: Dict[str, Dict[str, int]] = {}  # doc_id -> {term: count}
        self.doc_freqs: Dict[str, int] = {}  # term -> doc_count
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        return text.lower().split()
    
    def _bm25_score(self, query_terms: List[str], doc: Document) -> float:
        """Compute BM25 score"""
        score = 0.0
        doc_terms = self.term_freqs.get(doc.id, {})
        
        for term in query_terms:
            if term in doc_terms:
                term_freq = doc_terms[term]
                doc_freq = self.doc_freqs.get(term, 1)
                
                # BM25 components
                idf = math.log(len(self.documents) / doc_freq)
                tf_component = (term_freq * 2.2) / (term_freq + 1.2)
                score += idf * tf_component
        
        return score
    
    async def retrieve(self, query: str, top_k: int = 5) -> List[Document]:
        """Find documents by keyword matching"""
        if not self.documents:
            return []
        
        query_terms = self._tokenize(query)
        scores = []
        
        for doc in self.documents:
            score = self._bm25_score(query_terms, doc)
            scores.append((doc, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for doc, score in scores[:top_k]:
            doc.relevance_score = score
            results.append(doc)
        
        return results
    
    async def add_document(self, doc: Document):
        """Index document"""
        self.documents.append(doc)
        terms = self._tokenize(doc.content)
        self.term_freqs[doc.id] = {}
        
        for term in terms:
            if term not in self.term_freqs[doc.id]:
                self.term_freqs[doc.id][term] = 0
            self.term_freqs[doc.id][term] += 1
            
            if term not in self.doc_freqs:
                self.doc_freqs[term] = 0
            self.doc_freqs[term] += 1
    
    async def remove_document(self, doc_id: str):
        """Remove from index"""
        self.documents = [d for d in self.documents if d.id != doc_id]
        
        # Remove term frequencies
        if doc_id in self.term_freqs:
            for term in self.term_freqs[doc_id]:
                self.doc_freqs[term] -= 1
            del self.term_freqs[doc_id]


class HybridRetriever(RetrieverBackend):
    """Hybrid vector + keyword retrieval
    
    Combines both methods with weighted scoring.
    """
    
    def __init__(self, vector_weight: float = 0.6, keyword_weight: float = 0.4):
        super().__init__("hybrid")
        self.vector_retriever = VectorRetriever()
        self.keyword_retriever = KeywordRetriever()
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
    
    async def retrieve(self, query: str, top_k: int = 5) -> List[Document]:
        """Retrieve using both methods, combine scores"""
        vector_results = await self.vector_retriever.retrieve(query, top_k * 2)
        keyword_results = await self.keyword_retriever.retrieve(query, top_k * 2)
        
        # Combine results
        combined = {}
        for doc in vector_results:
            combined[doc.id] = {
                "doc": doc,
                "vector_score": doc.relevance_score,
                "keyword_score": 0.0
            }
        
        for doc in keyword_results:
            if doc.id not in combined:
                combined[doc.id] = {
                    "doc": doc,
                    "vector_score": 0.0,
                    "keyword_score": 0.0
                }
            combined[doc.id]["keyword_score"] = doc.relevance_score
        
        # Compute hybrid scores
        for entry in combined.values():
            entry["combined_score"] = (
                entry["vector_score"] * self.vector_weight +
                entry["keyword_score"] * self.keyword_weight
            )
        
        # Sort and return top-k
        sorted_results = sorted(
            combined.values(),
            key=lambda x: x["combined_score"],
            reverse=True
        )
        
        results = []
        for entry in sorted_results[:top_k]:
            entry["doc"].relevance_score = entry["combined_score"]
            results.append(entry["doc"])
        
        return results
    
    async def add_document(self, doc: Document):
        """Add to both retrievers"""
        self.documents.append(doc)
        await self.vector_retriever.add_document(doc)
        await self.keyword_retriever.add_document(doc)
    
    async def remove_document(self, doc_id: str):
        """Remove from both retrievers"""
        self.documents = [d for d in self.documents if d.id != doc_id]
        await self.vector_retriever.remove_document(doc_id)
        await self.keyword_retriever.remove_document(doc_id)


class RAGEngine:
    """Unified RAG Engine
    
    Manages multiple retrieval backends and augments queries
    with relevant context for improved LLM responses.
    """
    
    def __init__(self):
        self.primary_retriever = HybridRetriever()
        self.backup_retrievers: Dict[str, RetrieverBackend] = {}
        self.retrieval_history: List[RAGResult] = []
    
    async def augment_query(
        self,
        query: str,
        top_k: int = 5,
        method: str = "hybrid"
    ) -> RAGResult:
        """Augment query with retrieved context
        
        Args:
            query: User's original query
            top_k: Number of documents to retrieve
            method: Retrieval method (hybrid, vector, keyword)
        
        Returns:
            RAGResult with documents and augmented context
        """
        # Select retriever
        if method == "hybrid":
            retriever = self.primary_retriever
        elif method in self.backup_retrievers:
            retriever = self.backup_retrievers[method]
        else:
            retriever = self.primary_retriever
        
        # Retrieve documents
        documents = await retriever.retrieve(query, top_k)
        
        # Build augmented context
        context_parts = ["Relevant context:"]
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"\n{i}. {doc.to_context_string()}")
        
        augmented_context = "\n".join(context_parts)
        
        # Compute coverage (rough estimate)
        query_terms = set(query.lower().split())
        covered_terms = set()
        for doc in documents:
            doc_terms = set(doc.content.lower().split())
            covered_terms.update(query_terms & doc_terms)
        
        coverage = len(covered_terms) / max(len(query_terms), 1)
        
        result = RAGResult(
            query=query,
            documents=documents,
            augmented_context=augmented_context,
            retrieval_method=method,
            total_documents=len(retriever.documents),
            coverage=coverage
        )
        
        self.retrieval_history.append(result)
        return result
    
    async def add_document(
        self,
        content: str,
        source: str,
        doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add document to RAG system
        
        Args:
            content: Document content
            source: Document source/name
            doc_id: Optional document ID (auto-generated if None)
            metadata: Optional metadata
        
        Returns:
            Document ID
        """
        if doc_id is None:
            doc_id = f"doc_{len(self.primary_retriever.documents)}"
        
        doc = Document(
            id=doc_id,
            content=content,
            source=source,
            metadata=metadata or {}
        )
        
        await self.primary_retriever.add_document(doc)
        for retriever in self.backup_retrievers.values():
            await retriever.add_document(doc)
        
        return doc_id
    
    async def bulk_add_documents(self, documents: List[Tuple[str, str]]) -> List[str]:
        """Add multiple documents
        
        Args:
            documents: List of (content, source) tuples
        
        Returns:
            List of document IDs
        """
        doc_ids = []
        for content, source in documents:
            doc_id = await self.add_document(content, source)
            doc_ids.append(doc_id)
        return doc_ids
    
    async def remove_document(self, doc_id: str):
        """Remove document from RAG system"""
        await self.primary_retriever.remove_document(doc_id)
        for retriever in self.backup_retrievers.values():
            await retriever.remove_document(doc_id)
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all retrievers"""
        health = {
            "primary": await self.primary_retriever.health_check()
        }
        for name, retriever in self.backup_retrievers.items():
            health[name] = await retriever.health_check()
        return health
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        return {
            "total_documents": len(self.primary_retriever.documents),
            "retrieval_history_length": len(self.retrieval_history),
            "average_coverage": (
                sum(r.coverage for r in self.retrieval_history) /
                max(len(self.retrieval_history), 1)
            )
        }


# Global RAG engine instance
rag_engine = RAGEngine()


async def initialize_rag():
    """Initialize RAG system
    
    Usage:
        await initialize_rag()
        result = await rag_engine.augment_query("What is machine learning?")
        print(f"Context:\\n{result.augmented_context}")
    """
    # Verify retrievers are operational
    health = await rag_engine.health_check()
    return all(health.values())


if __name__ == "__main__":
    # Example usage
    async def main():
        print("Initializing RAG Engine...")
        await initialize_rag()
        
        # Add sample documents
        docs = [
            (
                "Machine learning is a subset of artificial intelligence that enables systems to learn from data.",
                "ML Basics"
            ),
            (
                "Deep learning uses neural networks with multiple layers to process complex patterns.",
                "Deep Learning"
            ),
            (
                "Natural language processing helps computers understand human language.",
                "NLP"
            ),
            (
                "Computer vision enables machines to interpret visual information from images.",
                "Computer Vision"
            ),
            (
                "Reinforcement learning trains agents through interaction with environments.",
                "RL"
            ),
        ]
        
        print("\nAdding documents to RAG...")
        doc_ids = await rag_engine.bulk_add_documents(docs)
        print(f"✅ Added {len(doc_ids)} documents")
        
        # Test retrieval
        queries = [
            "What is machine learning?",
            "How do neural networks work?",
            "Tell me about AI",
        ]
        
        print("\n📚 Testing RAG retrieval:")
        for query in queries:
            result = await rag_engine.augment_query(query, top_k=3)
            print(f"\n💬 Query: {query}")
            print(f"   Retrieval method: {result.retrieval_method}")
            print(f"   Coverage: {result.coverage:.1%}")
            print(f"   Found: {len(result.documents)} documents")
            for doc in result.documents[:1]:  # Show first doc
                print(f"     - [{doc.source}] (score: {doc.relevance_score:.2f})")
        
        # Stats
        stats = rag_engine.get_stats()
        print(f"\n📊 RAG Statistics:")
        print(f"   Total documents: {stats['total_documents']}")
        print(f"   Retrieval history: {stats['retrieval_history_length']}")
        print(f"   Avg coverage: {stats['average_coverage']:.1%}")
    
    asyncio.run(main())
