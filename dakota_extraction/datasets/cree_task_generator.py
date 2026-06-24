"""Helpers for building Cree SFT and RL tasks from extracted dictionary rows."""

from __future__ import annotations

from dataclasses import dataclass


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

    return {
        "prompt": "\n".join(prompt_lines) + "\n",
        "answer": entry.cree_primary,
        "metadata": {
            "direction": "english_to_cree",
            "entry_id": entry.entry_id,
            "difficulty": estimate_difficulty(entry),
            "page": entry.page_number,
            "source_image": entry.source_image,
        },
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

    return {
        "prompt": "\n".join(prompt_lines) + "\n",
        "answer": entry.english_headword,
        "metadata": {
            "direction": "cree_to_english",
            "entry_id": entry.entry_id,
            "difficulty": estimate_difficulty(entry),
            "page": entry.page_number,
            "source_image": entry.source_image,
        },
    }


def build_rl_tasks(entry: NormalizedCreeEntry) -> list[dict[str, object]]:
    """Return the core forward and backward RL tasks."""
    return [build_forward_task(entry), build_backward_task(entry)]
