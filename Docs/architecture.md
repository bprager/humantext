# Architecture

## 1. Overview

HumanText is a modular, local-first system built around four cooperating subsystems:

1. **Detection**
2. **Reasoning**
3. **Rewrite**
4. **Style learning**

SQLite is the source of truth. Optional graph capabilities are layered on top when relationship traversal or explainable signal-to-strategy mapping benefits from graph queries.

## 2. Top-level architecture

```text
+-----------------------------+
| CLI / Editor / Agent Client |
+--------------+--------------+
               |
               v
+-----------------------------+
| MCP Server / API Adapter    |
+--------------+--------------+
               |
               v
+-----------------------------+
| Application Service Layer   |
| - analyze_text              |
| - suggest_edits             |
| - rewrite_text              |
| - learn_style               |
+---+-------------+-----------+
    |             |            
    v             v            v
+-------+    +---------+   +----------------+
|Detect |    |Rewrite  |   | Style Learner  |
+---+---+    +----+----+   +--------+-------+
    |             |                 |
    +-------> Reasoning Layer <-----+
                 |
                 v
        +-------------------+
        | SQLite Persistence|
        | + optional graph  |
        +-------------------+
```

## 3. Core runtime components

### 3.1 Ingestion and segmentation
Responsibilities:
- read markdown, txt, and later docx/html
- normalize whitespace and punctuation
- split into document, paragraph, sentence, clause spans
- assign stable IDs and offsets

### 3.2 Detector engine
Responsibilities:
- run lexical, syntactic, and structural detectors
- produce span-level findings
- attach evidence and rationale
- emit normalized signal scores

Detector types:
- lexical detectors
- phrase pattern detectors
- structure detectors
- citation/reference detectors
- style-profile deviation detectors

### 3.3 Reasoning layer
Responsibilities:
- map signals to strategies
- merge overlapping findings
- down-rank weak or redundant findings
- apply genre and profile-aware policies

Graph helps here because the problem is relational:
- signal -> supported_by -> evidence
- signal -> fixed_by -> strategy
- strategy -> constrained_by -> genre
- author -> has_trait -> voice_trait
- voice_trait -> softens -> signal

### 3.4 Rewrite engine
Responsibilities:
- produce minimal edits first
- escalate to larger rewrite only when needed
- preserve meaning and hard constraints
- emit a structured diff and rationale

Modes:
- suggest only
- minimally revise
- strong revise
- profile match

### 3.5 Style learner
Responsibilities:
- ingest trusted sample corpus
- extract stable voice features
- calculate confidence by feature
- store per-author voice profile
- update incrementally

### 3.6 MCP server
Expose tool endpoints:
- `analyze_text`
- `suggest_edits`
- `rewrite_text`
- `learn_style`
- `get_voice_profile`
- `list_signals`

## 4. Storage architecture

### 4.1 Why SQLite first
SQLite keeps the project:
- easy to run
- easy to test
- easy to embed
- attractive for open-source adoption

### 4.2 Optional graph overlay
Use `sqlite-graph` where it adds value, especially for:
- signal-to-strategy mapping
- explanation traversal
- provenance chains
- profile override logic

Do **not** make graph usage mandatory in the first implementation. Keep a repository layer so the project can run on plain relational tables first and optionally enable graph-backed queries.

## 5. Request lifecycle

### Analyze
1. normalize text
2. segment into spans
3. run baseline detectors
4. optionally load author profile
5. adjust findings using profile
6. aggregate and rank results
7. return JSON plus explanation

### Rewrite
1. analyze text
2. choose rewrite strategies
3. generate minimal candidate edits
4. validate constraints
5. return revised text plus change log

### Learn style
1. ingest trusted corpus
2. extract stylometric features
3. compute profile and confidence
4. persist traits and exemplars
5. mark corpus provenance

## 6. Evaluation architecture

Maintain three datasets:
- baseline AI-leaning samples
- trusted human samples
- author-specific corpora

Scoring dimensions:
- meaning preservation
- signal reduction
- user preference
- profile alignment
- edit acceptance

## 7. Deployment targets

### MVP
- Python package
- local CLI
- local MCP server

### Later
- VS Code extension
- Obsidian integration
- hosted API

## 8. Design constraints

- local-first by default
- no hard dependency on cloud models
- explainability over magic scores
- deterministic storage and migrations
- reproducible evaluation
