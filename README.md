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
  <a href="https://github.com/bprager/humantext/actions/workflows/release.yml"><img src="https://img.shields.io/github/actions/workflow/status/bprager/humantext/release.yml?label=release" alt="Release Workflow"></a>
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

## Status

The current repository already includes baseline signal detection, ranked edit suggestions, rewrite strategies, voice-profile learning, SQLite persistence, CLI commands, and an MCP adapter. The next step is deeper profile-aware and span-aware editing behavior.

## Inspiration

HumanText was inspired by [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). Those patterns are used here as heuristics for editorial review, not as a claim of authorship certainty.
