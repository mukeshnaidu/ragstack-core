"""
chunking.py — Demonstrates FixedSizeChunker with three configurations.

Uses sample.txt as input corpus — one large block to show how chunk_size affects output.
No API keys needed.
"""
from pathlib import Path

from ragstack_core.chunkers.fixed_size_chunker import FixedSizeChunker, ModelType
from ragstack_core.cleaners.pipeline import TextCleaningPipeline
from ragstack_core.loaders import TextLoader
from ragstack_core.models.document_block import DocumentBlock

SAMPLE_TXT = Path(__file__).parent / "sample_data" / "sample.txt"
MAX_BLOCKS = 5


def load_sample_blocks() -> list[DocumentBlock]:
    loader = TextLoader(lines_per_block=50)
    info = loader.load_info(SAMPLE_TXT)
    pipeline = TextCleaningPipeline.default()
    blocks: list[DocumentBlock] = []
    for i, block in enumerate(loader.load_blocks(SAMPLE_TXT, info)):
        if i >= MAX_BLOCKS:
            break
        blocks.append(pipeline.clean_block(block))
    return blocks


def demo_chunker(
    label: str, chunker: FixedSizeChunker, blocks: list[DocumentBlock]
) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print(f"  chunk_size={chunker.chunk_size}, overlap={chunker.overlap}")
    print("─" * 60)

    all_chunks = []
    for block in blocks:
        all_chunks.extend(chunker.chunk_block(block))

    print(f"  Total chunks from {len(blocks)} blocks: {len(all_chunks)}")

    first = all_chunks[0]
    print("\n  First chunk:")
    print(f"    chunk_index : {first.chunk_index}")
    print(f"    token_count : {first.metadata['token_count']}")
    print(f"    char_count  : {first.metadata['char_count']}")
    print(f"    model_type  : {first.metadata['model_type']}")
    print(f"    overlap     : {first.metadata['overlap']}")
    print(f"    text preview: {first.text[:100]!r}")


if __name__ == "__main__":
    print("Loading and cleaning blocks from sample.txt...")
    blocks = load_sample_blocks()
    total_chars = sum(len(b.text) for b in blocks)
    print(f"Loaded {len(blocks)} block(s) (~{total_chars} chars).\n")

    demo_chunker(
        "ModelType.CLAUDE — 1024 tokens, 100 overlap",
        FixedSizeChunker(ModelType.CLAUDE),
        blocks,
    )
    demo_chunker(
        "ModelType.OPENAI_EMBEDDING — 512 tokens, 50 overlap",
        FixedSizeChunker(ModelType.OPENAI_EMBEDDING),
        blocks,
    )
    demo_chunker(
        "Custom — 300 tokens, 30 overlap",
        FixedSizeChunker(chunk_size=300, overlap=30),
        blocks,
    )
