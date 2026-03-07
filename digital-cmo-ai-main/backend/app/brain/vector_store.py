"""
Vector Store - provides semantic search over memory using dense embeddings.

Supports two backends:
- **FAISS** (default) – fast, local, file-backed index.
- **ChromaDB** – persistent, metadata-rich document store.

Both backends expose the same ``VectorStoreBase`` interface so the rest of the
brain module is backend-agnostic.
"""

from __future__ import annotations

import json
import os
import uuid
import hashlib
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

import numpy as np


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class VectorStoreBase(ABC):
    """Common interface for all vector store backends."""

    @abstractmethod
    def add(self, text: str, metadata: Optional[dict] = None, doc_id: Optional[str] = None) -> str:
        """Add a document and return its ID."""

    @abstractmethod
    def add_batch(self, texts: list[str], metadatas: Optional[list[dict]] = None) -> list[str]:
        """Add multiple documents at once."""

    @abstractmethod
    def search(self, query: str, k: int = 5, filter_metadata: Optional[dict] = None) -> list[dict]:
        """Return top-k results as ``[{"text": ..., "score": ..., "metadata": ...}]``."""

    @abstractmethod
    def delete(self, doc_id: str) -> bool:
        """Delete a document by ID."""

    @abstractmethod
    def count(self) -> int:
        """Return the number of stored documents."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all documents."""


# ---------------------------------------------------------------------------
# Lightweight built-in embedding (TF-IDF-like, no external model needed)
# ---------------------------------------------------------------------------

