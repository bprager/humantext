"""Minimal rewrite helpers."""

REPLACEMENTS = {
    "facilitates": "helps",
    "in order to": "to",
}


def rewrite_text(text: str) -> str:
    """Apply deterministic baseline replacements."""
    updated = text
    for source, target in REPLACEMENTS.items():
        updated = updated.replace(source, target)
    return updated
