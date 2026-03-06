"""Baseline text analysis helpers."""

from humantext.detectors.signals import SIGNALS


def analyze_text(text: str) -> list[dict[str, str]]:
    """Return simple span-free findings for the seeded baseline signals."""
    lowered = text.lower()
    findings: list[dict[str, str]] = []
    for signal in SIGNALS:
        if signal["pattern"] in lowered:
            findings.append(
                {
                    "signal_code": signal["code"],
                    "signal": signal["name"],
                    "description": signal["description"],
                }
            )
    return findings
