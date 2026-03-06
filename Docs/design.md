# Design

## Design goals

1. Make the tool useful in real editing, not just demo detection.
2. Prefer targeted suggestions over heavy rewriting.
3. Learn an author's actual habits.
4. Keep the output inspectable and debuggable.

## User experience

### Analyze experience
The user pastes text and gets:
- a short summary
- a ranked signal list
- marked spans
- explanation per signal

### Suggest experience
The user sees a compact edit plan:
- what to cut
- what to make more concrete
- where to replace canned transitions
- what to keep because it matches the author's voice

### Rewrite experience
The user gets:
- revised text
- diff
- rationale
- confidence notes

## Detection design

Each signal definition includes:
- `signal_code`
- `name`
- `description`
- `category`
- `patterns`
- `anti_patterns`
- `severity_default`
- `rewrite_strategies`
- `genres_where_allowed`
- `notes`

### Detector output contract

```json
{
  "signal_code": "GENERIC_SIGNIFICANCE",
  "span_start": 120,
  "span_end": 168,
  "severity": 0.72,
  "confidence": 0.81,
  "evidence": ["marking a pivotal moment", "broader landscape"],
  "profile_adjustment": -0.10,
  "recommended_strategies": ["replace_with_specific_claim", "delete_if_empty"]
}
```

## Personal style model design

A `VoiceProfile` should include both statistics and exemplars.

### Quantitative features
- average sentence length
- sentence length variance
- average paragraph length
- punctuation frequency
- transition frequency
- contraction usage
- passive voice tendency
- lexical concreteness proxy
- hedging frequency
- list frequency

### Qualitative traits
- level of formality
- directness
- tolerance for abstraction
- preferred openings and closings
- favored transition words
- favored sentence cadence

### Confidence
Every feature gets a confidence score based on:
- corpus size
- corpus diversity
- recency
- quality filters

## Rewrite strategy design

Strategies should be granular and composable.

Examples:
- replace inflated significance with concrete fact
- replace vague attribution with named source or remove
- cut summary sentence at section end
- replace canned transition with direct continuation
- swap abstract noun phrase for active verb
- simplify copula avoidance
- preserve purposeful hedging in legal or scientific prose

## Modes

### Minimal edit mode
Only apply high-confidence, local edits.

### Balanced mode
Apply broader cleanup while preserving cadence.

### Strong humanization mode
Apply deeper rewrites, but still preserve meaning.

### Profile match mode
Prioritize moves that resemble the author's known habits.

## Evaluation design

### Automatic checks
- JSON schema validity
- no dropped named entities without explanation
- no increase in unsupported claims
- bounded edit distance in minimal mode

### Human review checks
- feels more natural
- keeps intended meaning
- matches author voice
- avoids overediting

## Failure modes to guard against

- bland output
- style drift toward generic “assistant” prose
- accidental claim mutation
- over-penalizing formal human writing
- mistaking domain conventions for AI residue

## UI notes for future integrations

- show spans inline
- allow accept/reject per suggestion
- always expose explanation toggle
- permit corpus management for voice learning
