<p align="center">
  <img src=".github/assets/humantext-logo.png" alt="HumanText logo" width="360">
</p>

<h1 align="center">HumanText</h1>

<p align="center">
  <strong>Local-first editorial intelligence for text that should sound specific, accountable, and human.</strong>
</p>

<p align="center">
  Analyze drafts. Rank the edits that matter. Rewrite with constraints. Learn a trusted voice profile.
</p>

<p align="center">
  <a href="https://github.com/bprager/humantext/releases"><img src="https://img.shields.io/github/v/release/bprager/humantext?display_name=tag" alt="Latest Release"></a>
  <a href="https://github.com/bprager/humantext/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/bprager/humantext/ci.yml?branch=main&label=lint%20%2B%20test%20%2B%20coverage" alt="CI Status"></a>
  <a href="https://codecov.io/gh/bprager/humantext"><img src="https://codecov.io/gh/bprager/humantext/graph/badge.svg?branch=main" alt="Code Coverage"></a>
  <a href="https://github.com/bprager/humantext/blob/main/LICENSE"><img src="https://img.shields.io/github/license/bprager/humantext" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/local--first-SQLite%20%2B%20MCP-0F766E" alt="Local-first SQLite and MCP">
</p>

HumanText is for reviewers, editors, and teams that use AI to draft but still need prose that reads like it came from a real author. It treats suspicious patterns as editorial signals, not proof of authorship.

## Why HumanText

- Flags generic, inflated, or mechanical phrasing with explanation-backed findings
- Suggests the smallest useful edits before resorting to a full rewrite
- Preserves facts, terminology, and legitimate nuance
- Learns from trusted samples instead of flattening every voice into one style
- Works locally through CLI, Python, SQLite, and MCP interfaces

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

humantext analyze Docs/demo.md
humantext suggest Docs/demo.md
humantext rewrite Docs/demo.md
humantext eval data/datasets/core-v1

# Optional LLM-assisted span rewriting
humantext rewrite Docs/demo.md \
  --llm-provider openai_compatible \
  --llm-base-url http://localhost:11434/v1 \
  --llm-model llama3.1

# Or keep the defaults in .env and just run rewrite
cat <<'EOF' > .env
HUMANTEXT_LLM_PROVIDER=openai_compatible
HUMANTEXT_LLM_BASE_URL=http://localhost:11434/v1
HUMANTEXT_LLM_MODEL=llama3.1
HUMANTEXT_LLM_API_KEY_ENV=OLLAMA_API_KEY
EOF

humantext rewrite Docs/demo.md
```

## Learn a Voice Profile

Point the learner at any directory of trusted `.md` or `.txt` files.

```bash
humantext learn ./trusted-samples --author-id acme --name "Acme Editorial"
```

## Run the MCP Adapter

```bash
humantext mcp-serve
```

## Run the Benchmark Suite

HumanText now ships with a seeded regression corpus for evaluation and CI-safe benchmark runs.

```bash
humantext eval data/datasets/core-v1
humantext eval data/datasets/core-v1 --format markdown --output reports/core-v1.md
```

## Optional LLM Augmentation

HumanText keeps deterministic analysis as the default path. If you provide an optional LLM configuration, `rewrite` can use a user-defined model to rewrite only the flagged sentence spans while preserving the deterministic fallback path.

The current optional LLM path now also runs deterministic post-checks, adds a second-pass critique section to the rewrite output, and can use that critique to drive one more targeted rewrite pass on the remaining flagged spans.

LLM settings can come from CLI flags, environment variables, or a local `.env` file. Resolution order is `CLI/MCP input -> real environment -> .env -> built-in defaults`. Supported env keys are `HUMANTEXT_LLM_PROVIDER`, `HUMANTEXT_LLM_BASE_URL`, `HUMANTEXT_LLM_MODEL`, `HUMANTEXT_LLM_API_KEY_ENV`, `HUMANTEXT_LLM_TIMEOUT`, `HUMANTEXT_LLM_TEMPERATURE`, and `HUMANTEXT_LLM_CAPABILITIES`.

## Status

The current repository already includes baseline signal detection, ranked edit suggestions, rewrite strategies, voice-profile learning, SQLite persistence, CLI commands, an MCP adapter, and a seeded evaluation harness for regression testing and benchmark runs. The next step is deeper profile-aware and span-aware editing behavior.

## Inspiration

HumanText was inspired by [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). Those patterns are used here as heuristics for editorial review, not as a claim of authorship certainty.
