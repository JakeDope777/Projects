"""
Comprehensive tests for the Vector Store module.

Tests cover:
- BuiltinEmbedder
- FAISSVectorStore (add, search, delete, batch, persistence)
- ChromaVectorStore (add, search, delete, batch)
- Factory function
"""

import os
import tempfile

import pytest
from app.brain.vector_store import (
    BuiltinEmbedder,
    FAISSVectorStore,
    ChromaVectorStore,
    create_vector_store,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def embedder():
    return BuiltinEmbedder(dimension=128)


@pytest.fixture
def faiss_store(tmp_path):
    return FAISSVectorStore(
        persist_dir=str(tmp_path / "faiss"),
        dimension=128,
    )


@pytest.fixture
def chroma_store(tmp_path):
    return ChromaVectorStore(
        persist_dir=str(tmp_path / "chroma"),
        collection_name="test_collection",
    )


# ---------------------------------------------------------------------------
# BuiltinEmbedder tests
# ---------------------------------------------------------------------------

class TestBuiltinEmbedder:
    """Tests for the built-in hash-based embedder."""

    def test_embed_returns_list(self, embedder):
        vec = embedder.embed("hello world")
        assert isinstance(vec, list)
        assert len(vec) == 128

    def test_embed_deterministic(self, embedder):
        v1 = embedder.embed("test text")
        v2 = embedder.embed("test text")
        assert v1 == v2

    def test_embed_different_texts(self, embedder):
        v1 = embedder.embed("hello")
        v2 = embedder.embed("goodbye")
        assert v1 != v2

    def test_embed_normalized(self, embedder):
        import math
        vec = embedder.embed("some text here")
        norm = math.sqrt(sum(x * x for x in vec))
        assert abs(norm - 1.0) < 0.01

    def test_embed_batch(self, embedder):
        texts = ["text one", "text two", "text three"]
        vecs = embedder.embed_batch(texts)
        assert len(vecs) == 3
        assert all(len(v) == 128 for v in vecs)

    def test_embed_empty_string(self, embedder):
        vec = embedder.embed("")
        assert isinstance(vec, list)
        assert len(vec) == 128


# ---------------------------------------------------------------------------
# FAISSVectorStore tests
# ---------------------------------------------------------------------------

class TestFAISSVectorStore:
    """Tests for the FAISS-backed vector store."""

    def test_add_and_count(self, faiss_store):
        faiss_store.add("Hello world", metadata={"tag": "greeting"})
        assert faiss_store.count() == 1

    def test_add_returns_id(self, faiss_store):
        doc_id = faiss_store.add("Test document")
        assert isinstance(doc_id, str)
        assert len(doc_id) > 0

    def test_add_with_custom_id(self, faiss_store):
        doc_id = faiss_store.add("Test", doc_id="custom-123")
        assert doc_id == "custom-123"

    def test_search_returns_results(self, faiss_store):
        faiss_store.add("Marketing budget is $10,000")
        faiss_store.add("Target audience is CTOs")
        faiss_store.add("Brand voice is professional")
        results = faiss_store.search("budget", k=3)
        assert len(results) > 0
        assert "text" in results[0]
        assert "score" in results[0]

    def test_search_empty_store(self, faiss_store):
        results = faiss_store.search("anything")
        assert results == []

    def test_search_relevance(self, faiss_store):
        faiss_store.add("Our marketing budget is $50,000 per quarter")
        faiss_store.add("The weather is sunny today")
        faiss_store.add("Budget allocation for advertising campaigns")
        results = faiss_store.search("marketing budget", k=3)
        # The budget-related docs should score higher
        assert len(results) == 3
        texts = [r["text"] for r in results]
        assert any("budget" in t.lower() for t in texts[:2])

    def test_add_batch(self, faiss_store):
        texts = ["Doc 1", "Doc 2", "Doc 3"]
        ids = faiss_store.add_batch(texts)
        assert len(ids) == 3
        assert faiss_store.count() == 3

    def test_add_batch_with_metadata(self, faiss_store):
        texts = ["Doc A", "Doc B"]
        metas = [{"type": "a"}, {"type": "b"}]
        ids = faiss_store.add_batch(texts, metadatas=metas)
        assert len(ids) == 2

    def test_add_batch_empty(self, faiss_store):
        ids = faiss_store.add_batch([])
        assert ids == []

    def test_delete(self, faiss_store):
        doc_id = faiss_store.add("To be deleted")
        assert faiss_store.count() == 1
        assert faiss_store.delete(doc_id) is True
        assert faiss_store.count() == 0

    def test_delete_nonexistent(self, faiss_store):
        assert faiss_store.delete("nonexistent-id") is False

    def test_clear(self, faiss_store):
        faiss_store.add("Doc 1")
        faiss_store.add("Doc 2")
        assert faiss_store.count() == 2
        faiss_store.clear()
        assert faiss_store.count() == 0

    def test_persistence(self, tmp_path):
        persist_dir = str(tmp_path / "persist_test")
        store1 = FAISSVectorStore(persist_dir=persist_dir, dimension=128)
        store1.add("Persistent document")
        assert store1.count() == 1

        # Create a new store pointing to the same directory
        store2 = FAISSVectorStore(persist_dir=persist_dir, dimension=128)
        assert store2.count() == 1
        results = store2.search("Persistent", k=1)
        assert len(results) == 1
        assert "Persistent document" in results[0]["text"]

    def test_search_with_metadata_filter(self, faiss_store):
        faiss_store.add("Doc A", metadata={"category": "marketing"})
        faiss_store.add("Doc B", metadata={"category": "sales"})
        results = faiss_store.search("Doc", k=5, filter_metadata={"category": "marketing"})
        assert all(r["metadata"].get("category") == "marketing" for r in results)

    def test_search_k_larger_than_store(self, faiss_store):
        faiss_store.add("Only doc")
        results = faiss_store.search("doc", k=100)
        assert len(results) == 1


# ---------------------------------------------------------------------------
# ChromaVectorStore tests
# ---------------------------------------------------------------------------

class TestChromaVectorStore:
    """Tests for the ChromaDB-backed vector store."""

    def test_add_and_count(self, chroma_store):
        chroma_store.add("Hello world")
        assert chroma_store.count() == 1

    def test_add_returns_id(self, chroma_store):
        doc_id = chroma_store.add("Test document")
        assert isinstance(doc_id, str)

    def test_search_returns_results(self, chroma_store):
        chroma_store.add("Marketing budget is $10,000")
        chroma_store.add("Target audience is CTOs")
        results = chroma_store.search("budget", k=2)
        assert len(results) > 0
        assert "text" in results[0]
        assert "score" in results[0]

    def test_search_empty_store(self, chroma_store):
        results = chroma_store.search("anything")
        assert results == []

    def test_add_batch(self, chroma_store):
        texts = ["Doc 1", "Doc 2", "Doc 3"]
        ids = chroma_store.add_batch(texts)
        assert len(ids) == 3
        assert chroma_store.count() == 3

    def test_delete(self, chroma_store):
        doc_id = chroma_store.add("To be deleted")
        assert chroma_store.delete(doc_id) is True

    def test_clear(self, chroma_store):
        chroma_store.add("Doc 1")
        chroma_store.add("Doc 2")
        chroma_store.clear()
        assert chroma_store.count() == 0

    def test_metadata_sanitization(self, chroma_store):
        # ChromaDB only accepts str/int/float/bool
        doc_id = chroma_store.add(
            "Test",
            metadata={"list_val": [1, 2, 3], "str_val": "hello", "int_val": 42},
        )
        assert isinstance(doc_id, str)


# ---------------------------------------------------------------------------
# Factory function tests
# ---------------------------------------------------------------------------

class TestCreateVectorStore:
    """Tests for the factory function."""

    def test_create_faiss(self, tmp_path):
        store = create_vector_store(
            backend="faiss",
            persist_dir=str(tmp_path / "faiss"),
            dimension=64,
        )
        assert isinstance(store, FAISSVectorStore)

    def test_create_chroma(self, tmp_path):
        store = create_vector_store(
            backend="chroma",
            persist_dir=str(tmp_path / "chroma"),
        )
        assert isinstance(store, ChromaVectorStore)

    def test_default_is_faiss(self, tmp_path):
        store = create_vector_store(persist_dir=str(tmp_path / "default"))
        assert isinstance(store, FAISSVectorStore)
