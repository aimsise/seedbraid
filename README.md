# Helix v2

Helix v2 provides reference-based reconstruction with deterministic content-defined chunking (CDC), a binary HLX1 seed format, and IPFS publish/fetch transport.

## Features
- Lossless encode/decode with SHA-256 verification.
- Chunkers: `fixed`, `cdc_buzhash`, `cdc_rabin`.
- Genome storage (SQLite) for deduplicated chunk reuse.
- HLX1 binary seed container (`manifest + recipe + optional RAW + integrity`).
- IPFS CLI integration (`publish`, `fetch`).

## Quick Start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Optional zstd support:
```bash
pip install -e .[dev,zstd]
```

## CLI
### Encode
```bash
helix encode input.bin --genome ./genome --out seed.hlx \
  --chunker cdc_buzhash --avg 65536 --min 16384 --max 262144 \
  --learn --no-portable --compression zlib
```

### Decode
```bash
helix decode seed.hlx --genome ./genome --out recovered.bin
```

### Verify
```bash
helix verify seed.hlx --genome ./genome
```

### Prime
```bash
helix prime "./dataset/**/*" --genome ./genome --chunker cdc_buzhash
```

### Publish (IPFS)
```bash
helix publish seed.hlx --no-pin
helix publish seed.hlx --pin
```

### Fetch (IPFS)
```bash
helix fetch <cid> --out fetched.hlx
```

## IPFS Installation/Check
Check if IPFS CLI is available:
```bash
ipfs --version
```

If missing, install Kubo (IPFS CLI) and ensure `ipfs` is on your PATH.

## Common Failures
- `ipfs CLI not found`:
  - Install IPFS and verify with `ipfs --version`.
- `Missing required chunk` on decode/verify:
  - Provide the correct `--genome`, or re-encode with `--portable`.
- `zstd` compression error:
  - Install optional dependency `zstandard`, or use `--compression zlib`.

## Tests and CI-Equivalent Local Commands
```bash
ruff check .
pytest
```

IPFS tests auto-skip when `ipfs` is not installed.

## 1-byte Insertion Dedup Benchmark
Run:
```bash
python scripts/bench_shifted_dedup.py
```

Expected behavior:
- `cdc_buzhash` should show better reuse than `fixed` when a single-byte insertion shifts offsets.

## Project Documents
- Format spec: `docs/FORMAT.md`
- Design rationale: `docs/DESIGN.md`
- Threat model: `docs/THREAT_MODEL.md`
- Plan: `PLANS.md`
