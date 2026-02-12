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
