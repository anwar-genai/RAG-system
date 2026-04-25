"""Per-user memory store.

A single FAISS index holds durable facts for all users, isolated at retrieval
time by a ``user_id`` metadata filter. The Django ORM is the source of truth
(``UserMemory`` rows); FAISS is a search-only mirror that can be rebuilt from
the DB at any time via :func:`rebuild_memory_index`.

Deduplication is cosine-based: before inserting a new memory we check whether
the user already has a sufficiently similar one. OpenAI's
``text-embedding-3-small`` returns L2-normalized vectors, so an L2 distance
under ~0.4 corresponds to cosine similarity > 0.92 — strict enough to catch
near-duplicates without blocking nuanced updates.
"""

from __future__ import annotations

import re
import threading
from pathlib import Path
from typing import List, Optional

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


_SENTINEL_USER_ID = -1  # seed doc so FAISS can be created empty; filtered out everywhere
_DEDUPE_L2_THRESHOLD = 0.4  # ~cosine sim > 0.92 for normalized embeddings
_DEFAULT_FETCH_K = 30


# ----------------------------------------------------------------------
# PII guardrail
# ----------------------------------------------------------------------
# Belt-and-suspenders: the extraction prompt tells the LLM not to produce PII,
# but we also hard-filter any extracted fact that matches these patterns before
# it's ever written to the DB or the vector index.
_PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),                              # US SSN
    re.compile(r"\b(?:\d[ -]?){13,19}\b"),                             # credit-card-ish
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),                            # OpenAI / Stripe secret key
    re.compile(r"\b(?:Bearer|Token)\s+[A-Za-z0-9._\-]{16,}", re.I),    # auth headers
    re.compile(r"\b[A-Fa-f0-9]{32,}\b"),                               # long hex secrets
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),                 # PEM private key
]


def contains_pii(text: str) -> bool:
    """True if the text matches any obvious PII / secret pattern."""
    return any(p.search(text) for p in _PII_PATTERNS)


class MemoryStore:
    """FAISS-backed search index for per-user memories."""

    def __init__(self, embeddings, index_path: Path):
        self.embeddings = embeddings
        self.index_path = index_path
        self._lock = threading.Lock()
        self.vs: Optional[FAISS] = None
        self._load_or_create()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def _load_or_create(self) -> None:
        if self.index_path.exists():
            self.vs = FAISS.load_local(
                str(self.index_path),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
            return

        # FAISS can't be created empty — seed with a sentinel that all real
        # queries filter out via the user_id metadata check.
        seed = Document(
            page_content="__memory_index_init__",
            metadata={"user_id": _SENTINEL_USER_ID, "sentinel": True},
        )
        self.vs = FAISS.from_documents([seed], self.embeddings)
        self._save()

    def _save(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.vs.save_local(str(self.index_path))

    # ------------------------------------------------------------------
    # Write path
    # ------------------------------------------------------------------
    def add(self, user_id: int, content: str, memory_db_id: int) -> bool:
        """Embed and index a memory. Returns False if skipped as a near-duplicate."""
        content = (content or "").strip()
        if not content:
            return False

        with self._lock:
            if self._is_duplicate(user_id, content):
                return False
            self.vs.add_texts(
                texts=[content],
                metadatas=[{"user_id": user_id, "memory_db_id": memory_db_id}],
                ids=[self._doc_id(memory_db_id)],
            )
            self._save()
        return True

    def delete(self, memory_db_id: int) -> None:
        with self._lock:
            try:
                self.vs.delete([self._doc_id(memory_db_id)])
                self._save()
            except Exception:
                # Missing ID is fine — DB row may have been deleted before index caught up.
                pass

    # ------------------------------------------------------------------
    # Read path
    # ------------------------------------------------------------------
    def search(self, user_id: int, query: str, k: int = 3) -> List[str]:
        """Return up to k memory texts most relevant to query for this user."""
        query = (query or "").strip()
        if not query or self.vs is None:
            return []

        try:
            docs = self.vs.similarity_search(
                query,
                k=k,
                filter={"user_id": user_id},
                fetch_k=_DEFAULT_FETCH_K,
            )
        except Exception:
            return []

        return [
            d.page_content
            for d in docs
            if d.metadata.get("user_id") == user_id
            and not d.metadata.get("sentinel")
        ]

    def _is_duplicate(self, user_id: int, content: str) -> bool:
        try:
            hits = self.vs.similarity_search_with_score(
                content,
                k=3,
                filter={"user_id": user_id},
                fetch_k=_DEFAULT_FETCH_K,
            )
        except Exception:
            return False
        return any(
            score < _DEDUPE_L2_THRESHOLD
            and doc.metadata.get("user_id") == user_id
            and not doc.metadata.get("sentinel")
            for doc, score in hits
        )

    @staticmethod
    def _doc_id(memory_db_id: int) -> str:
        return f"mem_{memory_db_id}"


# ----------------------------------------------------------------------
# Singleton + DB-authoritative rebuild
# ----------------------------------------------------------------------
_memory_store: Optional[MemoryStore] = None
_memory_store_lock = threading.Lock()


def get_memory_store() -> MemoryStore:
    """Return the process-wide MemoryStore, lazily initializing from RAG embeddings."""
    global _memory_store
    if _memory_store is None:
        with _memory_store_lock:
            if _memory_store is None:
                from .rag import get_rag_system  # late import to avoid cycle
                rag = get_rag_system()
                index_path = rag.vector_store_dir / "memory_index"
                _memory_store = MemoryStore(rag.embeddings, index_path)
    return _memory_store


def rebuild_memory_index() -> int:
    """Wipe and rebuild the FAISS memory index from active UserMemory rows.

    Called by a management command or a ``/api/memory/rebuild`` admin endpoint
    when the index gets out of sync with the DB. Returns the number of memories
    re-indexed."""
    from .models import UserMemory  # late import — Django may not be ready at module load

    store = get_memory_store()
    # Drop the on-disk index then re-init (sentinel + empty).
    with store._lock:
        if store.index_path.exists():
            import shutil
            shutil.rmtree(store.index_path)
        store._load_or_create()

    count = 0
    for mem in UserMemory.objects.filter(is_active=True).iterator():
        if store.add(mem.user_id, mem.content, mem.id):
            count += 1
    return count
