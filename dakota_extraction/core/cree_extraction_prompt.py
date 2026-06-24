"""Specialized extraction prompt for the Cree 1865 dictionary."""

from __future__ import annotations


CREE_DICTIONARY_EXTRACTION_PROMPT = """You are analyzing a page from a historical **English-Cree dictionary**.

## Dictionary Structure

This source is not formatted like the Dakota1890 dictionary. Treat it as an
**English -> Cree** reference work with a likely two-column page layout.

### Typical Entry Pattern
Each entry may contain:
1. **English headword**: the entry anchor, often in roman type and alphabetized
2. **Part of speech**: abbreviations such as `n.`, `v. t.`, `v. i.`, `adj.`
3. **Primary Cree rendering**: the main Cree word or phrase
4. **Additional Cree variants**: alternate forms, compounds, or related renderings
5. **Qualifiers**: semantic or usage qualifiers such as `steep`, `high`, `river bank`
6. **Example pairs**: short English examples with corresponding Cree realizations
7. **Usage notes / cross-references**: `See ...`, regional notes, or structural comments

## Your Task

Extract EVERY dictionary entry on the page into the following JSON shape:

```json
{
  "page_metadata": {
    "columns": 2,
    "dictionary_direction": "english_to_cree",
    "layout_notes": "observations about the page layout",
    "quality_issues": "damage, bleed-through, skew, or unclear print"
  },
  "entries": [
    {
      "entry_id": "auto-generated later",
      "english_headword": "English entry headword exactly as printed",
      "cree_primary": "main Cree rendering exactly as printed",
      "part_of_speech": "n. | v. t. | v. i. | adj. | null",
      "qualifiers": ["semantic or usage qualifiers"],
      "cree_variants": ["additional Cree forms or variants"],
      "example_pairs": [
        {
          "english": "example phrase in English",
          "cree": "example phrase in Cree"
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
2. Do not reverse the dictionary direction. The English headword is the prompt
   side, and the Cree realization is the answer side.
3. Process left column top-to-bottom before the right column.
4. Keep `cree_primary` to the best single main rendering. Put secondary forms
   in `cree_variants`.
5. If examples appear inline, split them into `example_pairs` only when the
   English and Cree sides can be paired with confidence.
6. Use `usage_notes` for comments like `See Spine`, distribution notes, or
   extraction remarks that do not belong in the core fields.
7. If a value is not present, prefer `null` or `[]` over guessing.

## Output Rules

- Return ONLY JSON
- No markdown fences
- No prose before or after the JSON
- Preserve field names exactly
"""


def build_cree_extraction_prompt(page_context: str = "") -> str:
    """Return the Cree dictionary extraction prompt with optional page context."""
    prompt = CREE_DICTIONARY_EXTRACTION_PROMPT
    if page_context:
        prompt += f"\n\n## Page-Specific Context\n{page_context}\n"
    return prompt

