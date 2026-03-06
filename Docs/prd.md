# Product Requirements Document

## Product name

HumanText

## Vision

Build a local-first editorial intelligence system that helps people turn AI-assisted drafts into writing that feels authentic, specific, and human, while preserving meaning and respecting the author's own voice.

## Problem statement

AI-generated and AI-assisted text often carries recognizable patterns such as inflated significance, generic phrasing, repetitive transitions, vague attribution, canned summaries, and residual chatbot wording. Wikipedia's field guide catalogs many of these signals and explicitly notes that they are descriptive clues rather than proof. HumanText should operationalize those clues without turning them into brittle rules.

At the same time, many strong human writers naturally share some of these traits. A formal lawyer, academic, or architect may legitimately write with long sentences, abstract nouns, or a measured tone. A useful product therefore needs **two layers**:

1. a baseline heuristic layer
2. a personalized style layer learned from trusted documents

## Users

### Primary users
- consultants
- lawyers
- analysts
- founders
- executives
- academics

### Secondary users
- editors
- technical writers
- product marketers
- developers integrating MCP workflows

## Jobs to be done

1. Analyze whether a passage sounds generic, inflated, or chatbot-like.
2. Show what specifically makes it sound that way.
3. Suggest targeted edits rather than opaque rewrites.
4. Rewrite toward a preferred voice profile.
5. Learn an individual's style from prior documents.
6. Expose all of the above to editors and agents.

## Key use cases

### UC1, Analyze text
Input: paragraph or full document.
Output:
- signals with spans
- severity
- confidence
- rationale
- recommended edits

### UC2, Suggest edits
Input: paragraph plus optional style profile.
Output:
- ordered edit suggestions
- before/after snippets
- explanation per suggestion

### UC3, Rewrite text
Input: text plus constraints.
Constraints may include:
- preserve technical terminology
- preserve legal hedging
- do not change cited claims
- target concise or formal tone
- follow known voice profile

### UC4, Learn style
Input: folder of trusted documents.
Output:
- extracted features
- normalized `VoiceProfile`
- confidence by feature
- corpus quality score

### UC5, MCP integration
Input: requests from an IDE, editor, or agent.
Output:
- machine-readable JSON results
- optional markdown explanation

## Functional requirements

### Detection
- detect at least 30 baseline signals in MVP
- support span-level findings
- aggregate findings into document-level summary
- support configuration by genre

### Personalization
- ingest plain text and markdown in MVP
- maintain per-author voice profiles
- allow a profile to soften or override a baseline suggestion
- track provenance from source documents

### Rewriting
- generate suggested edits before full rewrite
- preserve meaning by default
- expose a “minimal edit” mode
- expose a “strong humanization” mode

### Explainability
- every major finding has a human-readable rationale
- every rewrite returns a change log
- system distinguishes baseline heuristic from personal-style adjustment

### Storage
- use SQLite as primary store
- support optional graph overlay via `sqlite-graph`
- support migrations

### Interfaces
- CLI
- Python library
- MCP server

## Non-goals for MVP

- authorship proof
- plagiarism detection
- truth verification of all claims
- automatic legal or medical advice validation
- full word-processor UI

## Success metrics

- >60% suggestion acceptance in pilot workflows
- preferred over a plain LLM rewrite in side-by-side review
- measurable reduction in flagged signals
- high meaning-preservation scores in evaluation set
- GitHub adoption and issue activity as open source signal

## Risks

1. Over-correction into bland “safe” prose
2. Misclassifying genuine human style as synthetic
3. Losing domain precision in rewrite step
4. Overfitting to current LLM style quirks
5. False user expectation that the tool can “hide AI use” with certainty

## Mitigations

- personalize against trusted corpus
- default to minimal edits
- require explanation per suggestion
- add evaluation harness and golden datasets
- position product as editorial quality support, not evasion

## Release slices

### Slice 1
- baseline heuristics
- CLI analysis
- structured JSON output

### Slice 2
- rewrite engine
- explanation diff
- evaluation harness

### Slice 3
- style learning
- profile-aware rewriting

### Slice 4
- MCP server
- editor integration
