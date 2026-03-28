"""
PHASE 19: RAG + MEMORY SYSTEM
=============================
In-memory document store, hybrid retrieval, and context assembly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from math import sqrt
from typing import Any, Dict, List, Optional, Tuple


def _tokenize(text: str) -> List[str]:
    return [t.strip(".,!?;:()[]{}\"'").lower() for t in text.split() if t.strip()]


def _bow_vector(text: str) -> Dict[str, float]:
    v: Dict[str, float] = {}
    for tok in _tokenize(text):
        v[tok] = v.get(tok, 0.0) + 1.0
    return v


def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in a.keys())
    na = sqrt(sum(v * v for v in a.values()))
    nb = sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


@dataclass
class DocumentChunk:
    chunk_id: str
    doc_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Dict[str, float] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RetrievalHit:
    chunk_id: str
    doc_id: str
    score_semantic: float
    score_keyword: float
    score_hybrid: float
    content: str
    metadata: Dict[str, Any]


class DocumentStore:
    def __init__(self) -> None:
        self.chunks: Dict[str, DocumentChunk] = {}
        self.by_doc: Dict[str, List[str]] = {}

    def add_chunk(self, chunk: DocumentChunk) -> None:
        self.chunks[chunk.chunk_id] = chunk
        self.by_doc.setdefault(chunk.doc_id, []).append(chunk.chunk_id)

    def add_document(self, doc_id: str, text: str, chunk_size_words: int = 120) -> List[DocumentChunk]:
        words = text.split()
        created: List[DocumentChunk] = []
        if not words:
            return created
        i = 0
        idx = 0
        while i < len(words):
            part = words[i : i + chunk_size_words]
            content = " ".join(part)
            chunk_id = f"{doc_id}::chunk::{idx}"
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                content=content,
                embedding=_bow_vector(content),
            )
            self.add_chunk(chunk)
            created.append(chunk)
            i += chunk_size_words
            idx += 1
        return created

    def get_chunk(self, chunk_id: str) -> Optional[DocumentChunk]:
        return self.chunks.get(chunk_id)

    def all_chunks(self) -> List[DocumentChunk]:
        return list(self.chunks.values())


class HybridRetriever:
    def __init__(self, store: DocumentStore, semantic_weight: float = 0.7, keyword_weight: float = 0.3) -> None:
        self.store = store
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight

    def _keyword_score(self, query_tokens: List[str], content_tokens: List[str]) -> float:
        if not query_tokens:
            return 0.0
        q = set(query_tokens)
        c = set(content_tokens)
        if not c:
            return 0.0
        return len(q & c) / len(q)

    def search(self, query: str, top_k: int = 5, min_score: float = 0.05) -> List[RetrievalHit]:
        q_vec = _bow_vector(query)
        q_toks = _tokenize(query)
        hits: List[RetrievalHit] = []
        for chunk in self.store.all_chunks():
            s_sem = _cosine(q_vec, chunk.embedding)
            s_kw = self._keyword_score(q_toks, _tokenize(chunk.content))
            s_h = self.semantic_weight * s_sem + self.keyword_weight * s_kw
            if s_h >= min_score:
                hits.append(
                    RetrievalHit(
                        chunk_id=chunk.chunk_id,
                        doc_id=chunk.doc_id,
                        score_semantic=round(s_sem, 4),
                        score_keyword=round(s_kw, 4),
                        score_hybrid=round(s_h, 4),
                        content=chunk.content,
                        metadata=chunk.metadata,
                    )
                )
        hits.sort(key=lambda h: h.score_hybrid, reverse=True)
        return hits[:top_k]


class MemoryManager:
    def __init__(self) -> None:
        self.short_term: List[str] = []
        self.long_term: List[str] = []

    def add_short_term(self, event: str) -> None:
        self.short_term.append(event)
        if len(self.short_term) > 20:
            self.short_term = self.short_term[-20:]

    def consolidate(self) -> str:
        if not self.short_term:
            return ""
        summary = " | ".join(self.short_term[-8:])
        self.long_term.append(summary)
        self.short_term.clear()
        return summary

    def recall(self, query: str, top_k: int = 3) -> List[str]:
        q = set(_tokenize(query))
        scored: List[Tuple[float, str]] = []
        for item in self.long_term:
            toks = set(_tokenize(item))
            score = len(q & toks) / max(len(q), 1)
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [x[1] for x in scored[:top_k] if x[0] > 0]


class RAGMemorySystem:
    def __init__(self) -> None:
        self.store = DocumentStore()
        self.retriever = HybridRetriever(self.store)
        self.memory = MemoryManager()

    def ingest_document(self, doc_id: str, text: str, chunk_size_words: int = 120) -> int:
        chunks = self.store.add_document(doc_id, text, chunk_size_words=chunk_size_words)
        return len(chunks)

    def retrieve_context(self, query: str, top_k: int = 5) -> List[RetrievalHit]:
        return self.retriever.search(query, top_k=top_k)

    def build_context(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        hits = self.retrieve_context(query, top_k=top_k)
        recalled = self.memory.recall(query, top_k=3)
        assembled = "\n\n".join(h.content for h in hits)
        return {
            "query": query,
            "hits": hits,
            "recalled_memory": recalled,
            "assembled_context": assembled,
        }
