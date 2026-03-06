"""Seed signal definitions used by the baseline analyzer."""

SIGNALS = [
    {
        "code": "GENERIC_PHRASE",
        "name": "generic_phrase",
        "pattern": "facilitates",
        "description": "Generic phrasing that usually benefits from a more concrete verb.",
    },
    {
        "code": "VERBOSITY",
        "name": "verbosity",
        "pattern": "in order to",
        "description": "Verbose phrasing that can often be shortened without losing meaning.",
    },
]
