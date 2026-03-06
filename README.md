# HumanText

HumanText is a local-first editorial intelligence engine for teams who use AI to draft, but still need writing that sounds specific, accountable, and recognizably human.

It analyzes generic or mechanical writing patterns, explains why they weaken the prose, and helps revise text toward a stronger author voice without turning the product into an authorship detector.

## Why HumanText

Most AI writing tools rewrite too aggressively and explain too little.

HumanText is built to do the opposite:

- detect stylistic signals that make writing feel generic, inflated, or chatbot-like
- suggest targeted edits before heavy rewrites
- preserve meaning, terminology, and legitimate nuance
- learn voice traits from trusted writing samples
- run locally with a simple, inspectable architecture

## Who it is for

- consultants
- lawyers
- analysts
- founders
- editors
- teams building editorial or agent workflows

## Core workflow

1. Analyze text for stylistic signals.
2. Rank the highest-value edits.
3. Rewrite with constraints.
4. Learn and apply a real voice profile.
5. Expose the workflow through CLI, library, and MCP interfaces.

## Project direction

HumanText is designed as:

- local-first
- explainable
- profile-aware
- SQLite-backed
- integration-friendly

## Inspiration

The project was inspired by Wikipedia's field guide, [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), which catalogs common writing patterns often associated with AI-generated text. HumanText treats those patterns as heuristics for editorial analysis, not proof of authorship.

## Repository map

- `src/humantext/` - Python package scaffold
- `Docs/` - product and architecture documentation
- `migrations/` - database schema migrations
- `tests/` - unit and CLI smoke tests
- `Data/` - corpora, datasets, and sample material
- `.codex/` - project operating notes and session guidance

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
make check
PYTHONPATH=src python -m humantext.cli.main analyze Docs/demo.md
```

## Status

This repository is in active buildout. The architecture, schema, signal taxonomy, tests, and package structure are in place; the core analysis and rewrite engine are still at scaffold stage.
