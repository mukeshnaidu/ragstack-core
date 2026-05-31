"""
full_pipeline.py — End-to-end ragstack pipeline on sample.txt.

Stages:
  [1/5] Load    → TextLoader (first MAX_BLOCKS blocks)
  [2/5] Clean   → TextCleaningPipeline.default()
  [3/5] Chunk   → FixedSizeChunker(ModelType.OPENAI_EMBEDDING)
  [4/5] Embed & Store → OpenAI text-embedding-3-large + pgvector
  [5/5] Search  → search_with_scores()

Requires: OPENAI_API_KEY and POSTGRES_URL environment variables
Install : uv add 'ragstack[openai]' 'ragstack[pgvector]'

Run the schema first if you haven't already:
  psql $POSTGRES_URL -f src/ragstack_core/stores/schema.sql
"""
import os
from pathlib import Path

from ragstack_core.chunkers.fixed_size_chunker import FixedSizeChunker, ModelType
from ragstack_core.cleaners.pipeline import TextCleaningPipeline
from ragstack_core.embedders import EmbeddingProvider, create_embedder
from ragstack_core.loaders import TextLoader
from ragstack_core.stores import VectorStoreProvider, create_store

SAMPLE_TXT = Path(__file__).parent / "sample_data" / "sample.txt"
MAX_BLOCKS = 10  # limit blocks to keep API cost low during development

QUERIES = [
    "What were the difficult times like?",
    "How did the revolution begin?",
    "What does liberty mean to people?",
]


def main() -> None:
    postgres_url = os.environ["POSTGRES_URL"]

    # ── [1/5] Load ────────────────────────────────────────────────────
    print("[1/5] Loading...")
    loader = TextLoader(lines_per_block=3)
    info = loader.load_info(SAMPLE_TXT)
    raw_blocks = []
    for i, block in enumerate(loader.load_blocks(SAMPLE_TXT, info)):
        if i >= MAX_BLOCKS:
            break
        raw_blocks.append(block)
    print(f"      Loaded {len(raw_blocks)} blocks from '{info.file_name}'")

    # ── [2/5] Clean ───────────────────────────────────────────────────
    print("[2/5] Cleaning...")
    pipeline = TextCleaningPipeline.default()
    clean_blocks = [pipeline.clean_block(b) for b in raw_blocks]
    print(f"      Cleaned {len(clean_blocks)} blocks")

    # ── [3/5] Chunk ───────────────────────────────────────────────────
    print("[3/5] Chunking...")
    chunker = FixedSizeChunker(ModelType.OPENAI_EMBEDDING)
    chunks = []
    for block in clean_blocks:
        chunks.extend(chunker.chunk_block(block))
    print(f"      Produced {len(chunks)} chunks (512 tokens, 50 overlap)")

    # ── [4/5] Embed & Store ───────────────────────────────────────────
    print("[4/5] Embedding and storing...")
    embedder = create_embedder(
        EmbeddingProvider.OPENAI, model_name="text-embedding-3-large"
    )
    store = create_store(VectorStoreProvider.PGVECTOR, connection_string=postgres_url)
    store.upsert(chunks, embedder)
    print(f"      Stored {len(chunks)} chunks (model: {embedder.model_name})")

    # ── [5/5] Search ──────────────────────────────────────────────────
    print("[5/5] Searching...\n")
    for query in QUERIES:
        print(f"  Query: {query!r}")
        results = store.search_with_scores(query, embedder, top_k=3)
        for rank, (chunk, score) in enumerate(results):
            print(f"  [{rank}] score={score:.4f}  {chunk.text[:120]!r}")
        print()


if __name__ == "__main__":
    main()
