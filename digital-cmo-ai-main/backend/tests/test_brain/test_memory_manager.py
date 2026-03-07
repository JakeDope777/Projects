"""
Comprehensive tests for the Brain Memory Manager.

Tests cover:
- Persistent folder operations (Layer 2)
- Vector store integration (Layer 3)
- SQLite operations (Layer 4)
- Convenience methods
- Memory statistics
- Fallback behaviour
"""

import os
import pytest
from app.brain.memory_manager import MemoryManager
from app.brain.vector_store import FAISSVectorStore


@pytest.fixture
def memory(temp_memory_dir):
    return MemoryManager(
        memory_base_path=temp_memory_dir,
        db_path=":memory:",
        vector_store=None,  # Use fallback for basic tests
    )


@pytest.fixture
def memory_with_vector(temp_memory_dir, tmp_path):
    vector_store = FAISSVectorStore(
        persist_dir=str(tmp_path / "vectors"),
        dimension=128,
    )
    return MemoryManager(
        memory_base_path=temp_memory_dir,
        db_path=":memory:",
        vector_store=vector_store,
    )


# ---------------------------------------------------------------------------
# Layer 2: Persistent Folders
# ---------------------------------------------------------------------------

class TestMemoryManagerFolders:
    """Tests for persistent folder operations (Layer 2)."""

    def test_folder_structure_created(self, memory, temp_memory_dir):
        assert os.path.isdir(os.path.join(temp_memory_dir, "projects", "default"))
        assert os.path.isdir(os.path.join(temp_memory_dir, "workspace"))
        assert os.path.isdir(os.path.join(temp_memory_dir, "preferences"))
        assert os.path.isdir(os.path.join(temp_memory_dir, "knowledge_base"))

    def test_save_and_read(self, memory):
        memory.save_to_folder("workspace/test.md", "Hello World")
        content = memory.read_from_folder("workspace/test.md")
        assert content == "Hello World"

    def test_save_append(self, memory):
        memory.save_to_folder("workspace/log.md", "Line 1")
        memory.save_to_folder("workspace/log.md", "Line 2", append=True)
        content = memory.read_from_folder("workspace/log.md")
        assert "Line 1" in content
        assert "Line 2" in content

    def test_read_nonexistent_returns_none(self, memory):
        result = memory.read_from_folder("nonexistent/file.md")
        assert result is None

    def test_list_folder(self, memory):
        memory.save_to_folder("projects/test/goals.md", "Goal 1")
        memory.save_to_folder("projects/test/decisions.md", "Decision 1")
        files = memory.list_folder("projects/test")
        assert len(files) == 2

    def test_delete_file(self, memory):
        memory.save_to_folder("workspace/temp.md", "Temporary")
        assert memory.delete_from_folder("workspace/temp.md") is True
        assert memory.read_from_folder("workspace/temp.md") is None

    def test_delete_nonexistent(self, memory):
        assert memory.delete_from_folder("nonexistent.md") is False

    def test_save_creates_subdirectories(self, memory):
        memory.save_to_folder("deep/nested/path/file.md", "Content")
        content = memory.read_from_folder("deep/nested/path/file.md")
        assert content == "Content"


# ---------------------------------------------------------------------------
# Layer 3: Vector Store
# ---------------------------------------------------------------------------

class TestMemoryManagerVectorStore:
    """Tests for vector store integration (Layer 3)."""

    def test_store_embedding_with_vector_store(self, memory_with_vector):
        result = memory_with_vector.store_embedding(
            "Marketing budget is $10,000",
            {"tag": "budget"},
        )
        assert result is True

    def test_retrieve_similar_with_vector_store(self, memory_with_vector):
        memory_with_vector.store_embedding("Marketing budget is $10,000", {"tag": "budget"})
        memory_with_vector.store_embedding("Target audience is CTOs", {"tag": "audience"})
        memory_with_vector.store_embedding("Brand voice is professional", {"tag": "brand"})

        results = memory_with_vector.retrieve_similar("budget", k=3)
        assert len(results) > 0
        assert "text" in results[0]
        assert "score" in results[0]

    def test_store_embeddings_batch(self, memory_with_vector):
        texts = ["Fact 1", "Fact 2", "Fact 3"]
        metas = [{"i": 1}, {"i": 2}, {"i": 3}]
        result = memory_with_vector.store_embeddings_batch(texts, metas)
        assert result is True

    def test_retrieve_similar_empty(self, memory_with_vector):
        results = memory_with_vector.retrieve_similar("anything")
        assert results == []

    def test_memory_stats_with_vector(self, memory_with_vector):
        memory_with_vector.store_embedding("Test fact")
        stats = memory_with_vector.get_memory_stats()
        assert stats["vector_store_available"] is True
        assert stats["vector_document_count"] >= 1


