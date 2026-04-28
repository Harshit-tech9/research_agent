import uuid
import logging
from pathlib import Path

from config import MEMORY_STORE_DIR

logger = logging.getLogger(__name__)


class LongTermMemory:
    """
    Persistent vector store backed by ChromaDB.
    Stores Q&A pairs and observations so the agent can recall
    relevant past context via semantic similarity search.
    Falls back to a no-op silently if ChromaDB is unavailable.
    """

    def __init__(self, collection_name: str = "agent_memory", persist_dir: str = None):
        self._available = False
        self._collection = None
        dir_ = persist_dir or MEMORY_STORE_DIR
        try:
            import chromadb
            Path(dir_).mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=dir_)
            self._collection = client.get_or_create_collection(name=collection_name)
            self._available = True
            logger.info("LongTermMemory ready (%d items).", self._collection.count())
        except Exception as exc:
            logger.warning("LongTermMemory unavailable: %s", exc)

    # ── Write ─────────────────────────────────────────────────────────────────

    def store(self, text: str, metadata: dict | None = None) -> None:
        if not self._available:
            return
        try:
            self._collection.add(
                documents=[text],
                metadatas=[metadata or {}],
                ids=[str(uuid.uuid4())],
            )
        except Exception as exc:
            logger.warning("LongTermMemory store failed: %s", exc)

    # ── Read ──────────────────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        if not self._available:
            return []
        try:
            n = min(top_k, self._collection.count())
            if n == 0:
                return []
            results = self._collection.query(query_texts=[query], n_results=n)
            return results["documents"][0] if results["documents"] else []
        except Exception as exc:
            logger.warning("LongTermMemory retrieve failed: %s", exc)
            return []

    def count(self) -> int:
        if not self._available or self._collection is None:
            return 0
        try:
            return self._collection.count()
        except Exception:
            return 0

    @property
    def is_available(self) -> bool:
        return self._available
