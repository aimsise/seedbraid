"""Tests for T-035 security audit remediation."""

from __future__ import annotations

import json
import struct
import warnings
from pathlib import Path
from unittest.mock import patch

import pytest

from seedbraid.chunk_manifest import (
    ChunkEntry,
    ChunkManifest,
    read_chunk_manifest,
    write_chunk_manifest,
)
from seedbraid.cid import sha256_to_cidv1_raw
from seedbraid.container import (
    MAX_CHUNK_SIZE,
    decode_raw_payloads,
)
from seedbraid.errors import (
    ExternalToolError,
    SecurityWarning,
    SeedbraidError,
    SeedFormatError,
)
from seedbraid.ipfs_http import (
    _multipart_body,
    _sanitize_filename,
    _timeout,
)
from seedbraid.pinning import PinningServiceAPIProvider

# -- Step 1: Chunk size limit --------------------------------


class TestChunkSizeLimit:
    def test_decode_raw_payloads_rejects_oversized(
        self,
    ) -> None:
        huge = MAX_CHUNK_SIZE + 1
        payload = struct.pack(">I", 1)  # count=1
        payload += struct.pack(">II", 0, huge)
        payload += b"\x00" * huge
        with pytest.raises(
            SeedFormatError, match="exceeds limit"
        ):
            decode_raw_payloads(payload)

    def test_decode_raw_payloads_accepts_within_limit(
        self,
    ) -> None:
        chunk = b"hello"
        payload = struct.pack(">I", 1)
        payload += struct.pack(">II", 0, len(chunk))
        payload += chunk
        result = decode_raw_payloads(payload)
        assert result[0] == chunk

    def test_restore_genome_rejects_oversized(
        self, tmp_path: Path,
    ) -> None:
        from seedbraid.codec import (
            GENOME_SNAPSHOT_MAGIC,
            GENOME_SNAPSHOT_VERSION,
            restore_genome,
        )

        snap = tmp_path / "bad.sgs"
        huge = MAX_CHUNK_SIZE + 1
        header = struct.pack(
            ">4sHQ",
            GENOME_SNAPSHOT_MAGIC,
            GENOME_SNAPSHOT_VERSION,
            1,
        )
        entry_hdr = struct.pack(
            ">32sI", b"\x00" * 32, huge,
        )
        with snap.open("wb") as f:
            f.write(header)
            f.write(entry_hdr)
            f.write(b"\x00" * huge)

        genome = tmp_path / "genome.db"
        with pytest.raises(
            SeedbraidError, match="exceeds limit"
        ):
            restore_genome(
                snap, genome, replace=False,
            )


# -- Step 2: SB_KUBO_TIMEOUT --------------------------------


class TestKuboTimeout:
    def test_valid_timeout(self, monkeypatch) -> None:
        monkeypatch.setenv("SB_KUBO_TIMEOUT", "60")
        assert _timeout() == 60

    def test_default_timeout(self, monkeypatch) -> None:
        monkeypatch.delenv(
            "SB_KUBO_TIMEOUT", raising=False,
        )
        assert _timeout() == 30

    def test_non_integer_raises(
        self, monkeypatch,
    ) -> None:
        monkeypatch.setenv("SB_KUBO_TIMEOUT", "abc")
        with pytest.raises(
            ExternalToolError,
            match="not a valid integer",
        ) as exc_info:
            _timeout()
        assert exc_info.value.code == (
            "SB_E_INVALID_CONFIG"
        )

    def test_zero_raises(self, monkeypatch) -> None:
        monkeypatch.setenv("SB_KUBO_TIMEOUT", "0")
        with pytest.raises(
            ExternalToolError,
            match="positive integer",
        ):
            _timeout()

    def test_negative_raises(
        self, monkeypatch,
    ) -> None:
        monkeypatch.setenv("SB_KUBO_TIMEOUT", "-5")
        with pytest.raises(
            ExternalToolError,
            match="positive integer",
        ):
            _timeout()


# -- Step 3: Filename sanitization ---------------------------


