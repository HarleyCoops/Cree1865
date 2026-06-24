"""Extraction prompt for the early Cree grammar and pronunciation pages."""

from __future__ import annotations


CREE_GRAMMAR_EXTRACTION_PROMPT = """You are analyzing an early grammar or pronunciation page from a historical Cree source.

## Goal

Extract **testable grammar rules** and **aligned example material** that can be
turned into supervised and reinforcement-learning tasks later.

## What To Extract

1. **Grammar rules**
   - rule name
   - rule type: morphology, syntax, phonology, orthography, semantics
   - description
   - pattern
   - constraints
   - exceptions
   - verification criteria

2. **Morphological transformations**
   - base form
   - transformed form
   - affixes or internal changes
   - English gloss of the base
   - English gloss of the transformed form

3. **Interlinear or aligned examples**
   - Cree text
   - word glosses
   - full English translation
   - morpheme breakdown when available

## Output Format

Return JSON with this exact top-level structure:

```json
{
  "page_metadata": {
    "page_number": null,
    "section_title": "heading if visible",
    "quality_issues": "damage or uncertainty"
  },
  "grammar_rules": [
    {
      "rule_id": "auto-generated later",
      "rule_type": "morphology",
      "rule_name": "descriptive title",
      "description": "what the rule does",
      "pattern": "{base} + suffix -> transformed form",
      "constraints": [],
      "exceptions": [],
      "verification_criteria": [],
      "transformations": [
        {
          "base_form": "source form",
          "transformed_form": "target form",
          "affixes": [],
          "gloss_base": "English meaning",
          "gloss_transformed": "English meaning after transformation",
          "special_chars": [],
          "phonological_changes": null
        }
      ],
      "difficulty": "basic",
      "testable": true
    }
  ],
  "interlinear_examples": [
    {
      "cree_text": "full Cree example",
      "cree_words": ["tokenized", "cree", "words"],
      "word_glosses": ["gloss", "per", "word"],
      "morpheme_breakdown": [["optional"], ["optional"]],
      "english_translation": "full translation",
      "special_characters_found": []
    }
  ],
  "linguistic_notes": "other page-level observations",
  "extraction_confidence": 0.0
}
```

## Critical Instructions

1. Preserve Cree orthography exactly.
2. Prefer rules that can later be converted into verifiable RL tasks.
3. Only emit examples that can be aligned with confidence.
4. If the page is mainly pronunciation guidance, capture it as orthography or
   phonology rules rather than forcing morphology.
5. Return ONLY JSON.
"""


def build_cree_grammar_extraction_prompt(page_context: str = "") -> str:
    """Return the Cree grammar extraction prompt with optional page context."""
    prompt = CREE_GRAMMAR_EXTRACTION_PROMPT
    if page_context:
        prompt += f"\n\n## Page-Specific Context\n{page_context}\n"
    return prompt

