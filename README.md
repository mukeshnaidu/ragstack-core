# RAGSTACK

**Enterprise-grade Python RAG (Retrieval-Augmented Generation) toolkit.**

RAGSTACK is a composable, open-source SDK for building document ingestion pipelines. It handles everything between a raw file and a vector database: loading, cleaning, chunking, embedding, and storing — each stage independently usable and swappable.

> Built for engineers who want production-level RAG infrastructure without vendor lock-in.

---

## What Problem Does It Solve?

When building AI applications that answer questions from documents (contracts, reports, manuals, etc.), you need a reliable pipeline to:

1. Extract text from files (PDF, DOCX, CSV, etc.)
2. Clean that text (strip noise, fix encoding, redact PII)
3. Split it into chunks a model can process
4. Convert chunks to vector embeddings
5. Store and search those embeddings

Most tutorials wire this up with ad-hoc code. RAGSTACK gives you production-grade, tested building blocks for each stage — composable, type-safe, and pluggable.

---

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐     ┌──────────────┐     ┌──────────────┐
│   LOADERS   │ --> │   CLEANERS   │ --> │   CHUNKERS    │ --> │  EMBEDDERS   │ --> │    STORES    │
│             │     │              │     │               │     │              │     │              │
│ PDF / DOCX  │     │ Strip HTML   │     │ Fixed-size    │     │ OpenAI API   │     │ pgvector     │
│ TXT / CSV   │     │ Fix encoding │     │ token-based   │     │ Local model  │     │ Qdrant       │
│ Excel / MD  │     │ Remove PII   │     │ with overlap  │     │ (HuggingFace)│     │ Chroma       │
└─────────────┘     └──────────────┘     └───────────────┘     └──────────────┘     └──────────────┘
      │                    │                     │                    │                    │
DocumentInfo          DocumentBlock         DocumentChunk        float vectors       SearchResult
+ DocumentBlock       (cleaned)             (with metadata)      (1536 or 384d)      (with scores)
```

Every stage operates on well-defined Pydantic models. You can use the full pipeline or drop in at any stage.

---

## Folder Structure

```
ragstack1/
│
├── src/
│   └── ragstack_core/           # The core SDK package
│       │
│       ├── models/              # Shared data shapes (Pydantic)
│       │   ├── document_info.py     # File metadata: id, name, type, size, timestamps
│       │   ├── document_block.py    # Raw extracted text block from a loader
│       │   ├── document_chunk.py    # A chunk ready for embedding (has chunk_id, token_count)
│       │   ├── embedding_record.py  # A chunk paired with its vector
│       │   └── search_result.py     # A search hit with similarity score
│       │
│       ├── loaders/             # File → DocumentInfo + DocumentBlocks
│       │   ├── base_loader.py       # Abstract base class (load_info, load_blocks)
│       │   ├── text_loader.py       # .txt files, N lines per block
│       │   ├── pdf_loader.py        # .pdf via pypdf, N pages per block
│       │   ├── csv_loader.py        # .csv rows serialised as "key: value | ..."
│       │   ├── excel_loader.py      # .xlsx multi-sheet via openpyxl
│       │   └── markdown_loader.py   # .md split by heading sections
│       │
│       ├── cleaners/            # Text normalisation pipeline
│       │   ├── pipeline.py          # TextCleaningPipeline — ordered list of steps
│       │   ├── base_cleaner.py      # CleanerStep Protocol + CleanContext + CleaningResult
│       │   └── steps/               # One file per cleaning concern
│       │       ├── whitespace_normalizer.py
│       │       ├── unicode_normalizer.py
│       │       ├── html_tag_stripper.py
│       │       ├── pdf_artifact_cleaner.py
│       │       ├── markdown_cleaner.py
│       │       ├── encoding_fixer.py
│       │       ├── control_char_cleaner.py
│       │       ├── typography_cleaner.py
│       │       ├── ligature_expander.py
│       │       └── pii_redactor.py
│       │
│       ├── chunkers/            # DocumentBlock → DocumentChunks
│       │   ├── base_chunker.py      # Abstract base class
│       │   └── fixed_size_chunker.py # Token-based chunking with overlap (tiktoken)
│       │
│       ├── embedders/           # Text → float vectors
│       │   ├── base_embedder.py     # EmbedderProtocol definition
│       │   ├── factory.py           # create_embedder() — the public entry point
│       │   ├── openai_embedder.py   # OpenAI text-embedding-3-small (1536d)
│       │   └── local_embedder.py    # HuggingFace all-MiniLM-L6-v2 (384d), no API key
│       │
│       ├── stores/              # Vector storage + similarity search
│       │   ├── base_store.py        # VectorStoreProtocol definition
│       │   ├── factory.py           # create_store() — the public entry point
│       │   ├── pgvector_store.py    # PostgreSQL + pgvector (production)
│       │   ├── qdrant_store.py      # Qdrant (supports :memory: for dev)
│       │   ├── chroma_store.py      # ChromaDB (supports :memory: for dev)
│       │   └── schema.sql           # Run once to set up pgvector table
│       │
│       └── exceptions.py        # EmbeddingError, StorageError, MissingDependencyError
│
├── src/tests/                   # Pytest test suite (mirrors src/ragstack_core/)
├── examples/                    # Runnable examples for every module
│   ├── loaders.py
│   ├── cleaning.py
│   ├── chunking.py
│   ├── embedding.py
│   ├── vector_store.py
│   └── full_pipeline.py         # End-to-end demo
│
├── main.py                      # Placeholder entry point
├── pyproject.toml               # Package definition + optional dependencies
└── uv.lock                      # Locked dependency versions
```

### Why this structure?

Each folder is a **stage in the pipeline** and a **separate concern**. You can:
- Use only the loaders (extract text from files, nothing else)
- Use loaders + cleaners (extract and normalise)
- Skip straight to chunking if you already have text

Nothing in `loaders/` depends on `stores/`. Nothing in `cleaners/` knows about embeddings. This separation lets you swap any stage without touching the others — the definition of clean architecture.

---

## Integrated Packages

| Package | Purpose | When it's needed |
|---|---|---|
| `pydantic` | Data validation and type-safe models | Always (core models) |
| `pypdf` | PDF text extraction | Loading `.pdf` files |
| `openpyxl` | Excel file reading | Loading `.xlsx` files |
| `tiktoken` | Token counting (OpenAI's tokeniser) | All chunking |
| `ftfy` | Fix broken Unicode / encoding errors | Text cleaning |
| `openai` | Embedding API calls | `EmbeddingProvider.OPENAI` |
| `sentence-transformers` | Local HuggingFace embeddings | `EmbeddingProvider.LOCAL` |
| `psycopg[pool]` + `pgvector` | PostgreSQL vector storage | `VectorStoreProvider.PGVECTOR` |
| `qdrant-client` | Qdrant vector storage | `VectorStoreProvider.QDRANT` |
| `chromadb` | ChromaDB vector storage | `VectorStoreProvider.CHROMA` |
| `pytest` + `pytest-asyncio` | Testing | Development only |

**Core packages** (`pydantic`, `pypdf`, `openpyxl`, `tiktoken`, `ftfy`) are always installed.
**Optional packages** are installed only when you need them — see Installation below.

---

## Installation

### Prerequisites

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`

