# Performance Regression Gates

This document defines the benchmark gate used to detect performance regressions.

## Scope
- Workload: 1-byte insertion (shifted-dedup scenario)
- Comparison: `fixed` vs `cdc_buzhash`
- Outputs: reuse improvement, seed size ratio, encode throughput

## Gate Command
```bash
uv run --no-editable python scripts/bench_gate.py \
  --min-reuse-improvement-bps 1 \
  --max-seed-size-ratio 1.20 \
  --min-cdc-throughput-mib-s 0.10 \
  --json-out .artifacts/bench-report.json
```

Exit status:
- `0`: all gates passed
- `1`: at least one gate failed

## Default Thresholds
- `min_reuse_improvement_bps = 1`
- `max_seed_size_ratio = 1.20`
- `min_cdc_throughput_mib_s = 0.10`

Notes:
- Defaults are conservative to reduce CI flakiness.
- Teams should tune thresholds based on stable runner baselines.

## JSON Report
`scripts/bench_gate.py` can write machine-readable output:
- source size and insertion offset
- per-chunker metrics
- reuse improvement and seed-size ratio

Recommended CI action:
1. Upload JSON artifact.
2. Track trend over time.
3. Tighten thresholds after baseline stabilization.

## IPFS Chunk Fetch Performance

### Scope
- Workload: CDC-chunked file publish to local IPFS daemon, then parallel
  fetch and reconstruct.
- Operations measured: chunk publish throughput, chunk fetch throughput,
  peak memory during fetch-decode.

### Reference Thresholds (Local Daemon)
- `min_chunk_publish_throughput` = 10 chunks/s (16 workers)
- `min_chunk_fetch_throughput` = 50 chunks/s (64 workers)
- `max_fetch_decode_memory_mib` = 100 MiB (1K chunks, batch_size=100)

Notes:
- Thresholds apply only when `ipfs` CLI is available; IPFS tests and
  benchmarks are auto-skipped in environments without a running daemon.
- Benchmark integration into `scripts/bench_gate.py` is planned for
  Phase 9 (Ticket #10).
- Memory bound is derived from `batch_size=100 * avg_chunk=64KiB =
  6.4 MiB` active buffer; 100 MiB ceiling allows for process overhead
  and hash table materialization.
- Publish throughput is lower than fetch because `ipfs block put` is a
  write operation with storage commitment; fetch is a read-only operation.
