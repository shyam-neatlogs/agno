"""Neatlogs sandbox harness for agno-agi/agno#11904.

Reads one case from stdin ({"input": {"backend": ..., "filter": <FilterExpr.to_dict()>}}),
loads eight documents owned by different users into that vector database, searches with
the filter, and prints the names of the documents the search returned.
"""

import json
import logging
import os
import shutil
import sys
import tempfile
import uuid

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
logging.disable(logging.CRITICAL)

from agno.filters import from_dict  # noqa: E402
from agno.knowledge.document import Document  # noqa: E402

DOCS = [
    ("alice_plan", {"user_id": "alice", "team": "red", "score": 12, "region": "eu"}),
    ("alice_notes", {"user_id": "alice", "team": "blue", "score": 3, "region": "us"}),
    ("bob_secret", {"user_id": "bob", "team": "red", "score": 25, "region": "eu"}),
    ("bob_draft", {"user_id": "bob", "team": "blue", "score": 7, "region": "us"}),
    ("carol_report", {"user_id": "carol", "team": "red", "score": 18, "region": "apac"}),
    ("carol_memo", {"user_id": "carol", "team": "green", "score": 1, "region": "eu"}),
    ("dave_ledger", {"user_id": "dave", "team": "green", "score": 30, "region": "us"}),
    ("erin_brief", {"user_id": "erin", "team": "blue", "score": 15, "region": "apac"}),
]
VECTOR = [1.0, 0.0, 0.0, 0.0]


class FixedEmbedder:
    dimensions = 4

    def get_embedding(self, text):
        return VECTOR

    def get_embedding_and_usage(self, text):
        return VECTOR, {}


def open_db(backend, workdir):
    embedder = FixedEmbedder()
    name = f"t{uuid.uuid4().hex[:8]}"
    if backend == "qdrant":
        from agno.vectordb.qdrant import Qdrant

        return Qdrant(collection=name, location=":memory:", embedder=embedder)
    if backend == "chroma":
        from agno.vectordb.chroma import ChromaDb

        return ChromaDb(collection=name, path=workdir, embedder=embedder)
    if backend == "lancedb":
        from agno.vectordb.lancedb import LanceDb

        return LanceDb(table_name=name, uri=workdir, embedder=embedder)
    raise ValueError(f"unknown backend {backend}")


def run(case):
    workdir = tempfile.mkdtemp()
    try:
        db = open_db(case["backend"], workdir)
        db.create()
        db.insert(
            content_hash="neatlogs-11904",
            documents=[
                Document(id=uuid.uuid5(uuid.NAMESPACE_URL, name).hex, name=name, content=f"{name} record", meta_data=dict(meta), embedding=VECTOR)
                for name, meta in DOCS
            ],
        )
        results = db.search(query="record", limit=20, filters=[from_dict(case["filter"])]) or []
        return {"names": sorted(doc.name for doc in results)}
    except Exception as error:  # an honest refusal is reported, not a crash
        return {"error": type(error).__name__, "message": str(error)[:300]}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    case = json.loads(sys.stdin.readline())["input"]
    print(json.dumps({"output": run(case)}))