class TestFilenameSanitize:
    def test_clean_filename_unchanged(self) -> None:
        assert _sanitize_filename("seed.sbd") == (
            "seed.sbd"
        )

    def test_strips_quotes(self) -> None:
        assert _sanitize_filename('a"b') == "ab"

    def test_strips_crlf(self) -> None:
        assert _sanitize_filename("a\r\nb") == "ab"

    def test_strips_null(self) -> None:
        assert _sanitize_filename("a\0b") == "ab"

    def test_multipart_body_sanitizes(self) -> None:
        body = _multipart_body(
            "file",
            b"data",
            'evil"\r\nX-Injected: yes',
            "boundary123",
        )
        assert b'filename="evil' in body
        assert b"\r\nX-Injected" not in body


# -- Step 4: PSA CID verification ---------------------------


class TestPsaCidVerification:
    def test_matching_cid_accepted(self) -> None:
        prov = PinningServiceAPIProvider(
            endpoint="http://example.com",
            token="tok",
        )
        raw = json.dumps({
            "status": "pinned",
            "requestid": "req-1",
            "pin": {"cid": "bafy-test"},
        }).encode()
        result = prov._parse_success(
            raw, requested_cid="bafy-test",
        )
        assert result.cid == "bafy-test"

    def test_mismatched_cid_raises(self) -> None:
        prov = PinningServiceAPIProvider(
            endpoint="http://example.com",
            token="tok",
        )
        raw = json.dumps({
            "status": "pinned",
            "pin": {"cid": "bafy-wrong"},
        }).encode()
        with pytest.raises(
            ExternalToolError,
            match="does not match",
        ) as exc_info:
            prov._parse_success(
                raw, requested_cid="bafy-expected",
            )
        assert exc_info.value.code == (
            "SB_E_REMOTE_PIN"
        )

    def test_no_pin_cid_uses_requested(self) -> None:
        prov = PinningServiceAPIProvider(
            endpoint="http://example.com",
            token="tok",
        )
        raw = json.dumps({
            "status": "queued",
        }).encode()
        result = prov._parse_success(
            raw, requested_cid="bafy-req",
        )
        assert result.cid == "bafy-req"


# -- Step 5: SBE1 v2 fallback warning -----------------------


class TestV2FallbackWarning:
    def test_warning_emitted_without_cryptography(
        self,
    ) -> None:
        from seedbraid import container

        with (
            patch.object(
                container, "_HAS_CRYPTOGRAPHY", False,
            ),
            warnings.catch_warnings(record=True) as w,
        ):
            warnings.simplefilter("always")
            result = container.encrypt_seed_bytes(
                b"SBD1" + b"\x00" * 100,
                "password",
            )
            assert len(w) == 1
            assert issubclass(
                w[0].category, SecurityWarning,
            )
            assert "cryptography" in str(w[0].message)
            assert result[:4] == b"SBE1"


# -- Step 7: OP_RAW SHA-256 verification --------------------


class TestOpRawHashVerification:
    def test_raw_payload_hash_mismatch_raises(
        self,
    ) -> None:
        import hashlib

        from seedbraid.codec import _resolve_chunk
        from seedbraid.container import (
            OP_RAW,
            RecipeOp,
        )

        chunk = b"good data"
        digest = hashlib.sha256(chunk).digest()
        bad_chunk = b"tampered data"

        op = RecipeOp(opcode=OP_RAW, hash_index=0)

        class FakeGenome:
            def get_chunk(self, h):  # noqa: ANN001, ANN201
                return None

        with pytest.raises(
            Exception, match="hash mismatch"
        ):
            _resolve_chunk(
                op,
                [digest],
                {0: bad_chunk},
                FakeGenome(),
            )

    def test_raw_payload_valid_passes(self) -> None:
        import hashlib

        from seedbraid.codec import _resolve_chunk
        from seedbraid.container import (
            OP_RAW,
            RecipeOp,
        )

        chunk = b"good data"
        digest = hashlib.sha256(chunk).digest()
        op = RecipeOp(opcode=OP_RAW, hash_index=0)

        class FakeGenome:
            def get_chunk(self, h):  # noqa: ANN001, ANN201
                return None

        result = _resolve_chunk(
            op, [digest], {0: chunk}, FakeGenome(),
        )
        assert result == chunk


# -- Step 8: Manifest hash/CID validation -------------------


