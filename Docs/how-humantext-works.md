# How HumanText Works

## Purpose

HumanText is a local-first editorial system for identifying and reducing generic, inflated, mechanical, or chatbot-like writing patterns while preserving meaning, terminology, and legitimate nuance.

The current implementation is intentionally conservative:

- deterministic signal detection
- structured ranking and explanation
- rule-based rewrite strategies
- optional persisted voice profiles
- local CLI, SQLite, and MCP access

It does not attempt to prove AI authorship. It treats signals as editorial heuristics.

## Runtime architecture

HumanText currently has five main runtime layers:

1. Input and orchestration
2. Analysis
3. Suggestion and rewrite
4. Voice-profile learning
5. Persistence and integration

At a high level:

```text
User / Editor / Agent
        |
        v
CLI / MCP server
        |
        v
Application functions
  - analyze_text
  - suggest_edits
  - rewrite_text
  - learn_style
        |
        +--------------------+
        |                    |
        v                    v
Deterministic analysis   Voice profile loading
        |                    |
        +----------+---------+
                   |
                   v
          Ranked findings / edit plan
                   |
                   v
           Rule-based rewrite engine
                   |
                   v
          JSON output + persistence
```

## Main components

### 1. CLI entrypoints

The CLI is implemented in [src/humantext/cli/main.py](/Users/bernd/Projects/HumanText/src/humantext/cli/main.py).

Current commands:

- `analyze`
- `suggest`
- `rewrite`
- `ingest`
- `learn`
- `version`
- `mcp-serve`

The CLI is thin orchestration. It reads files, resolves optional voice-profile context from SQLite, and forwards normalized arguments into the core service functions.

### 2. MCP server

The MCP adapter is implemented in [src/humantext/mcp/server.py](/Users/bernd/Projects/HumanText/src/humantext/mcp/server.py).

It exposes the same core services over newline-delimited JSON on stdio:

- `analyze_text`
- `suggest_edits`
- `rewrite_text`
- `learn_style`
- `get_voice_profile`
- `list_signals`

This is important because it means HumanText is already usable as an editor/agent backend, not just a local CLI.

### 3. Signal detection

Signal definitions live in [src/humantext/detectors/signals.py](/Users/bernd/Projects/HumanText/src/humantext/detectors/signals.py).

Each signal definition contains:

- `signal_code`
- `name`
- `category`
- `description`
- regex `patterns`
- `severity_default`
- `confidence`
- recommended rewrite strategies
- rationale

The analysis runtime is in [src/humantext/core/analysis.py](/Users/bernd/Projects/HumanText/src/humantext/core/analysis.py).

Current analysis flow:

1. Iterate through all seeded signal definitions.
2. Run regex matching against the text.
3. Create a `Finding` object for each matched span.
4. Attach evidence, rationale, and rewrite strategies.
5. Optionally apply profile-aware score adjustments.
6. Sort findings by effective score and span position.
7. Return an `AnalysisResult`.

The current system uses deterministic pattern matching. There is no probabilistic classifier in the runtime.

### 4. Data models

Shared contracts live in [src/humantext/core/models.py](/Users/bernd/Projects/HumanText/src/humantext/core/models.py).

Core model types:

- `Finding`
- `AnalysisResult`
- `EditPriority`
- `EditSuggestion`
- `VoiceTrait`
- `VoiceProfile`
- `RewriteChange`
- `RewriteResult`

These models are the backbone of the product because they keep CLI, MCP, persistence, and future UI layers aligned around the same structured output.

### 5. Suggestion layer

The suggestion layer is implemented in [src/humantext/core/suggest.py](/Users/bernd/Projects/HumanText/src/humantext/core/suggest.py).

Its job is to transform analysis findings into a ranked edit plan:

- map each finding to its primary strategy
- infer edit scope
- attach a reviewer-facing risk note
- collect sample edits from the rewrite engine

This is intentionally smaller and more actionable than a full rewrite.

### 6. Rewrite engine

The rewrite engine is implemented in [src/humantext/rewrite/engine.py](/Users/bernd/Projects/HumanText/src/humantext/rewrite/engine.py).

Current rewrite behavior:

1. Re-run analysis for the input text.
2. For each finding, iterate its recommended strategies.
3. Apply matching regex-based rewrite rules.
4. Record each applied change as a structured diff event.
5. Polish sentence starts and normalize whitespace.
6. Emit output text, warnings, and change log.

Important limitation:

- rewrites are still mostly document-wide regex substitutions, not precise span-targeted edits

That means the current system is useful, but not yet as surgical as it should become.

### 7. Voice learning

Voice learning is implemented in [src/humantext/learning/style.py](/Users/bernd/Projects/HumanText/src/humantext/learning/style.py).

Current profile extraction computes stable traits from trusted samples, including:

- average sentence length
- sentence length variance
- average paragraph length
- transition frequency
- contraction usage
- hedging frequency
- formality
- directness
- tolerance for abstraction

The current system stores both numeric and categorical traits, then uses some of those traits to adjust finding severity during analysis.

### 8. Persistence

Persistence is implemented in [src/humantext/storage/database.py](/Users/bernd/Projects/HumanText/src/humantext/storage/database.py) with schema in [migrations/001_init.sql](/Users/bernd/Projects/HumanText/migrations/001_init.sql).

SQLite currently stores:

- source documents
- spans
- analysis runs
- findings
- signal definitions
- rewrite strategies
- strategy mappings
- authors
- voice profiles
- voice traits

This makes HumanText reproducible and inspectable. It is one of the strongest differences between HumanText and prompt-only tools.

## Request flows

### Analyze flow

1. Read input text.
2. Optionally load persisted profile summary and traits.
3. Run signal detectors.
4. Adjust score based on profile traits when applicable.
5. Return structured findings, top signals, and summary.

### Suggest flow

1. Run analysis.
2. Turn findings into ranked edit priorities.
3. Generate sample rewrite snippets from the rewrite engine.
4. Return edit plan plus analysis context.

### Rewrite flow

1. Run analysis.
2. Apply strategy rules.
3. Normalize and polish text.
4. Return revised text plus structured change log.

### Learn flow

1. Load trusted `.md` and `.txt` documents.
2. Extract recurring voice features.
3. Create a `VoiceProfile`.
4. Persist profile and traits into SQLite.

## Why the current design works

The current design is strong in four ways:

- It is deterministic and inspectable.
- It exposes structured machine-readable outputs.
- It keeps local-first privacy as the default.
- It already has enough architecture to support stronger future layers.

## Current technical limitations

The biggest current limits are:

- detector coverage is still narrower than the best prompt-only editorial playbooks
- rewrite rules are not yet span-targeted
- there is no second-pass critique loop after rewrite
- the system mostly removes genericity; it is weaker at adding authentic authorial texture
- the profile model influences scoring more than actual rewrite style

## Strategic next step

The right next architecture move is not to replace the deterministic core. It is to keep the deterministic core as the baseline and layer in:

- broader signal coverage
- span-targeted editing
- optional LLM-assisted planning and critique
- stronger profile-conditioned rewriting

That preserves explainability while materially improving quality.
