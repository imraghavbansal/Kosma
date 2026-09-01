class KosmaError(Exception):
    """Base class for all Kosma SDK errors."""


class KosmaConfigError(KosmaError):
    """Raised when the SDK is missing required configuration (API key/URL)."""


class KosmaIngestError(KosmaError):
    """Raised when the ingestion API rejects or fails to accept a trace."""