class TestManifestFormatValidation:
    def test_invalid_hash_hex_raises(
        self, tmp_path: Path,
    ) -> None:
        p = tmp_path / "bad_hash.json"
        p.write_text(
            json.dumps({
                "format": "SBD1-CHUNKS",
                "version": 1,
                "chunks": [{
                    "hash": "not-a-hex-hash",
                    "cid": "bafkreiaaaa",
                }],
            }),
            encoding="utf-8",
        )
        with pytest.raises(
            SeedbraidError, match="invalid hash"
        ):
            read_chunk_manifest(p)

    def test_short_hash_raises(
        self, tmp_path: Path,
    ) -> None:
        p = tmp_path / "short_hash.json"
        p.write_text(
            json.dumps({
                "format": "SBD1-CHUNKS",
                "version": 1,
                "chunks": [{
                    "hash": "abcd1234",
                    "cid": "bafkreiaaaa",
                }],
            }),
            encoding="utf-8",
        )
        with pytest.raises(
            SeedbraidError, match="invalid hash"
        ):
            read_chunk_manifest(p)

    def test_uppercase_hash_raises(
        self, tmp_path: Path,
    ) -> None:
        p = tmp_path / "upper_hash.json"
        h = "A" * 64
        p.write_text(
            json.dumps({
                "format": "SBD1-CHUNKS",
                "version": 1,
                "chunks": [{
                    "hash": h,
                    "cid": "bafkreiaaaa",
                }],
            }),
            encoding="utf-8",
        )
        with pytest.raises(
            SeedbraidError, match="invalid hash"
        ):
            read_chunk_manifest(p)

    def test_invalid_cid_raises(
        self, tmp_path: Path,
    ) -> None:
        h = "a" * 64
        p = tmp_path / "bad_cid.json"
        p.write_text(
            json.dumps({
                "format": "SBD1-CHUNKS",
                "version": 1,
                "chunks": [{
                    "hash": h,
                    "cid": "not-a-valid-cid",
                }],
            }),
            encoding="utf-8",
        )
        with pytest.raises(
            SeedbraidError, match="invalid CID"
        ):
            read_chunk_manifest(p)

    def test_valid_entry_accepted(
        self, tmp_path: Path,
    ) -> None:
        digest = bytes(32)
        h = digest.hex()
        c = sha256_to_cidv1_raw(
            digest, is_digest=True,
        )
        p = tmp_path / "valid.json"
        m = ChunkManifest(
            seed_sha256="a" * 64,
            chunks=(ChunkEntry(hash_hex=h, cid=c),),
        )
        write_chunk_manifest(m, p)
        loaded = read_chunk_manifest(p)
        assert len(loaded.chunks) == 1


# -- Step 9: scrypt r/p minimum validation ------------------


class TestScryptRpValidation:
    def _make_v2_blob(
        self, *, scrypt_r: int, scrypt_p: int,
    ) -> bytes:
        from seedbraid.container import (
            _V2_HEADER_FMT,
            ENC_MAGIC,
            SCRYPT_N_DEFAULT,
        )

        salt = b"\x00" * 16
        nonce = b"\x00" * 16
        ct = b"\x00" * 64
        mac = b"\x00" * 32
        header = struct.pack(
            _V2_HEADER_FMT,
            ENC_MAGIC,
            2,  # version
            16,  # salt_len
            16,  # nonce_len
            len(ct),  # ciphertext_len
            SCRYPT_N_DEFAULT,
            scrypt_r,
            scrypt_p,
            0,  # flags
        )
        return header + salt + nonce + ct + mac

    def test_r_zero_raises(self) -> None:
        from seedbraid.container import (
            validate_encrypted_seed_envelope,
        )

        blob = self._make_v2_blob(
            scrypt_r=0, scrypt_p=1,
        )
        with pytest.raises(
            SeedFormatError,
            match="downgrade attack",
        ):
            validate_encrypted_seed_envelope(blob)

    def test_p_zero_raises(self) -> None:
        from seedbraid.container import (
            validate_encrypted_seed_envelope,
        )

        blob = self._make_v2_blob(
            scrypt_r=1, scrypt_p=0,
        )
        with pytest.raises(
            SeedFormatError,
            match="downgrade attack",
        ):
            validate_encrypted_seed_envelope(blob)

    def test_valid_rp_passes(self) -> None:
        from seedbraid.container import (
            validate_encrypted_seed_envelope,
        )

        blob = self._make_v2_blob(
            scrypt_r=8, scrypt_p=1,
        )
        info = validate_encrypted_seed_envelope(blob)
        assert info.scrypt_r == 8
        assert info.scrypt_p == 1
