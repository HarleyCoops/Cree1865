"""Schema for English-to-Cree dictionary entries."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field


@dataclass
class CreeDictionaryEntry:
    """Single English-headword dictionary row with Cree realizations."""

    entry_id: str
    english_headword: str
    cree_primary: str
    column: int
    page_number: int
    source_image: str
    part_of_speech: str | None = None
    qualifiers: list[str] = field(default_factory=list)
    cree_variants: list[str] = field(default_factory=list)
    example_pairs: list[dict[str, str]] = field(default_factory=list)
    usage_notes: str | None = None
    see_also: list[str] = field(default_factory=list)
    confidence: float = 1.0
    extraction_notes: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Convert to a plain dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_translation_pair(self) -> dict[str, object]:
        """Return the primary English-to-Cree translation pair."""
        return {
            "source": self.english_headword,
            "target": self.cree_primary,
            "metadata": {
                "entry_id": self.entry_id,
                "pos": self.part_of_speech,
            },
        }


def validate_entry(entry: CreeDictionaryEntry) -> tuple[bool, list[str]]:
    """Validate a Cree dictionary entry."""
    issues: list[str] = []

    if not entry.entry_id:
        issues.append("Missing entry_id")
    if not entry.english_headword:
        issues.append("Missing english_headword")
    if not entry.cree_primary:
        issues.append("Missing cree_primary")
    if not 0.0 <= entry.confidence <= 1.0:
        issues.append(f"Invalid confidence: {entry.confidence}")
    if entry.english_headword.strip().lower() == entry.cree_primary.strip().lower():
        issues.append("English and Cree values are identical")

    return len(issues) == 0, issues
