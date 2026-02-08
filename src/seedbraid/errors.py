class HelixError(Exception):
    """Base error for Helix operations."""


class SeedFormatError(HelixError):
    """Raised when HLX1 seed structure or integrity checks fail."""


class DecodeError(HelixError):
    """Raised when reconstruction cannot proceed."""


class ExternalToolError(HelixError):
    """Raised when external tools (e.g., ipfs) are unavailable or fail."""
