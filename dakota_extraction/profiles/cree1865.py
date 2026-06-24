"""Source profile for the Cree 1865 bootstrap dictionary."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HistoricalSourceProfile:
    """Structured source metadata for a historical dictionary pipeline replay."""

    profile_id: str
    language_name: str
    source_title: str
    source_author: str
    source_year: int
    pdf_path: str
    page_count: int
    front_matter_end_pdf_page: int
    dictionary_start_pdf_page: int
    dictionary_direction: str
    column_layout: str
    reverse_dictionary_transition_pdf_page: int | None = None
    reverse_dictionary_start_pdf_page: int | None = None
    reverse_dictionary_transition_printed_page: int | None = None
    reverse_dictionary_start_printed_page: int | None = None
    sample_dictionary_pages: tuple[int, ...] = field(default_factory=tuple)
    sample_reverse_dictionary_pages: tuple[int, ...] = field(default_factory=tuple)
    sample_front_matter_pages: tuple[int, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return asdict(self)


CREE1865_PROFILE = HistoricalSourceProfile(
    profile_id="cree1865",
    language_name="Cree",
    source_title="A Dictionary of the Cree Language",
    source_author="E. A. Watkins",
    source_year=1865,
    pdf_path=str(Path("CreeDictionary.pdf")),
    page_count=492,
    front_matter_end_pdf_page=28,
    dictionary_start_pdf_page=29,
    reverse_dictionary_transition_pdf_page=211,
    reverse_dictionary_start_pdf_page=212,
    reverse_dictionary_transition_printed_page=183,
    reverse_dictionary_start_printed_page=184,
    dictionary_direction="english_to_cree",
    column_layout="two-column",
    sample_dictionary_pages=(29, 40, 100),
    sample_reverse_dictionary_pages=(212, 220),
    sample_front_matter_pages=(24, 28),
    notes=(
        "Front matter includes preface, pronunciation key, and early grammar notes.",
        "Part I English-Cree begins at PDF page 29.",
        "The reverse-section transition appears at printed page 183, which lands at PDF page 211 in the local scan.",
        "The first full Cree-English entry page appears at printed page 184, which lands at PDF page 212 in the local scan.",
        "Current automated extraction is only schema-ready for Part I English-Cree pages.",
    ),
)
