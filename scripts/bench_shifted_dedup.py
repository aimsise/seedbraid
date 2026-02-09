from __future__ import annotations

import random
import tempfile
from pathlib import Path

from helix.chunking import ChunkerConfig
from helix.codec import encode_file, prime_genome


def run_case(
    chunker: str,
    cfg: ChunkerConfig,
    base: Path,
    shifted: Path,
    tmp: Path,
) -> tuple[dict, int]:
    genome = tmp / f"genome-{chunker}"
    seed = tmp / f"shifted-{chunker}.hlx"

    prime_stats = prime_genome(base, genome, chunker=chunker, cfg=cfg)
    encode_stats = encode_file(
        in_path=shifted,
        genome_path=genome,
        out_seed_path=seed,
        chunker=chunker,
        cfg=cfg,
        learn=True,
        portable=False,
        manifest_compression="zlib",
    )
    return {
        "primed_total": prime_stats["total_chunks"],
        "total_chunks": encode_stats.total_chunks,
        "reused_chunks": encode_stats.reused_chunks,
        "new_chunks": encode_stats.new_chunks,
        "reuse_ratio": (
            0
            if encode_stats.total_chunks == 0
            else encode_stats.reused_chunks / encode_stats.total_chunks
        ),
    }, seed.stat().st_size


def main() -> None:
    cfg = ChunkerConfig(min_size=4_096, avg_size=16_384, max_size=65_536, window_size=32)
    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        base = tdir / "base.bin"
        shifted = tdir / "shifted.bin"

        rng = random.Random(42)
        original = bytes(rng.randrange(0, 256) for _ in range(3_200_000))
        base.write_bytes(original)
        shifted.write_bytes(original[:100_000] + b"Z" + original[100_000:])

        fixed_stats, fixed_seed_size = run_case("fixed", cfg, base, shifted, tdir)
        cdc_stats, cdc_seed_size = run_case("cdc_buzhash", cfg, base, shifted, tdir)

        print("== 1-byte insertion dedup benchmark ==")
        print(
            "fixed      "
            f"reuse_ratio={fixed_stats['reuse_ratio']:.4f} "
            f"new_chunks={fixed_stats['new_chunks']} seed_size={fixed_seed_size}"
        )
        print(
            "cdc_buzhash "
            f"reuse_ratio={cdc_stats['reuse_ratio']:.4f} "
            f"new_chunks={cdc_stats['new_chunks']} seed_size={cdc_seed_size}"
        )


if __name__ == "__main__":
    main()
