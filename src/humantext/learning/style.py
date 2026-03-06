"""Baseline voice-profile learning helpers."""

from __future__ import annotations

import re
import uuid
from statistics import mean, pstdev

from humantext.core.models import VoiceProfile, VoiceTrait
from humantext.core.segmentation import paragraph_spans, sentence_spans

_TRANSITIONS = ("however", "therefore", "additionally", "furthermore", "overall", "in summary")
_HEDGES = ("may", "might", "could", "perhaps", "suggests", "appears")
_ABSTRACT_NOUNS = ("landscape", "framework", "context", "significance", "interplay")
_CONTRACTIONS = re.compile(r"\b\w+'(?:t|re|ve|ll|d|s|m)\b", re.IGNORECASE)
_WORD_RE = re.compile(r"\b\w+\b")


def learn_voice_profile(documents: list[str], *, author_id: str, name: str | None = None) -> VoiceProfile:
    """Infer a baseline voice profile from trusted documents."""
    if not documents:
        raise ValueError("At least one trusted document is required to learn a voice profile")

    sentences = [sentence.text for document in documents for sentence in sentence_spans(document)]
    paragraphs = [paragraph.text for document in documents for paragraph in paragraph_spans(document)]
    words = [word for document in documents for word in _WORD_RE.findall(document)]

    sentence_lengths = [len(_WORD_RE.findall(sentence)) for sentence in sentences] or [0]
    paragraph_lengths = [len(_WORD_RE.findall(paragraph)) for paragraph in paragraphs] or [0]
    total_words = max(len(words), 1)

    transition_count = sum(document.lower().count(transition) for document in documents for transition in _TRANSITIONS)
    hedge_count = sum(document.lower().count(hedge) for document in documents for hedge in _HEDGES)
    abstract_count = sum(document.lower().count(noun) for document in documents for noun in _ABSTRACT_NOUNS)
    contraction_count = sum(len(_CONTRACTIONS.findall(document)) for document in documents)

    avg_sentence = round(mean(sentence_lengths), 2)
    sentence_variance = round(pstdev(sentence_lengths), 2) if len(sentence_lengths) > 1 else 0.0
    avg_paragraph = round(mean(paragraph_lengths), 2)
    transition_rate = round(transition_count / max(len(sentences), 1), 3)
    contraction_rate = round(contraction_count / total_words, 3)
    hedge_rate = round(hedge_count / total_words, 3)
    abstraction_rate = round(abstract_count / total_words, 3)

    formality = _formality(avg_sentence, contraction_rate)
    directness = _directness(avg_sentence, hedge_rate)
    abstraction_tolerance = _abstraction_tolerance(abstraction_rate)
    confidence = round(min(0.95, 0.45 + 0.08 * len(documents) + 0.01 * len(sentences)), 3)

    traits = [
        VoiceTrait("average_sentence_length", f"{avg_sentence}", confidence, sentences[:3]),
        VoiceTrait("sentence_length_variance", f"{sentence_variance}", max(0.3, confidence - 0.05), sentences[:3]),
        VoiceTrait("average_paragraph_length", f"{avg_paragraph}", max(0.3, confidence - 0.05), paragraphs[:3]),
        VoiceTrait("transition_frequency", f"{transition_rate}", max(0.3, confidence - 0.1), list(_TRANSITIONS[:3])),
        VoiceTrait("contraction_usage", f"{contraction_rate}", max(0.3, confidence - 0.05), _examples(documents, _CONTRACTIONS.pattern)),
        VoiceTrait("hedging_frequency", f"{hedge_rate}", max(0.3, confidence - 0.08), _examples(documents, "|".join(_HEDGES))),
        VoiceTrait("formality", formality, confidence, sentences[:3]),
        VoiceTrait("directness", directness, confidence, sentences[:3]),
        VoiceTrait("tolerance_for_abstraction", abstraction_tolerance, confidence, _examples(documents, "|".join(_ABSTRACT_NOUNS))),
    ]
    summary = (
        f"{name or author_id} tends toward {formality} formality, {directness} cadence, "
        f"and {abstraction_tolerance} tolerance for abstraction across {len(documents)} trusted document(s)."
    )
    return VoiceProfile(
        profile_id=f"profile_{uuid.uuid4().hex}",
        author_id=author_id,
        name=name or author_id,
        profile_summary=summary,
        confidence=confidence,
        corpus_doc_count=len(documents),
        traits=traits,
    )


def _examples(documents: list[str], pattern: str) -> list[str]:
    regex = re.compile(pattern, re.IGNORECASE)
    examples: list[str] = []
    for document in documents:
        for sentence in sentence_spans(document):
            if regex.search(sentence.text):
                examples.append(sentence.text)
                if len(examples) == 3:
                    return examples
    return examples


def _formality(avg_sentence: float, contraction_rate: float) -> str:
    if avg_sentence >= 20 and contraction_rate < 0.01:
        return "high"
    if avg_sentence >= 14:
        return "medium"
    return "low"


def _directness(avg_sentence: float, hedge_rate: float) -> str:
    if avg_sentence <= 15 and hedge_rate < 0.01:
        return "direct"
    if hedge_rate > 0.02:
        return "measured"
    return "balanced"


def _abstraction_tolerance(rate: float) -> str:
    if rate >= 0.02:
        return "high"
    if rate >= 0.01:
        return "medium"
    return "low"
