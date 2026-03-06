"""Text segmentation helpers for ingestion."""

from __future__ import annotations

import re
from dataclasses import dataclass

_PARAGRAPH_RE = re.compile(r"\n\s*\n", re.MULTILINE)
_SENTENCE_RE = re.compile(r"[^.!?\n]+[.!?]?", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class Span:
    span_type: str
    ordinal: int
    start_offset: int
    end_offset: int
    text: str


def paragraph_spans(text: str) -> list[Span]:
    spans: list[Span] = []
    start = 0
    ordinal = 0
    for match in _PARAGRAPH_RE.finditer(text):
        end = match.start()
        segment = text[start:end].strip()
        if segment:
            real_start = text.index(segment, start, end if end > start else len(text))
            spans.append(Span("paragraph", ordinal, real_start, real_start + len(segment), segment))
            ordinal += 1
        start = match.end()
    tail = text[start:].strip()
    if tail:
        real_start = text.index(tail, start)
        spans.append(Span("paragraph", ordinal, real_start, real_start + len(tail), tail))
    return spans


def sentence_spans(text: str) -> list[Span]:
    spans: list[Span] = []
    ordinal = 0
    for match in _SENTENCE_RE.finditer(text):
        segment = match.group(0).strip()
        if not segment:
            continue
        start = match.start() + match.group(0).index(segment)
        spans.append(Span("sentence", ordinal, start, start + len(segment), segment))
        ordinal += 1
    return spans
