---
description: "Plan and execute a refactoring with safety checks"
argument-hint: "<refactoring target and goal>"
---

Plan and execute refactoring: $ARGUMENTS

Current state:
!`git status --short`
!`git diff --stat`

## Instructions

1. Spawn the **planner** agent to create a refactoring plan
2. Present the plan summary and ask for user approval before proceeding
3. After approval, implement changes incrementally
4. After each significant change, run:
   - Tests: `PYTHONPATH=src uv run --no-editable python -m pytest`
   - Lint: `UV_CACHE_DIR=.uv-cache uv run --no-editable ruff check .`
5. Spawn the **code-reviewer** agent to verify the final result
6. Report summary of changes and verification results
