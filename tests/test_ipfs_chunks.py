"""Unit tests for IPFSChunkStorage (monkeypatch, no IPFS daemon)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import pytest

from seedbraid.cid import sha256_to_cidv1_raw
from seedbraid.errors import ExternalToolError
from seedbraid.ipfs_chunks import (
    IPFSChunkStorage,
    fetch_chunk,
    publish_chunk,
)


@dataclass
class _Proc:
    returncode: int
    stdout: bytes | str
    stderr: bytes | str


_CHUNK_DATA = b"hello ipfs chunk"
_CHUNK_HASH = hashlib.sha256(_CHUNK_DATA).digest()
_CHUNK_CID = sha256_to_cidv1_raw(_CHUNK_DATA)


def _patch_ipfs(monkeypatch):  # noqa: ANN001, ANN202
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.shutil.which",
        lambda _: "/usr/bin/ipfs",
    )


# -- has_chunk -----------------------------------------------


def test_has_chunk_returns_true_on_stat_success(
    monkeypatch,
) -> None:
    _patch_ipfs(monkeypatch)
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.subprocess.run",
        lambda *a, **kw: _Proc(
            returncode=0,
            stdout=b"Key: ... Size: 16\n",
            stderr=b"",
        ),
    )
    storage = IPFSChunkStorage()
    assert storage.has_chunk(_CHUNK_HASH) is True


def test_has_chunk_returns_false_on_stat_failure(
    monkeypatch,
) -> None:
    _patch_ipfs(monkeypatch)
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.subprocess.run",
        lambda *a, **kw: _Proc(
            returncode=1,
            stdout=b"",
            stderr=b"block not found",
        ),
    )
    storage = IPFSChunkStorage()
    assert storage.has_chunk(_CHUNK_HASH) is False


# -- get_chunk -----------------------------------------------


def test_get_chunk_returns_data_on_success(
    monkeypatch,
) -> None:
    _patch_ipfs(monkeypatch)
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.subprocess.run",
        lambda *a, **kw: _Proc(
            returncode=0,
            stdout=_CHUNK_DATA,
            stderr=b"",
        ),
    )
    storage = IPFSChunkStorage()
    result = storage.get_chunk(_CHUNK_HASH)
    assert result == _CHUNK_DATA


def test_get_chunk_returns_none_on_failure(
    monkeypatch,
) -> None:
    _patch_ipfs(monkeypatch)
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.subprocess.run",
        lambda *a, **kw: _Proc(
            returncode=1,
            stdout=b"",
            stderr=b"offline",
        ),
    )
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.time.sleep",
        lambda _: None,
    )
    storage = IPFSChunkStorage(retries=2)
    assert storage.get_chunk(_CHUNK_HASH) is None


def test_get_chunk_retries_with_backoff(
    monkeypatch,
) -> None:
    calls: list[list[str]] = []
    sleeps: list[float] = []

    def _fake_run(cmd, **kw):  # noqa: ANN001, ANN003, ANN202
        calls.append(cmd)
        if len(calls) < 3:
            return _Proc(
                returncode=1,
                stdout=b"",
                stderr=b"timeout",
            )
        return _Proc(
            returncode=0,
            stdout=_CHUNK_DATA,
            stderr=b"",
        )

    _patch_ipfs(monkeypatch)
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.subprocess.run",
        _fake_run,
    )
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.time.sleep",
        lambda s: sleeps.append(s),
    )

    storage = IPFSChunkStorage(
        retries=3, backoff_ms=100,
    )
    result = storage.get_chunk(_CHUNK_HASH)
    assert result == _CHUNK_DATA
    assert len(sleeps) == 2
    assert sleeps[0] == pytest.approx(0.1)
    assert sleeps[1] == pytest.approx(0.2)


def test_get_chunk_gateway_fallback(
    monkeypatch,
) -> None:
    urls: list[str] = []

    class _Resp:
        def __init__(self, data: bytes) -> None:
            self._data = data

        def __enter__(self):  # noqa: ANN204
            return self

        def __exit__(self, *a):  # noqa: ANN001, ANN201
            return False

        def read(self) -> bytes:
            return self._data

    def _fake_urlopen(url, timeout=30):  # noqa: ANN001, ANN202
        urls.append(url)
        return _Resp(_CHUNK_DATA)

    _patch_ipfs(monkeypatch)
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.subprocess.run",
        lambda *a, **kw: _Proc(
            returncode=1,
            stdout=b"",
            stderr=b"offline",
        ),
    )
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.urllib.request.urlopen",
        _fake_urlopen,
    )
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.time.sleep",
        lambda _: None,
    )

    storage = IPFSChunkStorage(
        gateway="https://gw.example/ipfs",
        retries=1,
    )
    result = storage.get_chunk(_CHUNK_HASH)
    assert result == _CHUNK_DATA
    expected_url = (
        f"https://gw.example/ipfs/{_CHUNK_CID}"
    )
    assert urls == [expected_url]


# -- put_chunk -----------------------------------------------


def test_put_chunk_success_with_cid_verification(
    monkeypatch,
) -> None:
    _patch_ipfs(monkeypatch)
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.subprocess.run",
        lambda *a, **kw: _Proc(
            returncode=0,
            stdout=_CHUNK_CID.encode() + b"\n",
            stderr=b"",
        ),
    )
    storage = IPFSChunkStorage()
    result = storage.put_chunk(
        _CHUNK_HASH, _CHUNK_DATA,
    )
    assert result is True
    assert storage.count_chunks() == 1


def test_put_chunk_cid_mismatch_raises(
    monkeypatch,
) -> None:
    _patch_ipfs(monkeypatch)
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.subprocess.run",
        lambda *a, **kw: _Proc(
            returncode=0,
            stdout=b"bafkreiwrong\n",
            stderr=b"",
        ),
    )
    storage = IPFSChunkStorage()
    with pytest.raises(
        ExternalToolError,
        match="CID mismatch",
    ) as exc_info:
        storage.put_chunk(_CHUNK_HASH, _CHUNK_DATA)
    assert exc_info.value.code == (
        "SB_E_IPFS_CHUNK_PUT"
    )


def test_put_chunk_retries_on_failure(
    monkeypatch,
) -> None:
    calls: list[list[str]] = []

    def _fake_run(cmd, **kw):  # noqa: ANN001, ANN003, ANN202
        calls.append(cmd)
        if len(calls) == 1:
            return _Proc(
                returncode=1,
                stdout=b"",
                stderr=b"daemon offline",
            )
        return _Proc(
            returncode=0,
            stdout=_CHUNK_CID.encode() + b"\n",
            stderr=b"",
        )

    _patch_ipfs(monkeypatch)
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.subprocess.run",
        _fake_run,
    )
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.time.sleep",
        lambda _: None,
    )

    storage = IPFSChunkStorage(retries=2)
    assert storage.put_chunk(
        _CHUNK_HASH, _CHUNK_DATA,
    ) is True
    assert len(calls) == 2


def test_put_chunk_all_retries_exhausted_raises(
    monkeypatch,
) -> None:
    _patch_ipfs(monkeypatch)
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.subprocess.run",
        lambda *a, **kw: _Proc(
            returncode=1,
            stdout=b"",
            stderr=b"daemon offline",
        ),
    )
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.time.sleep",
        lambda _: None,
    )

    storage = IPFSChunkStorage(retries=2)
    with pytest.raises(
        ExternalToolError,
        match="Failed to publish chunk",
    ) as exc_info:
        storage.put_chunk(_CHUNK_HASH, _CHUNK_DATA)
    assert exc_info.value.code == (
        "SB_E_IPFS_CHUNK_PUT"
    )


# -- context manager / count ---------------------------------


def test_context_manager(monkeypatch) -> None:
    _patch_ipfs(monkeypatch)
    with IPFSChunkStorage() as storage:
        assert storage is not None


def test_count_chunks_increments(
    monkeypatch,
) -> None:
    _patch_ipfs(monkeypatch)
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.subprocess.run",
        lambda *a, **kw: _Proc(
            returncode=0,
            stdout=_CHUNK_CID.encode() + b"\n",
            stderr=b"",
        ),
    )
    storage = IPFSChunkStorage()
    assert storage.count_chunks() == 0
    storage.put_chunk(_CHUNK_HASH, _CHUNK_DATA)
    assert storage.count_chunks() == 1
    storage.put_chunk(_CHUNK_HASH, _CHUNK_DATA)
    assert storage.count_chunks() == 2


# -- standalone functions ------------------------------------


def test_publish_chunk_standalone(
    monkeypatch,
) -> None:
    _patch_ipfs(monkeypatch)
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.subprocess.run",
        lambda *a, **kw: _Proc(
            returncode=0,
            stdout=_CHUNK_CID.encode() + b"\n",
            stderr=b"",
        ),
    )
    cid = publish_chunk(_CHUNK_DATA)
    assert cid == _CHUNK_CID


def test_fetch_chunk_standalone_raises_on_unavailable(
    monkeypatch,
) -> None:
    _patch_ipfs(monkeypatch)
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.subprocess.run",
        lambda *a, **kw: _Proc(
            returncode=1,
            stdout=b"",
            stderr=b"not found",
        ),
    )
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.time.sleep",
        lambda _: None,
    )
    with pytest.raises(
        ExternalToolError,
        match="not available",
    ) as exc_info:
        fetch_chunk(_CHUNK_CID)
    assert exc_info.value.code == (
        "SB_E_IPFS_CHUNK_GET"
    )


# -- error: ipfs not found ----------------------------------


def test_ipfs_not_found_raises(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "seedbraid.ipfs_chunks.shutil.which",
        lambda _: None,
    )
    storage = IPFSChunkStorage()
    with pytest.raises(
        ExternalToolError,
        match="ipfs CLI not found",
    ) as exc_info:
        storage.has_chunk(_CHUNK_HASH)
    assert exc_info.value.code == (
        "SB_E_IPFS_NOT_FOUND"
    )
