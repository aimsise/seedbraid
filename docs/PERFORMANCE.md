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
