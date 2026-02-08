from __future__ import annotations

from helix.container import OP_RAW, OP_REF, Recipe, RecipeOp, parse_seed, serialize_seed


def test_seed_serialize_parse_serialize_stable() -> None:
    h1 = bytes.fromhex("00" * 32)
    h2 = bytes.fromhex("11" * 32)
    recipe = Recipe(
        hash_table=[h1, h2],
        ops=[RecipeOp(opcode=OP_REF, hash_index=0), RecipeOp(opcode=OP_RAW, hash_index=1)],
    )
    manifest = {
        "format": "HLX1",
        "version": 1,
        "source_size": 5,
        "source_sha256": "deadbeef",
        "chunker": {"name": "fixed", "min": 1, "avg": 1, "max": 1, "window_size": 0},
        "portable": True,
        "learn": False,
        "stats": {"total_chunks": 2, "reused_chunks": 1, "new_chunks": 1, "raw_chunks": 1},
        "created_at": "2026-02-08T00:00:00+00:00",
    }
    raw = {1: b"abc"}

    blob1 = serialize_seed(manifest, recipe, raw, manifest_compression="zlib")
    parsed = parse_seed(blob1)
    blob2 = serialize_seed(
        parsed.manifest,
        parsed.recipe,
        parsed.raw_payloads,
        manifest_compression=parsed.manifest_compression,
    )

    assert blob1 == blob2
