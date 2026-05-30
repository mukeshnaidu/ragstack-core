CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id    TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    chunk_index INT  NOT NULL,
    text        TEXT NOT NULL,
    metadata    JSONB DEFAULT '{}',
    collection  TEXT NOT NULL DEFAULT 'ragstack',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (document_id, chunk_index, collection)
);

CREATE INDEX IF NOT EXISTS chunks_metadata_idx ON chunks USING gin (metadata);
CREATE INDEX IF NOT EXISTS chunks_collection_idx ON chunks (collection);
CREATE INDEX IF NOT EXISTS chunks_document_id_idx ON chunks (document_id, collection);

CREATE TABLE IF NOT EXISTS embeddings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id    TEXT NOT NULL REFERENCES chunks(chunk_id) ON DELETE CASCADE,
    model_name  TEXT NOT NULL,
    dimensions  INT  NOT NULL,
    vector      VECTOR NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (chunk_id, model_name)
);

CREATE INDEX IF NOT EXISTS embeddings_vector_idx
    ON embeddings USING hnsw (vector vector_cosine_ops);
