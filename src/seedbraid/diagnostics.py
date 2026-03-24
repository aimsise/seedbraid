"""Environment and dependency diagnostics for ``seedbraid doctor``.

Checks Python version, kubo API reachability, genome path
writability, and compression library status.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .errors import ExternalToolError, SeedbraidError
from .storage import resolve_genome_db_path


@dataclass(frozen=True)
class DoctorCheck:
    check: str
    status: str
    detail: str
    next_action: str | None = None


@dataclass(frozen=True)
class DoctorReport:
    checks: list[DoctorCheck]

    @property
    def ok_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "ok")

    @property
    def warn_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "warn")

    @property
    def fail_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "fail")

    @property
    def ok(self) -> bool:
        return self.fail_count == 0


def _check_python_version() -> DoctorCheck:
    major = sys.version_info.major
    minor = sys.version_info.minor
    detail = f"python={major}.{minor}"
    if (major, minor) >= (3, 12):
        return DoctorCheck(check="python", status="ok", detail=detail)
    return DoctorCheck(
        check="python",
        status="fail",
        detail=f"{detail} (requires >=3.12)",
        next_action=(
            "Install Python 3.12+ and recreate"
            " the project virtual environment."
        ),
    )


def _check_kubo_api() -> DoctorCheck:
    from . import ipfs_http  # deferred: avoid circular import

    version = ipfs_http.daemon_version()
    if version is None:
        return DoctorCheck(
            check="kubo_api",
            status="fail",
            detail=(
                "kubo API not reachable at"
                f" {ipfs_http.api_base_url()}"
            ),
            next_action=(
                "Start kubo daemon (`ipfs daemon`)"
                " and verify API endpoint."
                " Override with SB_KUBO_API env var."
            ),
        )
    return DoctorCheck(
        check="kubo_api",
        status="ok",
        detail=(
            f"kubo {version}"
            f" at {ipfs_http.api_base_url()}"
        ),
    )


def _check_ipfs_path() -> DoctorCheck:
    ipfs_path = os.environ.get("IPFS_PATH")
    if not ipfs_path:
        return DoctorCheck(
            check="ipfs_repo",
            status="warn",
            detail="IPFS_PATH is unset (using default ~/.ipfs)",
            next_action="Set IPFS_PATH for isolated environments when needed.",
        )
    p = Path(ipfs_path)
    if not p.exists():
        return DoctorCheck(
            check="ipfs_repo",
            status="warn",
            detail=f"IPFS_PATH does not exist: {p}",
            next_action=(
                "Run `ipfs init` for this"
                " IPFS_PATH before"
                " publish/fetch operations."
            ),
        )
    if not p.is_dir():
        return DoctorCheck(
            check="ipfs_repo",
            status="fail",
            detail=f"IPFS_PATH is not a directory: {p}",
            next_action="Set IPFS_PATH to a valid writable directory.",
        )
    return DoctorCheck(check="ipfs_repo", status="ok", detail=f"IPFS_PATH={p}")


def _check_genome_path(genome_path: Path) -> DoctorCheck:
    db_path = resolve_genome_db_path(genome_path)
    parent = db_path.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return DoctorCheck(
            check="genome_path",
            status="fail",
            detail=f"cannot create parent directory {parent}: {exc}",
            next_action="Choose a writable --genome path.",
        )

    if not os.access(parent, os.W_OK):
        return DoctorCheck(
            check="genome_path",
            status="fail",
            detail=f"directory is not writable: {parent}",
            next_action=(
                "Adjust directory permissions"
                " or select another"
                " --genome path."
            ),
        )

    try:
        with tempfile.NamedTemporaryFile(
            dir=parent,
            prefix=".seedbraid-doctor-",
            delete=True,
        ):
            pass
    except OSError as exc:
        return DoctorCheck(
            check="genome_path",
            status="fail",
            detail=f"write test failed under {parent}: {exc}",
            next_action="Fix filesystem permissions for genome storage.",
        )

    return DoctorCheck(
        check="genome_path",
        status="ok",
        detail=f"db_path={db_path}",
    )


def _check_compression() -> list[DoctorCheck]:
    checks: list[DoctorCheck] = [
        DoctorCheck(
            check="compression_zlib",
            status="ok",
            detail="zlib available (stdlib)",
        )
    ]
    if importlib.util.find_spec("zstandard") is None:
        checks.append(
            DoctorCheck(
                check="compression_zstd",
                status="warn",
                detail="optional dependency 'zstandard' is not installed",
                next_action=(
                    "Run `uv sync --extra zstd`"
                    " to enable --compression zstd."
                ),
            )
        )
    else:
        checks.append(
            DoctorCheck(
                check="compression_zstd",
                status="ok",
                detail="zstandard available",
            )
        )
    return checks


def run_doctor(genome_path: str | Path) -> DoctorReport:
    """Run environment and dependency diagnostics.

    Checks Python version, kubo API reachability,
    IPFS_PATH configuration, genome path writability,
    and compression library status.

    Args:
        genome_path: Path to the genome directory or
            database file to check for writability.

    Returns:
        Report containing individual check results.

    Raises:
        ExternalToolError: If an unexpected error
            occurs during diagnostics.
    """
    path = Path(genome_path)
    checks: list[DoctorCheck] = []
    try:
        checks.append(_check_python_version())
        checks.append(_check_kubo_api())
        checks.append(_check_ipfs_path())
        checks.append(_check_genome_path(path))
        checks.extend(_check_compression())
    except SeedbraidError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ExternalToolError(
            f"doctor failed unexpectedly: {exc}",
            code="SB_E_DOCTOR_CHECK",
            next_action=(
                "Re-run `seedbraid doctor --genome <path>`"
                " and inspect environment setup."
            ),
        ) from exc
    return DoctorReport(checks=checks)
