"""Anchored synthetic Q&A expansion for Cree dictionary training data."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any, Iterable

from dakota_extraction.datasets.cree_task_generator import CREE_ORTHOGRAPHY_CHARS


EXPANSION_SOURCE = "deterministic_cree_expander_v1"


@dataclass(frozen=True)
class ExpansionConfig:
    """Configuration for deterministic anchored Q&A expansion."""

    variants_per_record: int = 6
    include_original: bool = True


@dataclass(frozen=True)
class ExpansionTemplate:
    template_id: str
    family: str
    text: str


ENGLISH_TO_CREE_TEMPLATES = (
    ExpansionTemplate(
        "dictionary_lookup",
        "lookup",
        "In the 1865 Cree dictionary, what Cree form is listed for the English headword '{term}'?",
    ),
    ExpansionTemplate(
        "learner_dialogue",
        "dialogue",
        'A learner asks, "How do I say {term} in Cree?" Answer with only the dictionary form.',
    ),
    ExpansionTemplate(
        "cloze_lookup",
        "cloze",
        "Complete this dictionary lookup.\nEnglish headword: {term}\nCree form:",
    ),
    ExpansionTemplate(
        "flashcard",
        "flashcard",
        "Flashcard front: {term}\nFlashcard back, in Cree:",
    ),
    ExpansionTemplate(
        "source_page",
        "source_grounded",
        "Using the source entry on page {page}, translate the English headword '{term}' into Cree.",
    ),
    ExpansionTemplate(
        "answer_only",
        "lookup",
        "Give the Cree dictionary equivalent for '{term}'. Do not explain or add alternatives.",
    ),
    ExpansionTemplate(
        "community_review",
        "review_sheet",
        "For a community review worksheet, fill in the Cree answer for English '{term}'.",
    ),
    ExpansionTemplate(
        "long_context",
        "context_expansion",
        "The dictionary entry gives an English headword and a Cree form. Headword: {term}. "
        "Write the Cree form exactly as extracted.",
    ),
)

CREE_TO_ENGLISH_TEMPLATES = (
    ExpansionTemplate(
        "reverse_dictionary_lookup",
        "lookup",
        "In the 1865 Cree dictionary, what English meaning is listed for the Cree form '{term}'?",
    ),
    ExpansionTemplate(
        "reverse_learner_dialogue",
        "dialogue",
        'A learner sees the Cree form "{term}". What English meaning should they write?',
    ),
    ExpansionTemplate(
        "reverse_cloze_lookup",
        "cloze",
        "Complete this reverse dictionary lookup.\nCree form: {term}\nEnglish meaning:",
    ),
    ExpansionTemplate(
        "reverse_flashcard",
        "flashcard",
        "Flashcard front, in Cree: {term}\nFlashcard back, in English:",
    ),
    ExpansionTemplate(
        "reverse_source_page",
        "source_grounded",
        "Using the source entry on page {page}, give the English meaning of Cree '{term}'.",
    ),
    ExpansionTemplate(
        "reverse_answer_only",
        "lookup",
        "Give only the English dictionary meaning for the Cree word or phrase '{term}'.",
    ),
    ExpansionTemplate(
        "reverse_community_review",
        "review_sheet",
        "For a community review worksheet, fill in the English answer for Cree '{term}'.",
    ),
    ExpansionTemplate(
        "reverse_long_context",
        "context_expansion",
        "The dictionary entry gives a Cree form and an English meaning. Cree form: {term}. "
        "Write the English meaning exactly as extracted.",
    ),
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read JSONL records from disk."""
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSONL record") from exc
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    """Write JSONL records to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def expand_qa_records(
    rows: Iterable[dict[str, Any]],
    config: ExpansionConfig | None = None,
) -> list[dict[str, Any]]:
    """Expand plain Cree Q&A rows into anchored synthetic prompt variants."""
    cfg = config or ExpansionConfig()
    if cfg.variants_per_record < 0:
        raise ValueError("variants_per_record must be >= 0")

    expanded: list[dict[str, Any]] = []
    for row in rows:
        source_id = str(row.get("id") or "").strip()
        if not source_id:
            raise ValueError("Every source Q&A row must include an id.")
        if cfg.include_original:
            expanded.append(_original_anchor_row(row))
        expanded.extend(_synthetic_rows_for_record(row, cfg.variants_per_record))
    return expanded


def qa_rows_to_rl_tasks(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert expanded Q&A rows into Tinker-compatible RL task rows."""
    return [_qa_row_to_rl_task(row) for row in rows]


