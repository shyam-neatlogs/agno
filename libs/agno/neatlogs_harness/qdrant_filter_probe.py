"""Neatlogs Sandbox harness for agno-agi/agno#11907.

One document with the given metadata goes into an in-memory Qdrant; the
search runs with the given filters. Returns how many documents matched.
This file is test scaffolding: the fix belongs in agno/vectordb/qdrant/.
"""

from agno.knowledge.document import Document
from agno.vectordb.qdrant import Qdrant


class _FixedEmbedder:
    dimensions: int = 4

    def get_embedding(self, text: str) -> list[float]:
        return [1.0, 0.0, 0.0, 0.0]

    def get_embedding_and_usage(self, text: str) -> tuple[list[float], dict]:
        return [1.0, 0.0, 0.0, 0.0], {}


def run_qdrant_filter_search(meta: dict, filters: dict) -> dict:
    db = Qdrant(collection="probe", location=":memory:", embedder=_FixedEmbedder())
    db.create()
    db.insert(
        documents=[
            Document(id="1", name="probe", content="probe", meta_data=meta, embedding=[1.0, 0.0, 0.0, 0.0])
        ],
        content_hash="h1",
    )
    return {"matches": len(db.search(query="probe", limit=10, filters=filters) or [])}
