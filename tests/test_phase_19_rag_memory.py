"""PHASE 19 tests: RAG + memory system."""

from pradysagican.memory.rag_memory import RAGMemorySystem


def test_ingest_document_creates_chunks() -> None:
    system = RAGMemorySystem()
    text = " ".join(["retrieval generation context pipeline"] * 80)
    count = system.ingest_document("doc-1", text, chunk_size_words=50)
    assert count >= 2


def test_hybrid_retrieval_returns_hits() -> None:
    system = RAGMemorySystem()
    system.ingest_document(
        "doc-ai",
        "Retrieval augmented generation uses external context and grounding for answers.",
        chunk_size_words=30,
    )
    system.ingest_document(
        "doc-ops",
        "Kubernetes and deployment workflows focus on scaling and reliability.",
        chunk_size_words=30,
    )
    hits = system.retrieve_context("How does retrieval and context grounding work?", top_k=3)
    assert len(hits) >= 1
    assert hits[0].doc_id == "doc-ai"
    assert hits[0].score_hybrid >= 0.05


def test_memory_consolidation_and_recall() -> None:
    system = RAGMemorySystem()
    system.memory.add_short_term("we discussed retrieval pipeline for context assembly")
    system.memory.add_short_term("we discussed latency optimization for deployment")
    summary = system.memory.consolidate()
    assert "retrieval" in summary
    recalled = system.memory.recall("retrieval context")
    assert len(recalled) >= 1


def test_build_context_includes_hits_and_memory() -> None:
    system = RAGMemorySystem()
    system.ingest_document(
        "doc-1",
        "Agent workflows can use retrieval for context and generation for final output.",
        chunk_size_words=20,
    )
    system.memory.add_short_term("retrieval helps context fidelity")
    system.memory.consolidate()
    ctx = system.build_context("retrieval context generation", top_k=2)
    assert "assembled_context" in ctx
    assert len(ctx["hits"]) >= 1
    assert isinstance(ctx["recalled_memory"], list)
