"""Helix exception hierarchy and reusable next-action constants.

All domain errors derive from ``HelixError`` and carry structured
error codes plus actionable recovery hints.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorCodeInfo:
    code: str
    message: str
    next_action: str | None = None


class HelixError(Exception):
    """Base error for Helix operations."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "HELIX_E_UNKNOWN",
        next_action: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.next_action = next_action

    def as_info(self) -> ErrorCodeInfo:
        return ErrorCodeInfo(
            code=self.code,
            message=str(self),
            next_action=self.next_action,
        )


class SeedFormatError(HelixError):
    """Raised when HLX1 seed structure or integrity checks fail."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "HELIX_E_SEED_FORMAT",
        next_action: str | None = None,
    ) -> None:
        super().__init__(message, code=code, next_action=next_action)


class DecodeError(HelixError):
    """Raised when reconstruction cannot proceed."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "HELIX_E_DECODE",
        next_action: str | None = None,
    ) -> None:
        super().__init__(message, code=code, next_action=next_action)


class ExternalToolError(HelixError):
    """Raised when external tools (e.g., ipfs) are unavailable or fail."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "HELIX_E_EXTERNAL_TOOL",
        next_action: str | None = None,
    ) -> None:
        super().__init__(message, code=code, next_action=next_action)


# -- next_action templates -----------------------------------------
ACTION_VERIFY_SEED = (
    "Verify seed file integrity or regenerate"
    " with `helix encode`."
)
ACTION_REGENERATE_SEED = (
    "Regenerate the seed file with `helix encode`."
)
ACTION_REFETCH_SEED = (
    "Re-download or re-transfer the seed file."
)
ACTION_UPGRADE_HELIX = (
    "Upgrade Helix to the latest version."
)
ACTION_VERIFY_ENCRYPTION = (
    "Verify encryption key/password is correct."
)
ACTION_PROVIDE_ENCRYPTION_KEY = (
    "Provide --encryption-key"
    " or set HELIX_ENCRYPTION_KEY."
)
ACTION_INSTALL_ZSTD = (
    "Run `uv sync --extra zstd`"
    " to install zstandard."
)
ACTION_CHECK_OPTIONS = (
    "Check command-line options and retry."
)
ACTION_REPORT_BUG = (
    "This is likely a bug. Please report it."
)
ACTION_CHECK_GENOME = (
    "Check genome database,"
    " or run `helix prime` to rebuild."
)
ACTION_VERIFY_SNAPSHOT = (
    "Verify the snapshot file or regenerate"
    " with `helix genome-snapshot`."
)
ACTION_VERIFY_GENES_PACK = (
    "Verify the genes pack file or regenerate"
    " with `helix export-genes`."
)
ACTION_CHECK_DISK = (
    "Check directory permissions"
    " and available disk space."
)
ACTION_ENABLE_LEARN_OR_PORTABLE = (
    "Enable --learn or --portable"
    " for unknown chunks."
)
