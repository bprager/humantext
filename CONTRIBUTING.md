# Contributing

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install coverage ruff
git config core.hooksPath .githooks
make check
```

## Git hooks

The repository ships tracked hooks in `.githooks/`:

- `pre-commit` runs `make check`
- `pre-push` runs `make check` and `make coverage`

## Ground rules

- keep the project local-first
- keep heuristics explainable
- add tests with each new signal
- prefer minimal dependencies
- do not market or position the project as detector evasion

## Pull request expectations

- tests pass
- docs updated if behavior changes
- new signals include examples and rewrite strategies
- migration added for schema changes
