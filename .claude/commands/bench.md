---
description: "Run performance benchmarks and compare results"
argument-hint: "[benchmark target or comparison ref (optional)]"
---

Run performance benchmarks. Target: $ARGUMENTS

## Instructions

1. Run the benchmark gate:
   ```
   PYTHONPATH=src uv run python scripts/bench_gate.py
   ```
2. If a comparison ref is specified, checkout that ref in a temp worktree and compare
3. Report results summary:
   - Throughput numbers
   - Any threshold violations
   - Comparison with baseline (if applicable)
4. Reference `docs/PERFORMANCE.md` for threshold definitions
