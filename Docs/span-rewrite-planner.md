# Span Rewrite Planner

## Goal

Replace document-wide deterministic regex rewrites with offset-aware local patch planning while keeping the existing CLI and MCP `rewrite_text` interface stable.

## Why

The current deterministic rewrite path applies regex replacements across the whole document for each finding. That makes change logs less local, increases the risk of collateral edits, and weakens `suggest_edits`, which currently derives sample edits from full-document before and after snapshots.

## Design

### Phase 1

- add internal planning models: `PlannedEdit` and `RewritePlan`
- add a deterministic planner module that:
  - maps findings to local candidate edits
  - resolves overlapping edits
  - applies accepted edits as exact patches
- extend `RewriteChange` with offset metadata so downstream tooling can reason about local diffs
- keep LLM rewrite behavior unchanged for now

### Planner flow

1. Run analysis and collect findings.
2. Convert each finding into one or more local candidate edits.
3. Sort candidates by score and locality.
4. Reject duplicates and overlapping lower-priority edits.
5. Apply accepted edits in source order while tracking final offsets.
6. Polish touched sentences and emit local change records.

## Conflict rules

- identical range and replacement: reject as duplicate
- overlapping ranges: keep the higher-priority edit
- priority order:
  1. higher `effective_score`
  2. earlier generator order for the same finding and strategy family
  3. earlier offset

## API impact

- `rewrite_text` stays stable
- `suggest_edits` can consume the same local changes without a contract break
- `RewriteChange.before` and `RewriteChange.after` now represent local diffs instead of whole-document snapshots
- `RewriteChange.span_start` and `RewriteChange.span_end` identify the edited span in the rewritten output

## Follow-on phases

### Phase 2

- introduce sentence-scope and sentence-prefix edit generators
- reduce global cleanup after patch application

### Phase 3

- share the planner directly with `suggest_edits`
- expose richer plan metadata over CLI and MCP if useful

### Phase 4

- unify deterministic and LLM rewrite outputs around the same patch model
- add benchmark coverage for overlap and conflict resolution cases
