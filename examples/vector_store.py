"""
vector_store.py — Demonstrates pgvector upsert and search.

Requires: OPENAI_API_KEY and POSTGRES_URL environment variables
Install : uv add 'ragstack[openai]' 'ragstack[pgvector]'

Run the schema first if you haven't already:
  psql $POSTGRES_URL -f src/ragstack_core/stores/schema.sql
"""
import os

from ragstack_core.embedders import create_embedder, EmbeddingProvider
from ragstack_core.stores import create_store, VectorStoreProvider
from ragstack_core.models.document_chunk import DocumentChunk

CHUNKS = [
    DocumentChunk(
        document_id="demo-doc",
        chunk_index=0,
        text="The James Webb Space Telescope captures infrared images of distant galaxies.",
    ),
    DocumentChunk(
        document_id="demo-doc",
        chunk_index=1,
        text="Sourdough bread requires a live starter culture of wild yeast and bacteria.",
    ),
    DocumentChunk(
        document_id="demo-doc",
        chunk_index=2,
        text="Napoleon Bonaparte was exiled to the island of Saint Helena in 1815.",
    ),
    DocumentChunk(
        document_id="demo-doc",
        chunk_index=3,
        text="Statins are commonly prescribed to lower LDL cholesterol in patients at cardiac risk.",
    ),
    DocumentChunk(
        document_id="demo-doc",
        chunk_index=4,
        text="The offside rule in football prevents attackers from gaining an unfair positional advantage.",
    ),
]


def _separator(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print("─" * 60)


if __name__ == "__main__":
    postgres_url = os.environ["POSTGRES_URL"]

    print("Creating embedder and store...")
    embedder = create_embedder(EmbeddingProvider.OPENAI, model_name="text-embedding-3-large")
    store = create_store(VectorStoreProvider.PGVECTOR, connection_string=postgres_url)

    _separator("Upserting 5 chunks")
    store.upsert(CHUNKS, embedder)
    print(f"  Upserted {len(CHUNKS)} chunks successfully.")

    _separator("store.search() — top 3 results (no scores)")
    query = "astronomy and space exploration"
    results = store.search(query, embedder, top_k=3)
    print(f"  Query: {query!r}")
    for i, chunk in enumerate(results):
        print(f"  [{i}] {chunk.text}")

    _separator("store.search_with_scores() — top 3 with cosine similarity")
    print("  Score: 1.0 = identical, 0.0 = unrelated")
    query2 = "cooking and food preparation"
    results_scored = store.search_with_scores(query2, embedder, top_k=3)
    print(f"  Query: {query2!r}")
    for i, (chunk, score) in enumerate(results_scored):
        print(f"  [{i}] score={score:.4f}  {chunk.text}")