### Step 1 — Clone the repo

```bash
git clone https://github.com/your-org/ragstack.git
cd ragstack
```

### Step 2 — Install with uv (recommended)

```bash
# Core only (loaders, cleaners, chunkers)
uv sync

# Add OpenAI embeddings
uv add 'ragstack[openai]'

# Add local/offline embeddings (HuggingFace)
uv add 'ragstack[local]'

# Add a vector store
uv add 'ragstack[pgvector]'   # PostgreSQL
uv add 'ragstack[qdrant]'     # Qdrant
uv add 'ragstack[chroma]'     # ChromaDB

# Install everything
uv add 'ragstack[all]'
```

### Step 3 — Set environment variables

```bash
# Only needed if using OpenAI embeddings
export OPENAI_API_KEY="sk-..."

# Only needed if using pgvector
export TEST_POSTGRES_URL="postgresql://user:pass@localhost:5432/ragstack"
```

### Step 4 — (pgvector only) Run the schema

```bash
psql $TEST_POSTGRES_URL -f src/ragstack_core/stores/schema.sql
```

### Step 5 — Verify

```bash
uv run pytest src/tests/
```

---

## Quick Start — Full Pipeline

```python
from ragstack_core.loaders import PdfLoader
from ragstack_core.cleaners.pipeline import TextCleaningPipeline
from ragstack_core.chunkers.fixed_size_chunker import FixedSizeChunker, ModelType
from ragstack_core.embedders import create_embedder, EmbeddingProvider
from ragstack_core.stores import create_store, VectorStoreProvider

# 1. Load
loader = PdfLoader(pages_per_block=1)
info = loader.load_info("report.pdf")
blocks = list(loader.load_blocks("report.pdf", info))

# 2. Clean
pipeline = TextCleaningPipeline.for_pdf()
clean_blocks = pipeline.clean_blocks(blocks)

# 3. Chunk
chunker = FixedSizeChunker(ModelType.OPENAI_EMBEDDING)  # 512 tokens, 50 overlap
chunks = [chunk for block in clean_blocks for chunk in chunker.chunk_block(block)]

# 4. Embed
embedder = create_embedder(EmbeddingProvider.OPENAI)  # reads OPENAI_API_KEY

# 5. Store
store = create_store(VectorStoreProvider.CHROMA, connection_string=":memory:")
store.upsert(chunks, embedder)

# 6. Search
results = store.search_with_scores("What are the key findings?", embedder, top_k=5)
for chunk, score in results:
    print(f"[{score:.3f}] {chunk.text[:200]}")

# 7. Clean up
store.delete_by_document_id(info.document_id)
```

