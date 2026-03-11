# Roadmap

## Phase 0, foundation
- package structure
- linting, tests, CI, releases
- SQLite migrations
- seeded signal catalog
- tracked local hooks

## Phase 1, baseline analysis MVP
- markdown and txt ingestion
- segmentation
- 30 baseline signals
- JSON analysis output
- CLI `analyze`

## Phase 2, rewrite MVP
- strategy map
- ranked edit planner
- structured diff output
- CLI `rewrite`
- baseline rule-driven rewrite engine

## Phase 3, style learning MVP
- corpus ingestion
- voice trait extraction
- profile persistence
- profile-aware weighting
- CLI `learn`

## Phase 4, integration surface
- local MCP server
- shared tool contracts
- SQLite-backed persistence
- editor and agent integration path

## Phase 5, deterministic quality expansion
- expand signal coverage using the strongest prompt-only editorial playbooks as backlog
- add missing detector families:
  - negative parallelism
  - rule of three
  - elegant variation
  - false range phrasing
  - title-case heading detection
  - emoji decoration
  - curly quote and punctuation normalization
  - sycophantic tone
  - excessive hedging
  - generic upbeat conclusions
- add stronger formatting-aware detectors
- add overlap-merging and deduplication between related findings
- add genre allowlists and suppressions, not only score adjustments

## Phase 6, precise rewrite engine
- replace document-wide regex rewrites with span-targeted edits
- keep offset-aware replacement planning
- add conflict resolution between overlapping edits
- preserve surrounding punctuation and formatting more reliably
- add stronger minimal, balanced, and profile-match rewrite modes

## Phase 7, second-pass editorial intelligence
- rewrite -> critique -> rewrite workflow
- deterministic post-checks for meaning drift
- rewrite quality scoring
- stronger preservation of qualifiers, named entities, and domain terms
- side-by-side comparison output for reviewers

## Phase 8, optional LLM augmentation
- user-defined and optional model configuration
- start with OpenAI-compatible adapter contract
- support local and hosted providers
- span-level LLM rewrite under strict constraints
- LLM critique pass for residual genericity
- LLM meaning-preservation review
- keep deterministic baseline available with LLM disabled

## Phase 9, evaluation and benchmark corpora
- benchmark corpus
- golden tests
- side-by-side comparison workflow
- rewrite acceptance scoring
- profile alignment evaluation
- domain demo folders for legal, consulting, product, and knowledge work

## Phase 10, product integrations
- VS Code extension
- Obsidian plugin
- optional web UI
- batch document workflows
- review queue for team usage
