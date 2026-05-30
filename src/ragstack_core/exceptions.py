class EmbeddingError(Exception):
    """Raised when an embedding provider call fails."""


class StorageError(Exception):
    """Raised when a vector store operation fails."""


class MissingDependencyError(ImportError):
    """Raised when an optional dependency is not installed."""