def write_expansion_outputs(
    *,
    qa_input: Path,
    qa_output: Path,
    rl_output: Path,
    report_output: Path,
    config: ExpansionConfig | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Read anchored Q&A rows, write expanded Q&A/RL JSONL files, and report counts."""
    source_rows = read_jsonl(qa_input)
    if limit is not None:
        if limit < 0:
            raise ValueError("limit must be >= 0")
        source_rows = source_rows[:limit]

    cfg = config or ExpansionConfig()
    qa_rows = expand_qa_records(source_rows, cfg)
    rl_rows = qa_rows_to_rl_tasks(qa_rows)
    report = _build_report(source_rows, qa_rows, rl_rows, cfg)

    write_jsonl(qa_output, qa_rows)
    write_jsonl(rl_output, rl_rows)
    report_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _original_anchor_row(row: dict[str, Any]) -> dict[str, Any]:
    copied = deepcopy(row)
    metadata = _base_metadata(row, synthetic=False)
    metadata["expansion_template"] = "original_anchor"
    metadata["expansion_family"] = "anchor"
    copied["metadata"] = metadata
    return copied


def _synthetic_rows_for_record(row: dict[str, Any], variants_per_record: int) -> list[dict[str, Any]]:
    direction = _direction(row)
    templates = ENGLISH_TO_CREE_TEMPLATES if direction == "english_to_cree" else CREE_TO_ENGLISH_TEMPLATES
    source_id = str(row["id"])
    term = _source_term(row)
    page = _page(row)
    synthetic_rows: list[dict[str, Any]] = []

    for index in range(variants_per_record):
        template = templates[index % len(templates)]
        cycle = index // len(templates)
        question = template.text.format(term=term, page=page)
        if cycle:
            question = f"{question}\nUse answer-only format. Expansion cycle: {cycle + 1}."
        metadata = _base_metadata(row, synthetic=True)
        metadata.update(
            {
                "expansion_template": template.template_id,
                "expansion_family": template.family,
                "expansion_index": index,
                "source_term": term,
            }
        )
        synthetic_rows.append(
            {
                "id": f"{source_id}__synthetic_{index + 1:02d}_{template.template_id}",
                "question": question,
                "answer": row["answer"],
                "direction": direction,
                "metadata": metadata,
            }
        )
    return synthetic_rows


def _qa_row_to_rl_task(row: dict[str, Any]) -> dict[str, Any]:
    direction = _direction(row)
    task_type = "word_translation" if direction == "english_to_cree" else "reverse_translation"
    answer = str(row.get("answer") or "").strip()
    if not answer:
        raise ValueError(f"{row.get('id', '<missing id>')}: answer is required")

    metadata = dict(row.get("metadata") or {})
    difficulty = str(row.get("difficulty") or metadata.get("difficulty") or "easy")
    info = {
        "rule_id": metadata.get("entry_id") or metadata.get("anchor_qa_id") or row.get("id"),
        "task_type": task_type,
        "difficulty": difficulty,
        "direction": direction,
        "page": metadata.get("page"),
        "verification_pattern": re.escape(answer),
        "special_chars": _special_chars(answer),
        "required_affixes": [],
        "hints": [answer],
        "orthography_chars": sorted(CREE_ORTHOGRAPHY_CHARS),
        "expansion_template": metadata.get("expansion_template"),
        "expansion_family": metadata.get("expansion_family"),
    }
    task_id = _rl_task_id(str(row["id"]))
    return {
        "id": task_id,
        "task_id": task_id,
        "prompt": str(row["question"]).rstrip() + "\n",
        "question": str(row["question"]).rstrip() + "\n",
        "answer": answer,
        "task_type": task_type,
        "difficulty": difficulty,
        "info": info,
        "metadata": metadata,
    }


def _build_report(
    source_rows: list[dict[str, Any]],
    qa_rows: list[dict[str, Any]],
    rl_rows: list[dict[str, Any]],
    config: ExpansionConfig,
) -> dict[str, Any]:
    direction_counts: dict[str, int] = {}
    synthetic_records = 0
    for row in qa_rows:
        direction = _direction(row)
        direction_counts[direction] = direction_counts.get(direction, 0) + 1
        if (row.get("metadata") or {}).get("synthetic_expansion") is True:
            synthetic_records += 1

    return {
        "expansion_source": EXPANSION_SOURCE,
        "input_records": len(source_rows),
        "output_qa_records": len(qa_rows),
        "output_rl_records": len(rl_rows),
        "synthetic_records": synthetic_records,
        "include_original": config.include_original,
        "variants_per_record": config.variants_per_record,
        "direction_counts": direction_counts,
    }


def _base_metadata(row: dict[str, Any], *, synthetic: bool) -> dict[str, Any]:
    metadata = dict(row.get("metadata") or {})
    metadata.update(
        {
            "anchor_qa_id": row.get("id"),
            "synthetic_expansion": synthetic,
            "answer_anchor": "dictionary_extraction",
            "expansion_source": EXPANSION_SOURCE,
        }
    )
    return metadata


def _direction(row: dict[str, Any]) -> str:
    direction = str(row.get("direction") or (row.get("metadata") or {}).get("direction") or "").strip()
    if direction not in {"english_to_cree", "cree_to_english"}:
        raise ValueError(f"{row.get('id', '<missing id>')}: unsupported direction {direction!r}")
    return direction


def _page(row: dict[str, Any]) -> str:
    page = (row.get("metadata") or {}).get("page")
    return str(page) if page is not None else "the source page"


def _source_term(row: dict[str, Any]) -> str:
    metadata = row.get("metadata") or {}
    for key in ("source_term", "english_headword", "cree_primary"):
        candidate = str(metadata.get(key) or "").strip()
        if candidate:
            return candidate

    question = str(row.get("question") or "")
    quoted = re.search(r"'([^']+)'|\"([^\"]+)\"", question)
    if quoted:
        return next(group for group in quoted.groups() if group)

    labelled = re.search(r"(?:English|Cree)\s*:\s*([^\n]+)", question, flags=re.IGNORECASE)
    if labelled:
        return labelled.group(1).strip()

    raise ValueError(f"{row.get('id', '<missing id>')}: could not infer source term from question")


def _special_chars(text: str) -> list[str]:
    return sorted(set(str(text)) & CREE_ORTHOGRAPHY_CHARS)


def _rl_task_id(row_id: str) -> str:
    return row_id.replace("_qa_", "_rl_")
