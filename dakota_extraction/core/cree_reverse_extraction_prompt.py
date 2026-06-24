"""Specialized extraction prompt for the reverse Cree-English section."""

from __future__ import annotations


CREE_REVERSE_DICTIONARY_EXTRACTION_PROMPT = """You are analyzing a page from the reverse section of a historical **Cree-English dictionary**.

## Dictionary Structure

This is `Part II. Cree-English` from Watkins 1865. Treat the Cree headword as
the printed entry anchor, but normalize the extracted JSON into the same fields
used by the downstream Cree training builder:

1. `cree_primary` is the Cree entry headword exactly as printed.
2. `english_headword` is the English gloss or gloss phrase exactly as printed.
3. `cree_variants` contains alternate Cree forms, inflections, or related forms.

## Your Task

Extract EVERY dictionary entry on the page into the following JSON shape:

```json
{
  "page_metadata": {
    "columns": 2,
    "dictionary_direction": "cree_to_english",
    "layout_notes": "observations about the page layout",
    "quality_issues": "damage, bleed-through, skew, or unclear print"
  },
  "entries": [
    {
      "entry_id": "auto-generated later",
      "cree_primary": "Cree entry headword exactly as printed",
      "english_headword": "English gloss or gloss phrase exactly as printed",
      "part_of_speech": "n. | v. t. | v. i. | adj. | null",
      "qualifiers": ["semantic or usage qualifiers"],
      "cree_variants": ["additional Cree forms or variants"],
      "example_pairs": [
        {
          "cree": "example phrase in Cree",
          "english": "example phrase in English"
        }
      ],
      "usage_notes": "free-text note or null",
      "see_also": ["related entries or cross references"],
      "column": 1,
      "confidence": 0.0,
      "extraction_notes": "uncertainty, ambiguity, damaged text, or parsing issue"
    }
  ]
}
```

## Critical Instructions

1. Preserve Cree spelling exactly as printed, including hyphens, apostrophes,
   macrons, accents, or other orthographic marks.
2. Do not put the Cree headword in `english_headword`; use `cree_primary` for
   the Cree anchor and `english_headword` for its English meaning.
3. Process left column top-to-bottom before the right column.
4. Keep `cree_primary` to the best single main Cree headword. Put secondary
   forms in `cree_variants`.
5. If examples appear inline, split them into `example_pairs` only when the
   Cree and English sides can be paired with confidence.
6. Use `usage_notes` for cross-references, distribution notes, or extraction
   remarks that do not belong in the core fields.
7. If a value is not present, prefer `null` or `[]` over guessing.

## Output Rules

- Return ONLY JSON
- No markdown fences
- No prose before or after the JSON
- Preserve field names exactly
"""


def build_cree_reverse_extraction_prompt(page_context: str = "") -> str:
    """Return the reverse Cree-English extraction prompt with optional context."""
    prompt = CREE_REVERSE_DICTIONARY_EXTRACTION_PROMPT
    if page_context:
        prompt += f"\n\n## Page-Specific Context\n{page_context}\n"
    return prompt
