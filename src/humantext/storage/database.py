"""SQLite-backed ingestion and persistence helpers."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from humantext.core.analysis import analyze_text
from humantext.core.models import AnalysisResult, VoiceProfile, VoiceTrait
from humantext.core.segmentation import paragraph_spans, sentence_spans
from humantext.detectors.signals import SIGNALS
from humantext.learning import learn_voice_profile


class HumanTextDatabase:
    """Thin SQLite wrapper aligned to the project migration schema."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row

    def close(self) -> None:
        self.connection.close()

    def initialize(self) -> None:
        if not self._schema_initialized():
            migration_path = Path(__file__).resolve().parents[3] / "migrations" / "001_init.sql"
            self.connection.executescript(migration_path.read_text(encoding="utf-8"))
        self.seed_signal_catalog()
        self.connection.commit()

    def seed_signal_catalog(self) -> None:
        strategy_rows: dict[str, tuple[str, str, str]] = {
            "replace_with_concrete_fact": ("Replace with concrete fact", "Swap generic importance language for a concrete claim.", "medium"),
            "delete_if_empty": ("Delete if empty", "Remove language that adds no substantive information.", "low"),
            "replace_with_specific_claim": ("Replace with specific claim", "Name the actual fact instead of gesturing at it.", "medium"),
            "name_source_or_remove": ("Name source or remove", "Add attribution the reader can inspect, or delete the claim.", "high"),
            "tighten_interpretive_tail": ("Tighten interpretive tail", "Cut shallow summary tails and keep the concrete point.", "low"),
            "swap_abstract_nouns_for_verbs": ("Swap abstract nouns for verbs", "Turn abstraction into concrete action where possible.", "medium"),
            "neutralize_promotional_language": ("Neutralize promotional language", "Replace promotional adjectives with factual wording.", "low"),
            "replace_canned_transition": ("Replace canned transition", "Drop the transition or continue directly.", "low"),
            "delete_redundant_summary": ("Delete redundant summary", "Remove summary framing that repeats the paragraph.", "low"),
            "simplify_to_plain_statement": ("Simplify to plain statement", "Prefer direct wording over inflated phrasing.", "low"),
            "remove_formatting_emphasis": ("Remove formatting emphasis", "Reduce generated-looking emphasis patterns.", "low"),
            "review_structure_for_authenticity": ("Review structure", "Check whether the structure is genuinely needed.", "low"),
            "remove_chat_residue": ("Remove chat residue", "Delete assistant-style framing or refusals.", "low"),
            "state_known_limits_plainly": ("State known limits plainly", "Describe source limits directly without speculation.", "low"),
            "verify_or_remove_reference": ("Verify or remove reference", "Keep only references that can be validated.", "high"),
            "remove_teacherly_preface": ("Remove teacherly preface", "State the point directly without instructional preface.", "low"),
        }
        self.connection.executemany(
            """
            INSERT OR IGNORE INTO rewrite_strategies(strategy_code, name, description, risk_level, metadata_json)
            VALUES(?, ?, ?, ?, ?)
            """,
            [(code, name, description, risk, json.dumps({})) for code, (name, description, risk) in strategy_rows.items()],
        )
        self.connection.executemany(
            """
            INSERT OR IGNORE INTO signal_definitions(signal_code, name, category, description, default_severity, enabled, metadata_json)
            VALUES(?, ?, ?, ?, ?, 1, ?)
            """,
            [
                (
                    signal.code,
                    signal.name,
                    signal.category,
                    signal.description,
                    signal.severity_default,
                    json.dumps({"confidence": signal.confidence, "patterns": signal.patterns}),
                )
                for signal in SIGNALS
            ],
        )
        self.connection.executemany(
            """
            INSERT OR IGNORE INTO signal_strategy_map(signal_code, strategy_code, priority)
            VALUES(?, ?, ?)
            """,
            [
                (signal.code, strategy, priority)
                for signal in SIGNALS
                for priority, strategy in enumerate(signal.rewrite_strategies, start=1)
            ],
        )

    def ensure_author(self, author_id: str, display_name: str | None = None) -> None:
        now = _timestamp()
        self.connection.execute(
            """
            INSERT INTO authors(author_id, display_name, created_at, updated_at)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(author_id) DO UPDATE SET
                display_name = excluded.display_name,
                updated_at = excluded.updated_at
            """,
            (author_id, display_name or author_id, now, now),
        )
        self.connection.commit()

    def ingest_document(
        self,
        text: str,
        *,
        path: str | None = None,
        title: str | None = None,
        source_type: str = "text",
        author_id: str | None = None,
        profile_id: str | None = None,
        trusted_for_learning: bool = False,
    ) -> str:
        document_id = f"doc_{uuid.uuid4().hex}"
        checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
        created_at = _timestamp()
        self.connection.execute(
            """
            INSERT INTO source_documents(
                document_id, author_id, profile_id, source_type, path, title, mime_type, checksum,
                trusted_for_learning, created_at
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (document_id, author_id, profile_id, source_type, path, title, "text/plain", checksum, int(trusted_for_learning), created_at),
        )
        spans = [*paragraph_spans(text), *sentence_spans(text)]
        for span in spans:
            self.connection.execute(
                """
                INSERT INTO document_spans(span_id, document_id, parent_span_id, span_type, ordinal, start_offset, end_offset, text)
                VALUES(?, ?, NULL, ?, ?, ?, ?, ?)
                """,
                (
                    f"span_{uuid.uuid4().hex}",
                    document_id,
                    span.span_type,
                    span.ordinal,
                    span.start_offset,
                    span.end_offset,
                    span.text,
                ),
            )
        self.connection.commit()
        return document_id

    def store_analysis(self, text: str, analysis: AnalysisResult, *, document_id: str | None = None, profile_id: str | None = None) -> str:
        analysis_id = f"analysis_{uuid.uuid4().hex}"
        created_at = _timestamp()
        self.connection.execute(
            """
            INSERT INTO analysis_runs(analysis_id, document_id, input_hash, profile_id, mode, created_at, summary_json)
            VALUES(?, ?, ?, ?, ?, ?, ?)
            """,
            (
                analysis_id,
                document_id,
                hashlib.sha256(text.encode("utf-8")).hexdigest(),
                profile_id,
                analysis.mode,
                created_at,
                json.dumps(
                    {
                        "summary": analysis.summary,
                        "top_signals": analysis.top_signals,
                        "genre": analysis.genre,
                        "profile_summary": analysis.profile_summary,
                    }
                ),
            ),
        )
        for finding in analysis.findings:
            self.connection.execute(
                """
                INSERT INTO findings(
                    finding_id, analysis_id, span_id, signal_code, severity, confidence,
                    profile_adjustment, effective_score, evidence_json, rationale
                ) VALUES(?, ?, NULL, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"finding_{uuid.uuid4().hex}",
                    analysis_id,
                    finding.signal_code,
                    finding.severity,
                    finding.confidence,
                    finding.profile_adjustment,
                    finding.effective_score,
                    json.dumps(finding.evidence),
                    finding.rationale,
                ),
            )
        self.connection.commit()
        return analysis_id

    def ingest_and_analyze(
        self,
        text: str,
        *,
        path: str | None = None,
        title: str | None = None,
        mode: str = "minimal",
        genre: str | None = None,
        profile_id: str | None = None,
        profile_summary: str | None = None,
    ) -> tuple[str, str, AnalysisResult]:
        document_id = self.ingest_document(text, path=path, title=title, profile_id=profile_id)
        analysis = analyze_text(
            text,
            mode=mode,
            genre=genre,
            profile_id=profile_id,
            profile_summary=profile_summary,
        )
        analysis_id = self.store_analysis(text, analysis, document_id=document_id, profile_id=profile_id)
        return document_id, analysis_id, analysis

    def learn_style(self, *, author_id: str, documents: list[dict[str, str]], profile_name: str | None = None) -> VoiceProfile:
        self.ensure_author(author_id, profile_name or author_id)
        texts = [document["text"] for document in documents]
        profile = learn_voice_profile(texts, author_id=author_id, name=profile_name or author_id)
        now = _timestamp()
        self.connection.execute(
            """
            INSERT INTO voice_profiles(
                profile_id, author_id, name, version, status, corpus_doc_count, confidence,
                summary_json, created_at, updated_at
            ) VALUES(?, ?, ?, 1, 'active', ?, ?, ?, ?, ?)
            """,
            (
                profile.profile_id,
                profile.author_id,
                profile.name,
                profile.corpus_doc_count,
                profile.confidence,
                json.dumps({"profile_summary": profile.profile_summary}),
                now,
                now,
            ),
        )
        for document in documents:
            self.ingest_document(
                document["text"],
                path=document.get("path"),
                title=document.get("title"),
                source_type=document.get("source_type", "text"),
                author_id=author_id,
                profile_id=profile.profile_id,
                trusted_for_learning=True,
            )
        for trait in profile.traits:
            self.connection.execute(
                """
                INSERT INTO voice_traits(trait_id, profile_id, trait_code, trait_value, confidence, evidence_json)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                (
                    f"trait_{uuid.uuid4().hex}",
                    profile.profile_id,
                    trait.trait_code,
                    trait.trait_value,
                    trait.confidence,
                    json.dumps(trait.evidence_examples),
                ),
            )
        self.connection.commit()
        return profile

    def get_voice_profile(self, profile_id: str) -> VoiceProfile | None:
        profile_row = self.connection.execute(
            "SELECT * FROM voice_profiles WHERE profile_id = ?",
            (profile_id,),
        ).fetchone()
        if profile_row is None:
            return None
        trait_rows = self.connection.execute(
            "SELECT trait_code, trait_value, confidence, evidence_json FROM voice_traits WHERE profile_id = ? ORDER BY trait_code",
            (profile_id,),
        ).fetchall()
        traits = [
            VoiceTrait(
                trait_code=row["trait_code"],
                trait_value=row["trait_value"],
                confidence=row["confidence"],
                evidence_examples=json.loads(row["evidence_json"]),
            )
            for row in trait_rows
        ]
        summary = json.loads(profile_row["summary_json"])["profile_summary"]
        return VoiceProfile(
            profile_id=profile_row["profile_id"],
            author_id=profile_row["author_id"],
            name=profile_row["name"],
            profile_summary=summary,
            confidence=profile_row["confidence"],
            corpus_doc_count=profile_row["corpus_doc_count"],
            traits=traits,
        )

    def list_rows(self, table: str) -> list[sqlite3.Row]:
        return list(self.connection.execute(f"SELECT * FROM {table}"))

    def _schema_initialized(self) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'authors'"
        ).fetchone()
        return row is not None


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()
