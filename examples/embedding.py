"""
embedding.py — Demonstrates the OpenAI embedder with text-embedding-3-large.

Requires: OPENAI_API_KEY environment variable
Install : uv add 'ragstack[openai]'
"""
from ragstack_core.embedders import create_embedder, EmbeddingProvider

SAMPLE_TEXTS = [
    "The Battle of Borodino was one of the deadliest battles of the Napoleonic Wars.",
    "Machine learning models learn patterns from large datasets.",
    "Paris is the capital of France and is known for the Eiffel Tower.",
]


if __name__ == "__main__":
    print("Creating OpenAI embedder (text-embedding-3-large)...")
    embedder = create_embedder(
        EmbeddingProvider.OPENAI,
        model_name="text-embedding-3-large",
    )

    print(f"  model_name : {embedder.model_name}")
    print(f"  dimensions : {embedder.dimensions}")

    print("\nEmbedding 3 sample texts...")
    vectors = embedder.embed(SAMPLE_TEXTS)

    for i, (text, vector) in enumerate(zip(SAMPLE_TEXTS, vectors)):
        print(f"\n  [{i}] text      : {text!r}")
        print(f"       vector[:5] : {[round(v, 6) for v in vector[:5]]}")
        print(f"       len(vector): {len(vector)}")
