"""Helpers for building Cree SFT and RL tasks from extracted dictionary rows."""

from __future__ import annotations

from dataclasses import dataclass
import re


CREE_ORTHOGRAPHY_CHARS = set(
    "\u0101\u0113\u012b\u014d\u016b"
    "\u00e1\u00e9\u00ed\u00f3\u00fa"
    "\u00e2\u00ea\u00ee\u00f4\u00fb"
)


@dataclass
class NormalizedCreeEntry:
    """Lightweight representation of an English-to-Cree dictionary row."""

    entry_id: str
    english_headword: str
    cree_primary: str
    part_of_speech: str | None
    qualifiers: list[str]
    variants: list[str]
    examples: list[str]
    usage_notes: str | None
    page_number: int | None
    source_image: str | None
    confidence: float | None

    @property
    def context_block(self) -> str:
        """Context block embedded in training prompts."""
        lines: list[str] = []
        if self.part_of_speech:
            lines.append(f"Part of speech: {self.part_of_speech}")
        if self.qualifiers:
            lines.append("Qualifiers: " + ", ".join(self.qualifiers))
        if self.variants:
            lines.append("Variants: " + ", ".join(self.variants))
        if self.examples:
            lines.append("Examples: " + " | ".join(self.examples))
        if self.usage_notes:
            lines.append(f"Usage notes: {self.usage_notes}")
        if self.page_number is not None:
            lines.append(f"Source page: {self.page_number}")
        return "\n".join(lines)


def estimate_difficulty(entry: NormalizedCreeEntry) -> str:
    """Infer a coarse task difficulty."""
    example_bonus = len(entry.examples) * 2
    variant_bonus = len(entry.variants)
    qualifier_bonus = len(entry.qualifiers)
    score = len(entry.cree_primary.split()) + example_bonus + variant_bonus + qualifier_bonus
    if score <= 6:
        return "easy"
    if score <= 14:
        return "medium"
    return "hard"


def build_sft_example(entry: NormalizedCreeEntry) -> dict[str, object]:
    """Return a supervised fine-tuning example."""
    return {
        "instruction": "Translate the English headword into Cree.",
        "input": f"English: {entry.english_headword}\n{entry.context_block or 'No additional context available.'}",
        "output": entry.cree_primary,
        "metadata": {
            "entry_id": entry.entry_id,
            "difficulty": estimate_difficulty(entry),
            "pos": entry.part_of_speech,
        },
    }


def _special_chars(text: str) -> list[str]:
    return sorted(set(text) & CREE_ORTHOGRAPHY_CHARS)


def _base_info(entry: NormalizedCreeEntry, task_type: str, answer: str) -> dict[str, object]:
    difficulty = estimate_difficulty(entry)
    return {
        "rule_id": entry.entry_id,
        "task_type": task_type,
        "difficulty": difficulty,
        "verification_pattern": re.escape(answer),
        "special_chars": _special_chars(answer),
        "required_affixes": [],
        "hints": [answer],
        "orthography_chars": sorted(CREE_ORTHOGRAPHY_CHARS),
    }


def _task_metadata(entry: NormalizedCreeEntry, direction: str) -> dict[str, object]:
    return {
        "direction": direction,
        "entry_id": entry.entry_id,
        "difficulty": estimate_difficulty(entry),
        "page": entry.page_number,
        "source_image": entry.source_image,
        "confidence": entry.confidence,
    }


def build_forward_task(entry: NormalizedCreeEntry) -> dict[str, object]:
    """English-to-Cree lookup task."""
    prompt_lines = [
        "Translate the following English headword into Cree.",
        f"English: {entry.english_headword}",
    ]
    if entry.part_of_speech:
        prompt_lines.append(f"Part of speech: {entry.part_of_speech}")
    if entry.examples:
        prompt_lines.append("Example usage: " + entry.examples[0])
    if entry.usage_notes:
        prompt_lines.append(f"Usage notes: {entry.usage_notes}")

    prompt = "\n".join(prompt_lines) + "\n"
    difficulty = estimate_difficulty(entry)
    return {
        "id": f"{entry.entry_id}_english_to_cree",
        "task_id": f"{entry.entry_id}_english_to_cree",
        "prompt": prompt,
        "question": prompt,
        "answer": entry.cree_primary,
        "task_type": "word_translation",
        "difficulty": difficulty,
        "info": _base_info(entry, "word_translation", entry.cree_primary),
        "metadata": _task_metadata(entry, "english_to_cree"),
    }


def build_backward_task(entry: NormalizedCreeEntry) -> dict[str, object]:
    """Cree-to-English reverse lookup task."""
    prompt_lines = [
        "Give the English meaning of this Cree word or phrase.",
        f"Cree: {entry.cree_primary}",
    ]
    if entry.part_of_speech:
        prompt_lines.append(f"Part of speech: {entry.part_of_speech}")
    if entry.variants:
        prompt_lines.append("Related variants: " + ", ".join(entry.variants))

    prompt = "\n".join(prompt_lines) + "\n"
    difficulty = estimate_difficulty(entry)
    info = _base_info(entry, "reverse_translation", entry.english_headword)
    info["special_chars"] = []
    return {
        "id": f"{entry.entry_id}_cree_to_english",
        "task_id": f"{entry.entry_id}_cree_to_english",
        "prompt": prompt,
        "question": prompt,
        "answer": entry.english_headword,
        "task_type": "reverse_translation",
        "difficulty": difficulty,
        "info": info,
        "metadata": _task_metadata(entry, "cree_to_english"),
    }


def build_rl_tasks(entry: NormalizedCreeEntry) -> list[dict[str, object]]:
    """Return the core forward and backward RL tasks."""
    return [build_forward_task(entry), build_backward_task(entry)]


def build_qa_pairs(entry: NormalizedCreeEntry) -> list[dict[str, object]]:
    """Return plain Q&A records for non-RL dataset consumers."""
    difficulty = estimate_difficulty(entry)
    return [
        {
            "id": f"{entry.entry_id}_qa_english_to_cree",
            "question": f"What is the Cree for '{entry.english_headword}'?",
            "answer": entry.cree_primary,
            "direction": "english_to_cree",
            "metadata": _task_metadata(entry, "english_to_cree") | {"difficulty": difficulty},
        },
        {
            "id": f"{entry.entry_id}_qa_cree_to_english",
            "question": f"What is the English meaning of '{entry.cree_primary}'?",
            "answer": entry.english_headword,
            "direction": "cree_to_english",
            "metadata": _task_metadata(entry, "cree_to_english") | {"difficulty": difficulty},
        },
    ]
