"""
Memory Manager - handles the four memory layers:

1. **Short-term**: conversation context (managed via ConversationStateManager).
2. **Persistent folders**: structured files under ``memory/``.
3. **Medium-term**: vector embeddings for similarity search (FAISS / ChromaDB).
4. **Long-term**: SQLite for structured data queries.

Improvements over the original:
- Proper vector store integration via ``VectorStoreBase``.
- Automatic fact extraction via ``MemoryWatcher``.
- Conversation summarisation via ``ConversationSummarizer``.
- Richer metadata on stored memories.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timezone

from ..core.config import settings
from .vector_store import VectorStoreBase, FAISSVectorStore, create_vector_store


class MemoryManager:
    """
    Unified interface for all four memory layers.
    """

    def __init__(
        self,
        memory_base_path: Optional[str] = None,
        db_path: Optional[str] = None,
        vector_store: Optional[VectorStoreBase] = None,
        vector_backend: str = "faiss",
        vector_persist_dir: Optional[str] = None,
    ):
        self.memory_base_path = Path(memory_base_path or settings.MEMORY_BASE_PATH)
        self.db_path = db_path or settings.DATABASE_URL.replace("sqlite:///", "")

        # For in-memory databases, keep a single persistent connection
        self._persistent_conn: Optional[sqlite3.Connection] = None
        if self.db_path == ":memory:":
            self._persistent_conn = sqlite3.connect(":memory:")
            self._persistent_conn.row_factory = sqlite3.Row

        # Initialise vector store
        if vector_store is not None:
            self.vector_store = vector_store
        else:
            persist_dir = vector_persist_dir or str(self.memory_base_path / "vector_store")
            try:
                self.vector_store: Optional[VectorStoreBase] = create_vector_store(
                    backend=vector_backend,
                    persist_dir=persist_dir,
                )
            except Exception:
                self.vector_store = None

        self._ensure_folder_structure()

    def _ensure_folder_structure(self) -> None:
        """Create the standard memory folder structure if it doesn't exist."""
        folders = [
            self.memory_base_path / "projects" / "default",
            self.memory_base_path / "workspace",
            self.memory_base_path / "preferences",
            self.memory_base_path / "knowledge_base",
        ]
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)

    # ── Layer 2: Persistent Folders ──────────────────────────────────

    def save_to_folder(self, file_path: str, content: str, append: bool = False) -> str:
        """
        Save content to a structured memory file.

        Args:
            file_path: Relative path within the memory folder.
            content: Text content to write.
            append: If True, append to existing file; otherwise overwrite.

        Returns:
            The absolute path of the written file.
        """
        full_path = self.memory_base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        mode = "a" if append else "w"
        with open(full_path, mode, encoding="utf-8") as f:
            if append:
                f.write(f"\n\n---\n_Updated: {datetime.now(timezone.utc).isoformat()}_\n\n")
            f.write(content)

        return str(full_path)

    def read_from_folder(self, file_path: str) -> Optional[str]:
        """Read content from a structured memory file."""
        full_path = self.memory_base_path / file_path
        if full_path.exists():
            return full_path.read_text(encoding="utf-8")
        return None

    def list_folder(self, folder_path: str = "") -> list[str]:
        """List all files in a memory subfolder."""
        target = self.memory_base_path / folder_path
        if not target.exists():
            return []
        files = []
        for item in target.rglob("*"):
            if item.is_file():
                files.append(str(item.relative_to(self.memory_base_path)))
        return sorted(files)

    def delete_from_folder(self, file_path: str) -> bool:
        """Delete a memory file. Returns True if the file was deleted."""
        full_path = self.memory_base_path / file_path
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    # ── Layer 3: Medium-term (Vector Store) ──────────────────────────

    def store_embedding(self, text: str, metadata: Optional[dict] = None) -> bool:
        """
        Store a text embedding in the vector database.

        Args:
            text: The text to embed and store.
            metadata: Additional metadata.

        Returns:
            True if successfully stored, False otherwise.
        """
        if self.vector_store is not None:
            try:
                self.vector_store.add(text, metadata=metadata)
                return True
            except Exception:
                pass

        # Fallback: store as a JSON line in a local file
        fallback_path = self.memory_base_path / "workspace" / "embeddings_log.jsonl"
        entry = {
            "text": text,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(fallback_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return True

    def store_embeddings_batch(self, texts: list[str], metadatas: Optional[list[dict]] = None) -> bool:
        """Store multiple embeddings at once."""
        if self.vector_store is not None:
            try:
                self.vector_store.add_batch(texts, metadatas)
                return True
            except Exception:
                pass

        # Fallback
        metadatas = metadatas or [{} for _ in texts]
        for text, meta in zip(texts, metadatas):
            self.store_embedding(text, meta)
        return True

    def retrieve_similar(self, query: str, k: int = 5, filter_metadata: Optional[dict] = None) -> list[dict]:
        """
        Retrieve the top-k most similar memory snippets.

        Args:
            query: The search query text.
            k: Number of results to return.
            filter_metadata: Optional metadata filter.

        Returns:
            List of dicts with 'text', 'score', and 'metadata' keys.
        """
        if self.vector_store is not None:
            try:
                results = self.vector_store.search(query, k=k, filter_metadata=filter_metadata)
                return results
            except Exception:
                pass

        return self._fallback_search(query, k)

    def _fallback_search(self, query: str, k: int) -> list[dict]:
        """Simple keyword-based fallback search over stored snippets."""
        log_path = self.memory_base_path / "workspace" / "embeddings_log.jsonl"
        if not log_path.exists():
            return []

        results = []
        query_terms = set(query.lower().split())
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    text = entry.get("text", "").lower()
                    score = sum(1 for term in query_terms if term in text)
                    if score > 0:
                        results.append({
                            "text": entry["text"],
                            "score": score,
                            "metadata": entry.get("metadata", {}),
                        })
                except json.JSONDecodeError:
                    continue

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]

    def get_memory_stats(self) -> dict:
        """Return statistics about the memory store."""
        stats: dict[str, Any] = {
            "folder_count": len(self.list_folder()),
            "vector_store_available": self.vector_store is not None,
        }
        if self.vector_store is not None:
            stats["vector_document_count"] = self.vector_store.count()
        return stats

    # ── Layer 3.5: Conversation watching (delegated to MemoryWatcher) ─

    def watch_conversation(self, conversation: list[dict]) -> list[dict]:
        """
        Analyse a conversation and extract salient information for embedding.

        This is a simplified built-in watcher. For advanced extraction, use
        the standalone ``MemoryWatcher`` class.
        """
        snippets = []
        keywords = [
            "decide", "decision", "goal", "prefer", "always",
            "never", "important", "remember", "brand", "guideline",
            "budget", "target", "deadline", "strategy",
        ]
        for msg in conversation:
            content = msg.get("content", "")
            if any(keyword in content.lower() for keyword in keywords):
                snippets.append({
                    "text": content,
                    "role": msg.get("role", "unknown"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "type": "conversation_extract",
                })
        return snippets

    # ── Layer 4: Long-term (SQLite) ──────────────────────────────────

    def _get_connection(self) -> sqlite3.Connection:
        """Return a database connection (persistent for :memory:, new otherwise)."""
        if self._persistent_conn is not None:
            return self._persistent_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def query_sql(self, sql: str, params: Optional[tuple] = None) -> list[dict]:
        """Execute a read-only SQL query against the SQLite database."""
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            rows = [dict(row) for row in cursor.fetchall()]
            if self._persistent_conn is None:
                conn.close()
            return rows
        except Exception as e:
            return [{"error": str(e)}]

    def execute_sql(self, sql: str, params: Optional[tuple] = None) -> bool:
        """Execute a write SQL statement."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            conn.commit()
            if self._persistent_conn is None:
                conn.close()
            return True
        except Exception:
            return False

    # ── Convenience Methods ──────────────────────────────────────────

    def save_decision(self, project: str, decision: str, reasoning: str) -> str:
        """Save a key decision to the project's decisions file."""
        content = f"## Decision\n{decision}\n\n**Reasoning:** {reasoning}\n"
        path = self.save_to_folder(
            f"projects/{project}/decisions.md", content, append=True
        )
        # Also store in vector store for semantic retrieval
        self.store_embedding(
            f"Decision: {decision}. Reasoning: {reasoning}",
            metadata={"type": "decision", "project": project},
        )
        return path

    def save_goal(self, project: str, goal: str) -> str:
        """Save a goal to the project's goals file."""
        content = f"- {goal}\n"
        path = self.save_to_folder(
            f"projects/{project}/goals.md", content, append=True
        )
        self.store_embedding(
            f"Goal: {goal}",
            metadata={"type": "goal", "project": project},
        )
        return path

    def update_status(self, status: str) -> str:
        """Update the current workspace status."""
        content = (
            f"# Current Status\n\n{status}\n\n"
            f"_Last updated: {datetime.now(timezone.utc).isoformat()}_\n"
        )
        return self.save_to_folder("workspace/current_status.md", content)

    def get_project_context(self, project: str = "default") -> dict[str, Optional[str]]:
        """Retrieve all context for a given project."""
        return {
            "goals": self.read_from_folder(f"projects/{project}/goals.md"),
            "decisions": self.read_from_folder(f"projects/{project}/decisions.md"),
            "status": self.read_from_folder("workspace/current_status.md"),
            "preferences": self.read_from_folder("preferences/coding_style.md"),
            "knowledge": self.read_from_folder("knowledge_base/reference_data.md"),
        }
