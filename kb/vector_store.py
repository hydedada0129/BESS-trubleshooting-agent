"""Chroma helpers shared by ingest and retrieval.py. Local only; telemetry disabled."""

from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.config import Settings

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CHROMA_PATH = REPO_ROOT / "chroma"
COLLECTION_NAME = "cases"


def open_client(path: Path = DEFAULT_CHROMA_PATH) -> chromadb.ClientAPI:
    # anonymized_telemetry=False: nothing about the knowledge base leaves the machine.
    return chromadb.PersistentClient(path=str(path), settings=Settings(anonymized_telemetry=False))


def get_collection(path: Path = DEFAULT_CHROMA_PATH):
    """Open the existing case collection. Raises if ingest has not been run."""
    return open_client(path).get_collection(COLLECTION_NAME)


def recreate_collection(path: Path = DEFAULT_CHROMA_PATH):
    """Drop and recreate the case collection (ingest always rebuilds from scratch)."""
    client = open_client(path)
    if COLLECTION_NAME in [c.name for c in client.list_collections()]:
        client.delete_collection(COLLECTION_NAME)
    return client.create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