---

## Using Each Module Independently

### Loaders

```python
from ragstack_core.loaders import TextLoader, PdfLoader, CsvLoader, MarkdownLoader
from ragstack_core.loaders.excel_loader import ExcelLoader

loader = TextLoader(lines_per_block=50)
info = loader.load_info("notes.txt")
for block in loader.load_blocks("notes.txt", info):
    print(block.block_index, block.text[:80])
```

### Cleaners

```python
from ragstack_core.cleaners.pipeline import TextCleaningPipeline

# Preset pipelines — pick the right one for your file type
pipeline = TextCleaningPipeline.default()       # general purpose
pipeline = TextCleaningPipeline.for_pdf()       # removes headers/footers, ligatures
pipeline = TextCleaningPipeline.for_markdown()  # strips MD syntax
pipeline = TextCleaningPipeline.for_tabular()   # CSV/Excel normalisation
pipeline = TextCleaningPipeline.with_pii_redaction(TextCleaningPipeline.default())

cleaned_block = pipeline.clean_block(block)
```

### Chunkers

```python
from ragstack_core.chunkers.fixed_size_chunker import FixedSizeChunker, ModelType

chunker = FixedSizeChunker(ModelType.CLAUDE)           # 1024 tokens, 100 overlap
chunker = FixedSizeChunker(ModelType.OPENAI_EMBEDDING) # 512 tokens, 50 overlap
chunker = FixedSizeChunker(chunk_size=300, overlap=30) # manual

for chunk in chunker.chunk_block(block):
    print(chunk.chunk_id, chunk.metadata["token_count"])
```

### Embedders

```python
from ragstack_core.embedders import create_embedder, EmbeddingProvider

# Cloud — requires OPENAI_API_KEY
embedder = create_embedder(EmbeddingProvider.OPENAI)

# Local — no API key, uses HuggingFace (runs on CPU or CUDA)
embedder = create_embedder(EmbeddingProvider.LOCAL, device="cpu")

vectors = embedder.embed(["sentence one", "sentence two"])  # list[list[float]]
print(embedder.model_name, embedder.dimensions)
```

### Vector Stores

```python
from ragstack_core.stores import create_store, VectorStoreProvider

# In-memory (dev/testing)
store = create_store(VectorStoreProvider.CHROMA, connection_string=":memory:")
store = create_store(VectorStoreProvider.QDRANT, connection_string=":memory:")

# Production
store = create_store(VectorStoreProvider.PGVECTOR, connection_string="postgresql://...")

store.upsert(chunks, embedder)
results = store.search("query text", embedder, top_k=5)
store.delete_by_document_id("doc-id")
```

---

## Running the Examples

```bash
uv run python examples/loaders.py
uv run python examples/cleaning.py
uv run python examples/chunking.py
uv run python examples/full_pipeline.py
```

---

## Running Tests

```bash
uv run pytest src/tests/                          # all tests
uv run pytest src/tests/test_loader.py            # one file
uv run pytest src/tests/test_loader.py::test_name # one test
```

pgvector integration tests require `TEST_POSTGRES_URL` env var. Without it they are automatically skipped.

---

## Key Design Decisions

**Content-hash IDs.** `document_id` is derived from `source_path:file_size:mtime`. Re-indexing the same file produces the same ID, making upserts idempotent. `chunk_id` is derived from `document_id:chunk_index:text_hash`.

**Protocol-based extensibility.** `EmbedderProtocol` and `VectorStoreProtocol` are structural protocols. You can add a new embedder or store by implementing the protocol — no base class inheritance needed.

**Optional dependencies.** The core package is lightweight. Each optional integration (`openai`, `pgvector`, etc.) is a separate install group so you never pull in libraries you don't use.

**Factory functions as the public API.** Users call `create_embedder()` and `create_store()`, never the concrete classes. This hides implementation details and lets the internals change without breaking calling code.

---

## Planned App Layer

```
app/
  routes/       # Thin FastAPI handlers — no business logic
  services/     # Orchestration and business logic
  repositories/ # Database/storage access
  models/       # Pydantic request/response schemas
  config/       # Environment-based configuration
```

The app layer (FastAPI, REST API, MCP server) is not yet implemented. `ragstack_core` is intentionally decoupled from it.

---

## License

MIT
