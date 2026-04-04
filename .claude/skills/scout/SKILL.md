---
name: scout
description: >-
  Investigate codebase and create an implementation plan by chaining
  /investigate (researcher, sonnet) and /plan2doc or /plan2doc-light.
  Routes to sonnet planner for S-size tickets, opus for M+.
disable-model-invocation: true
allowed-tools:
  - Skill
  - Read
argument-hint: "<topic or ticket to investigate and plan>"
---

Investigate and plan: $ARGUMENTS

## Instructions

1. Before calling /investigate, attempt to read the ticket file directly:
   - If `$ARGUMENTS` matches a ticket pattern (e.g., "T-030", "T-028b"), look for
     `.docs/tickets/TICKET-<NNN>-*.md` or `.docs/tickets/TICKET-<NNN><suffix>-*.md` using Glob.
   - If multiple matches, use the first. If zero matches, skip to step 2 (Size stays unset).
   - If found, read the `| Size |` table row to extract the Size value (S/M/L/XL).
2. Call `/investigate` with the topic to run codebase research via the researcher agent (sonnet).
3. Check the investigate response for failure conditions:
   - If the response contains `**Status**: failed` or `**Status**: partial`, print the error and stop.
   - If the response does not contain a research file path (e.g., no `.docs/research/` path), print an error and stop.
   - Only proceed if `**Status**: success` and a research file path is present.
4. Print the research summary and file path returned by investigate.
5. Determine the final Size:
   - If Size was read from the ticket file in step 1, use that value.
   - Otherwise, read the research file for a Size field (S/M/L/XL). Default to M if absent.
6. Route to the appropriate planner, including the research file path in the arguments:
   - **Size S**: Call `/plan2doc-light` with `<topic> (research: <research-file-path>)`.
   - **Size M/L/XL**: Call `/plan2doc` with `<topic> (research: <research-file-path>)`.
7. Print the plan summary and file path returned by plan2doc.
8. Print a final summary with both file paths and the detected size.

## Error Handling

- **Empty arguments**: Print "Usage: /scout <topic or ticket>" and stop.
- **investigate failure**: If `**Status**: failed` or `**Status**: partial` is present, or no research file path (`.docs/research/` path) is found in the response, print the error and stop. Do NOT proceed to plan2doc.
- **plan2doc failure**: Print the error and the research file path (research is still valid).