class TestMemoryManagerVectorFallback:
    """Tests for the vector store fallback (Layer 3)."""

    def test_store_embedding_fallback(self, memory):
        result = memory.store_embedding("Test fact about marketing", {"tag": "test"})
        assert result is True

    def test_retrieve_similar_fallback(self, memory):
        memory.store_embedding("Marketing budget is $10,000", {"tag": "budget"})
        memory.store_embedding("Target audience is CTOs", {"tag": "audience"})
        results = memory.retrieve_similar("budget", k=5)
        assert len(results) >= 1
        assert any("budget" in r.get("text", "").lower() for r in results)

    def test_watch_conversation(self, memory):
        conversation = [
            {"role": "user", "content": "Our brand guideline is to use formal tone"},
            {"role": "assistant", "content": "Noted, I will use formal tone."},
            {"role": "user", "content": "What is the weather?"},
        ]
        snippets = memory.watch_conversation(conversation)
        assert len(snippets) >= 1  # "guideline" keyword should trigger extraction


# ---------------------------------------------------------------------------
# Layer 4: SQLite
# ---------------------------------------------------------------------------

class TestMemoryManagerSQL:
    """Tests for SQLite operations (Layer 4)."""

    def test_query_sql_basic(self, memory):
        # Create a test table
        memory.execute_sql(
            "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)"
        )
        memory.execute_sql("INSERT INTO test_table (name) VALUES (?)", ("Test",))
        results = memory.query_sql("SELECT * FROM test_table")
        assert len(results) == 1
        assert results[0]["name"] == "Test"

    def test_query_sql_error(self, memory):
        results = memory.query_sql("SELECT * FROM nonexistent_table")
        assert len(results) == 1
        assert "error" in results[0]

    def test_execute_sql(self, memory):
        memory.execute_sql(
            "CREATE TABLE IF NOT EXISTS exec_test (id INTEGER PRIMARY KEY, val TEXT)"
        )
        result = memory.execute_sql("INSERT INTO exec_test (val) VALUES (?)", ("hello",))
        assert result is True

    def test_execute_sql_error(self, memory):
        result = memory.execute_sql("INSERT INTO nonexistent (val) VALUES (?)", ("x",))
        assert result is False


# ---------------------------------------------------------------------------
# Convenience Methods
# ---------------------------------------------------------------------------

class TestMemoryManagerConvenience:
    """Tests for convenience methods."""

    def test_save_decision(self, memory):
        path = memory.save_decision("default", "Use FastAPI", "Better async support")
        content = memory.read_from_folder("projects/default/decisions.md")
        assert "Use FastAPI" in content
        assert "Better async support" in content

    def test_save_goal(self, memory):
        memory.save_goal("default", "Launch MVP in 2 weeks")
        content = memory.read_from_folder("projects/default/goals.md")
        assert "Launch MVP in 2 weeks" in content

    def test_update_status(self, memory):
        memory.update_status("All modules scaffolded")
        content = memory.read_from_folder("workspace/current_status.md")
        assert "All modules scaffolded" in content

    def test_get_project_context(self, memory):
        memory.save_goal("default", "Test goal")
        ctx = memory.get_project_context("default")
        assert "goals" in ctx
        assert ctx["goals"] is not None

    def test_get_project_context_empty(self, memory):
        ctx = memory.get_project_context("nonexistent_project")
        assert "goals" in ctx
        assert ctx["goals"] is None


# ---------------------------------------------------------------------------
# Memory Statistics
# ---------------------------------------------------------------------------

class TestMemoryStats:
    """Tests for memory statistics."""

    def test_stats_without_vector(self, memory):
        stats = memory.get_memory_stats()
        assert "folder_count" in stats
        assert "vector_store_available" in stats

    def test_stats_with_vector(self, memory_with_vector):
        stats = memory_with_vector.get_memory_stats()
        assert stats["vector_store_available"] is True
        assert "vector_document_count" in stats
