# Rewrite Arena

## Purpose

Rewrite Arena is HumanText's counterfactual editing layer. Instead of returning one rewrite and asking the reviewer to trust it, the arena generates several disciplined alternatives, scores their tradeoffs, and recommends one.

## Why it exists

HumanText already knows how to:

- detect baseline signals
- plan local deterministic edits
- rewrite with deterministic and optional LLM paths
- learn a voice profile
- explain diffs

Rewrite Arena sits above those layers and turns them into a reviewer-facing choice system.

## Candidate lanes

### Minimal Cut

- remove the loudest problems
- keep the draft closest to its current shape

### Balanced Draft

- reduce more signals than Minimal Cut
- still avoid an overly aggressive sweep

### Hard Sweep

- apply the full deterministic edit plan
- optimize for maximum signal reduction

### Profile Match

- available when a voice profile is loaded
- lets profile traits veto lower-value edits that would flatten a legitimate style

### LLM Challenger

- available when optional LLM rewrite support is configured
- competes against the deterministic lanes under the same guardrails

## Scorecard

Each candidate is scored on:

- signal reduction
- protected-token retention
- qualifier retention
- negation retention
- edit distance ratio
- voice fit
- overall score

## Recommendation rule

The recommended candidate is the one with the highest overall score after balancing:

1. signal reduction
2. preservation of protected content
3. voice fit against the loaded profile, when available
4. restraint in total edit distance

## Current limits

- arena choices are not yet persisted as long-term editorial preferences
- the deterministic lanes use heuristics rather than a learned reward model
- voice fit is still a lightweight heuristic, not a corpus-level preference model

## Why it matters

This is the first HumanText feature that treats editorial quality as a choice among nearby alternatives rather than a single output. That makes the system more reviewable, more trustworthy, and much better positioned for future preference learning.
