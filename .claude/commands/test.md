---
description: "Create and run tests for specified files or features"
argument-hint: "<file path or feature name to test>"
---

Create and run tests for: $ARGUMENTS

## Instructions

1. Spawn the **test-writer** agent with the target
2. Do NOT write tests directly — delegate ALL test work to the agent
3. The test-writer will:
   - Examine existing test patterns in `tests/`
   - Create appropriate test cases
   - Run tests and fix failures
4. Report test file paths and pass/fail results to the user