class BuiltinEmbedder:
    """
    A simple TF-IDF-style embedder that produces fixed-dimension dense vectors
    without requiring any external model or API call.

    This is suitable for development / testing.  In production, replace with
    ``OpenAIEmbedder`` or a SentenceTransformers model.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self._vocab: dict[str, int] = {}
        self._idf: dict[str, float] = {}
        self._doc_count = 0

    def embed(self, text: str) -> list[float]:
        """Return a deterministic dense vector for *text*."""
        tokens = self._tokenize(text)
        vec = np.zeros(self.dimension, dtype=np.float32)
        for token in tokens:
            # Deterministic hash → dimension index
            h = int(hashlib.md5(token.encode()).hexdigest(), 16)
            idx = h % self.dimension
            vec[idx] += 1.0
        # L2-normalise
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        import re
        return re.findall(r"[a-z0-9]+", text.lower())


# ---------------------------------------------------------------------------
# OpenAI Embedder (uses the configured API key)
# ---------------------------------------------------------------------------

class OpenAIEmbedder:
    """
    Produces embeddings via the OpenAI-compatible ``/v1/embeddings`` endpoint.
    Requires ``OPENAI_API_KEY`` in the environment.
    """

    def __init__(self, model: str = "text-embedding-ada-002", dimension: int = 1536):
        self.model = model
        self.dimension = dimension
        self._client: Any = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI()
        return self._client

    def embed(self, text: str) -> list[float]:
        client = self._get_client()
        resp = client.embeddings.create(input=[text], model=self.model)
        return resp.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        client = self._get_client()
        resp = client.embeddings.create(input=texts, model=self.model)
        return [d.embedding for d in sorted(resp.data, key=lambda x: x.index)]


# ---------------------------------------------------------------------------
# FAISS Backend
# ---------------------------------------------------------------------------

class FAISSVectorStore(VectorStoreBase):
    """
    FAISS-backed vector store with file persistence.

    Stores document texts and metadata in a sidecar JSON file alongside the
    FAISS index binary.
    """

    def __init__(
        self,
        persist_dir: str = "./data/vector_store",
        embedder: Optional[Any] = None,
        dimension: int = 384,
    ):
        import faiss

        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.embedder = embedder or BuiltinEmbedder(dimension=dimension)
        self.dimension = dimension

        self._index_path = self.persist_dir / "faiss.index"
        self._meta_path = self.persist_dir / "faiss_meta.json"

        # Document metadata store: id → {text, metadata}
        self._docs: dict[str, dict] = {}
        # Ordered list of IDs matching FAISS internal row order
        self._id_order: list[str] = []

        # Load or create index
        if self._index_path.exists() and self._meta_path.exists():
            self._index = faiss.read_index(str(self._index_path))
            self._load_meta()
        else:
            self._index = faiss.IndexFlatIP(self.dimension)  # inner-product (cosine on normalised vecs)
            self._save()

    # -- persistence helpers ------------------------------------------------

    def _save(self) -> None:
        import faiss
        faiss.write_index(self._index, str(self._index_path))
        with open(self._meta_path, "w", encoding="utf-8") as f:
            json.dump({"docs": self._docs, "id_order": self._id_order}, f)

    def _load_meta(self) -> None:
        with open(self._meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._docs = data.get("docs", {})
        self._id_order = data.get("id_order", [])

    # -- VectorStoreBase implementation -------------------------------------

    def add(self, text: str, metadata: Optional[dict] = None, doc_id: Optional[str] = None) -> str:
        doc_id = doc_id or str(uuid.uuid4())
        vec = np.array([self.embedder.embed(text)], dtype=np.float32)
        self._index.add(vec)
        self._docs[doc_id] = {"text": text, "metadata": metadata or {}}
        self._id_order.append(doc_id)
        self._save()
        return doc_id

    def add_batch(self, texts: list[str], metadatas: Optional[list[dict]] = None) -> list[str]:
        if not texts:
            return []
        metadatas = metadatas or [{} for _ in texts]
        vecs = np.array(self.embedder.embed_batch(texts), dtype=np.float32)
        ids = []
        for i, text in enumerate(texts):
            doc_id = str(uuid.uuid4())
            self._docs[doc_id] = {"text": text, "metadata": metadatas[i]}
            self._id_order.append(doc_id)
            ids.append(doc_id)
        self._index.add(vecs)
        self._save()
        return ids

    def search(self, query: str, k: int = 5, filter_metadata: Optional[dict] = None) -> list[dict]:
        if self._index.ntotal == 0:
            return []
        k = min(k, self._index.ntotal)
        vec = np.array([self.embedder.embed(query)], dtype=np.float32)
        scores, indices = self._index.search(vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._id_order):
                continue
            doc_id = self._id_order[idx]
            doc = self._docs.get(doc_id)
            if doc is None:
                continue
            # Optional metadata filter
            if filter_metadata:
                if not all(doc.get("metadata", {}).get(fk) == fv for fk, fv in filter_metadata.items()):
                    continue
            results.append({
                "text": doc["text"],
                "score": float(score),
                "metadata": doc.get("metadata", {}),
                "id": doc_id,
            })
        return results

    def delete(self, doc_id: str) -> bool:
        if doc_id in self._docs:
            del self._docs[doc_id]
            # FAISS doesn't support single-row deletion easily; we rebuild
            self._rebuild_index()
            return True
        return False

    def count(self) -> int:
        return len(self._docs)

    def clear(self) -> None:
        import faiss
        self._docs.clear()
        self._id_order.clear()
        self._index = faiss.IndexFlatIP(self.dimension)
        self._save()

    def _rebuild_index(self) -> None:
        """Rebuild the FAISS index from the remaining documents."""
        import faiss
        self._index = faiss.IndexFlatIP(self.dimension)
        new_order = []
        vecs = []
        for doc_id in self._id_order:
            if doc_id in self._docs:
                vecs.append(self.embedder.embed(self._docs[doc_id]["text"]))
                new_order.append(doc_id)
        self._id_order = new_order
        if vecs:
            self._index.add(np.array(vecs, dtype=np.float32))
        self._save()


# ---------------------------------------------------------------------------
# ChromaDB Backend
# ---------------------------------------------------------------------------

class ChromaVectorStore(VectorStoreBase):
    """
    ChromaDB-backed vector store with built-in persistence and metadata filtering.
    """

    def __init__(
        self,
        persist_dir: str = "./data/chroma_store",
        collection_name: str = "digital_cmo_memory",
        embedder: Optional[Any] = None,
    ):
        import chromadb

        self.embedder = embedder or BuiltinEmbedder()
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, text: str, metadata: Optional[dict] = None, doc_id: Optional[str] = None) -> str:
        doc_id = doc_id or str(uuid.uuid4())
        embedding = self.embedder.embed(text)
        meta = self._sanitise_metadata(metadata or {})
        self._collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[meta],
        )
        return doc_id

    def add_batch(self, texts: list[str], metadatas: Optional[list[dict]] = None) -> list[str]:
        if not texts:
            return []
        metadatas = metadatas or [{} for _ in texts]
        ids = [str(uuid.uuid4()) for _ in texts]
        embeddings = self.embedder.embed_batch(texts)
        metas = [self._sanitise_metadata(m) for m in metadatas]
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metas,
        )
        return ids

    def search(self, query: str, k: int = 5, filter_metadata: Optional[dict] = None) -> list[dict]:
        total = self._collection.count()
        if total == 0:
            return []
        k = min(k, total)
        embedding = self.embedder.embed(query)
        where = filter_metadata if filter_metadata else None
        results = self._collection.query(
            query_embeddings=[embedding],
            n_results=k,
            where=where,
        )
        output = []
        docs = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        ids = results.get("ids", [[]])[0]
        for i, doc in enumerate(docs):
            output.append({
                "text": doc,
                "score": 1.0 - distances[i] if distances else 0.0,
                "metadata": metadatas[i] if metadatas else {},
                "id": ids[i] if ids else "",
            })
        return output

    def delete(self, doc_id: str) -> bool:
        try:
            self._collection.delete(ids=[doc_id])
            return True
        except Exception:
            return False

    def count(self) -> int:
        return self._collection.count()

    def clear(self) -> None:
        # ChromaDB doesn't have a bulk-clear; delete and recreate
        name = self._collection.name
        meta = self._collection.metadata
        self._client.delete_collection(name)
        self._collection = self._client.get_or_create_collection(name=name, metadata=meta)

    @staticmethod
    def _sanitise_metadata(meta: dict) -> dict:
        """ChromaDB only accepts str/int/float/bool metadata values and non-empty dicts."""
        clean = {}
        for k, v in meta.items():
            if isinstance(v, (str, int, float, bool)):
                clean[k] = v
            else:
                clean[k] = str(v)
        # ChromaDB rejects empty metadata dicts; ensure at least one key
        if not clean:
            clean["_source"] = "digital_cmo"
        return clean


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_vector_store(
    backend: str = "faiss",
    persist_dir: str = "./data/vector_store",
    embedder: Optional[Any] = None,
    dimension: int = 384,
    **kwargs: Any,
) -> VectorStoreBase:
    """
    Factory function to create the appropriate vector store backend.

    Args:
        backend: ``"faiss"`` or ``"chroma"``.
        persist_dir: Directory for persistence files.
        embedder: Optional embedder instance (must have ``.embed()`` and ``.embed_batch()``).
        dimension: Embedding dimension (only used for FAISS with BuiltinEmbedder).
    """
    if backend == "chroma":
        return ChromaVectorStore(
            persist_dir=persist_dir,
            embedder=embedder,
            **kwargs,
        )
    else:
        return FAISSVectorStore(
            persist_dir=persist_dir,
            embedder=embedder,
            dimension=dimension,
        )
