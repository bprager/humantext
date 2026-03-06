# SQLite Schema

This schema is intentionally relational first, with an optional graph overlay.

## 1. Core relational schema

```sql
CREATE TABLE authors (
    author_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE voice_profiles (
    profile_id TEXT PRIMARY KEY,
    author_id TEXT NOT NULL REFERENCES authors(author_id),
    name TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'active',
    corpus_doc_count INTEGER NOT NULL DEFAULT 0,
    confidence REAL NOT NULL DEFAULT 0.0,
    summary_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE source_documents (
    document_id TEXT PRIMARY KEY,
    author_id TEXT REFERENCES authors(author_id),
    profile_id TEXT REFERENCES voice_profiles(profile_id),
    source_type TEXT NOT NULL,
    path TEXT,
    title TEXT,
    mime_type TEXT,
    checksum TEXT,
    trusted_for_learning INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE document_spans (
    span_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES source_documents(document_id),
    parent_span_id TEXT REFERENCES document_spans(span_id),
    span_type TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    start_offset INTEGER NOT NULL,
    end_offset INTEGER NOT NULL,
    text TEXT NOT NULL
);

CREATE TABLE signal_definitions (
    signal_code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    default_severity REAL NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    metadata_json TEXT NOT NULL
);

CREATE TABLE rewrite_strategies (
    strategy_code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);

CREATE TABLE signal_strategy_map (
    signal_code TEXT NOT NULL REFERENCES signal_definitions(signal_code),
    strategy_code TEXT NOT NULL REFERENCES rewrite_strategies(strategy_code),
    priority INTEGER NOT NULL DEFAULT 100,
    PRIMARY KEY (signal_code, strategy_code)
);

CREATE TABLE analysis_runs (
    analysis_id TEXT PRIMARY KEY,
    document_id TEXT,
    input_hash TEXT NOT NULL,
    profile_id TEXT,
    mode TEXT NOT NULL,
    created_at TEXT NOT NULL,
    summary_json TEXT NOT NULL
);

CREATE TABLE findings (
    finding_id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL REFERENCES analysis_runs(analysis_id),
    span_id TEXT REFERENCES document_spans(span_id),
    signal_code TEXT NOT NULL REFERENCES signal_definitions(signal_code),
    severity REAL NOT NULL,
    confidence REAL NOT NULL,
    profile_adjustment REAL NOT NULL DEFAULT 0.0,
    effective_score REAL NOT NULL,
    evidence_json TEXT NOT NULL,
    rationale TEXT NOT NULL
);

CREATE TABLE rewrite_runs (
    rewrite_id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL REFERENCES analysis_runs(analysis_id),
    profile_id TEXT,
    mode TEXT NOT NULL,
    input_text TEXT NOT NULL,
    output_text TEXT NOT NULL,
    diff_json TEXT NOT NULL,
    rationale_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE voice_traits (
    trait_id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL REFERENCES voice_profiles(profile_id),
    trait_code TEXT NOT NULL,
    trait_value TEXT NOT NULL,
    confidence REAL NOT NULL,
    evidence_json TEXT NOT NULL
);

CREATE TABLE exemplars (
    exemplar_id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL REFERENCES voice_profiles(profile_id),
    span_id TEXT NOT NULL REFERENCES document_spans(span_id),
    trait_code TEXT,
    note TEXT
);
```

## 2. Useful indexes

```sql
CREATE INDEX idx_spans_document_ordinal ON document_spans(document_id, ordinal);
CREATE INDEX idx_findings_analysis_score ON findings(analysis_id, effective_score DESC);
CREATE INDEX idx_voice_traits_profile_trait ON voice_traits(profile_id, trait_code);
CREATE INDEX idx_documents_profile_trusted ON source_documents(profile_id, trusted_for_learning);
```

## 3. Optional graph overlay with sqlite-graph

When graph mode is enabled, mirror selected entities as nodes and edges.

### Suggested node labels
- Author
- VoiceProfile
- Document
- Span
- Signal
- Strategy
- Trait
- Finding

### Suggested edges
- `(Author)-[:HAS_PROFILE]->(VoiceProfile)`
- `(VoiceProfile)-[:HAS_TRAIT]->(Trait)`
- `(Document)-[:HAS_SPAN]->(Span)`
- `(Span)-[:TRIGGERED]->(Signal)`
- `(Signal)-[:FIXED_BY]->(Strategy)`
- `(Trait)-[:SOFTENS]->(Signal)`
- `(Finding)-[:SUPPORTED_BY]->(Span)`

### Example graph queries

```sql
SELECT cypher_execute('
MATCH (s:Signal)-[:FIXED_BY]->(r:Strategy)
RETURN s, r
');
```

```sql
SELECT cypher_execute('
MATCH (t:Trait)-[:SOFTENS]->(s:Signal)
WHERE t.trait_code = "high_formality"
RETURN t, s
');
```

## 4. Serialization notes

Use JSON columns for:
- detector evidence
- profile summaries
- diff details
- strategy metadata

Keep canonical, query-worthy fields in first-class columns.

## 5. Migration guidance

- use integer schema versions
- keep detector definitions seedable
- avoid encoding business logic only in SQL
- keep graph mirroring idempotent and optional
