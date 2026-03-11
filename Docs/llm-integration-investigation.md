# Optional LLM Integration Investigation

## Question

Would an optional, user-defined LLM integration drastically improve HumanText?

Short answer:

Yes, for rewrite quality, second-pass critique, profile matching, and factual-preservation review.

No, if the goal is to replace the deterministic signal engine entirely.

The right design is a hybrid system:

- deterministic analysis stays the baseline
- optional LLM capabilities sit on top as an enhancement layer
- the user chooses the model provider and whether cloud access is allowed

## Why an LLM can help

HumanText currently does well at:

- finding known signal patterns
- ranking issues
- making local rule-based cleanups
- learning lightweight voice profiles

But deterministic regex strategies are weaker at:

- nuanced paraphrase
- sentence-level restructuring
- preserving voice while removing genericity
- second-pass editorial critique
- meaning-preservation review
- handling cases where a signal is stylistic rather than lexical

An LLM can materially improve those areas.

## Where LLMs help the most

### 1. Rewrite quality

This is the highest-value use.

A capable model can:

- rewrite only the affected sentence or paragraph
- preserve the intended claim while varying rhythm and syntax
- produce less mechanical output than regex replacement
- adapt tone to profile and genre more naturally

This is where the quality jump can be drastic.

### 2. Second-pass critique

HumanText should adopt a two-pass or three-pass flow:

1. deterministic analysis
2. candidate rewrite
3. LLM critique of remaining AI-style residue
4. optional second rewrite

This mirrors what prompt-only tools often do well, but HumanText can do it with structured constraints and persistence.

### 3. Profile-conditioned editing

The current profile system mostly influences scoring.

An LLM can use stored voice traits and exemplar snippets to:

- preserve preferred cadence
- keep normal levels of hedging or abstraction
- avoid flattening the author into generic “clean prose”
- choose between minimal revision and stronger rewrite more intelligently

### 4. Meaning-preservation and claim safety review

An LLM is useful as a reviewer, not just a rewriter.

Example review tasks:

- compare original and rewritten text
- flag dropped qualifiers
- flag introduced unsupported claims
- flag removed named entities
- explain why a rewrite may have drifted from the source

That is a strong fit for model-based comparison.

### 5. Higher-coverage signal detection

This is useful, but less safe than rewrite assistance.

An LLM can identify patterns that regex rules miss:

- negative parallelisms
- euphonious but generic rhythm
- false ranges
- listicle cadence
- sycophantic tone
- generic positive endings

But this should remain advisory unless anchored to quoted evidence. Otherwise the system becomes less explainable and less reproducible.

## Where LLMs should not replace the core

The LLM should not replace:

- local baseline analysis
- persistence
- structured findings contracts
- explicit strategy mapping
- deterministic CI-safe behavior

Reasons:

- output variance
- cost
- latency
- privacy constraints
- harder testing and regression control
- weaker debuggability

HumanText’s differentiator is that it is a productized editorial engine, not only a prompt wrapper.

## Recommendation

Add an optional LLM enhancement layer, but keep it off by default.

The best architecture is:

### Tier 1: deterministic baseline

Always available.

- regex/pattern detectors
- profile-aware ranking
- rule-based suggestions
- local persistence

### Tier 2: optional LLM augmentation

Enabled only when configured.

- deeper edit planning
- span-targeted rewrites
- second-pass critique
- profile-conditioned restyling
- meaning-preservation review

### Tier 3: provider abstraction

The user chooses:

- local LLM
- hosted API
- OpenAI-compatible gateway

## Provider strategy

The fastest way to support “user-defined and optional” models is to target an OpenAI-compatible interface first.

Why:

- many local and hosted systems can expose that shape
- one adapter can cover multiple backends
- the user can point HumanText to their own base URL and model name

This should be the initial configuration contract:

- `provider`: `openai_compatible`, `openai`, `anthropic`, `ollama`
- `base_url`
- `api_key_env`
- `model`
- `timeout_seconds`
- `max_tokens`
- `temperature`
- `enabled_capabilities`

## Why this is practical now

Recent official docs support this approach:

- OpenAI’s Responses API supports structured outputs, function calling, custom tools, and MCP tools: [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses/retrieve)
- OpenAI recommends the Responses API as the forward path over older agent flows: [Responses migration guide](https://platform.openai.com/docs/guides/responses-vs-chat-completions)
- Anthropic documents a standard Messages API and has also announced an OpenAI-compatible endpoint in its API release notes: [Anthropic Messages](https://docs.anthropic.com/en/api/client-sdks), [Anthropic API release notes](https://docs.anthropic.com/en/release-notes/api)
- Ollama exposes a stable local API for self-hosted models: [Ollama API](https://docs.ollama.com/api)
- LiteLLM provides a unified gateway across many providers using OpenAI-style formats: [LiteLLM docs](https://docs.litellm.ai/)

## Best first implementation

Do not start with “LLM does everything.”

Start with one narrow, high-value capability:

### Option A: LLM rewrite for selected spans

Flow:

1. deterministic analysis finds spans
2. HumanText selects only affected spans
3. LLM rewrites each span under strict constraints
4. HumanText stitches the document back together
5. deterministic post-check validates the result

This gives the best quality jump with bounded risk.

### Option B: LLM critique after deterministic rewrite

Flow:

1. deterministic rewrite produces draft
2. LLM reviews original + rewritten text
3. model returns structured critique:
   - remaining generic phrases
   - possible meaning drift
   - tone mismatch
4. HumanText optionally runs a second rewrite

This is also strong, but should come after span-targeted rewriting exists.

## Recommended architecture

Add a new module family:

```text
src/humantext/llm/
  config.py
  client.py
  prompts.py
  adapters/
    openai_compatible.py
    anthropic.py
    ollama.py
  tasks/
    rewrite_span.py
    critique_rewrite.py
    compare_meaning.py
```

Then integrate optional calls at the application layer, not inside low-level models.

## Safety constraints for LLM use

Every LLM task should be constrained by:

- preserve all factual claims unless instructed otherwise
- do not introduce new sources
- do not add new named entities
- keep domain terminology intact
- return structured JSON only
- include a reason for every substantive rewrite

And every LLM-assisted rewrite should be post-checked for:

- named entity loss
- qualifier loss
- unsupported additions
- excessive edit distance in minimal mode

## Product impact

If implemented correctly, an optional LLM layer can drastically improve:

- rewrite naturalness
- profile alignment
- sentence rhythm
- second-pass quality control
- user-perceived helpfulness

It will not eliminate the need for the deterministic engine. It makes the deterministic engine more effective.

## Conclusion

HumanText should add optional, user-defined LLM support.

But the right framing is:

- deterministic core for reliability
- optional LLM layer for higher-order editorial intelligence

That combination is much stronger than either a pure prompt workflow or a pure regex workflow.
