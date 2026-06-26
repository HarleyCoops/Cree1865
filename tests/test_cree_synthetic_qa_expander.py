from __future__ import annotations

import json
import re
from pathlib import Path

from dakota_extraction.datasets.cree_synthetic_qa_expander import (
    ExpansionConfig,
    expand_qa_records,
    qa_rows_to_rl_tasks,
    read_jsonl,
    write_expansion_outputs,
)


def _qa_row(
    row_id: str,
    question: str,
    answer: str,
    direction: str,
    *,
    difficulty: str = "easy",
) -> dict[str, object]:
    return {
        "id": row_id,
        "question": question,
        "answer": answer,
        "direction": direction,
        "metadata": {
            "entry_id": row_id.removesuffix("_qa_english_to_cree").removesuffix("_qa_cree_to_english"),
            "difficulty": difficulty,
            "page": 29,
            "source_image": "rendered/page_029.png",
            "confidence": 0.92,
        },
    }


def test_cree_synthetic_expansion_preserves_anchored_answers() -> None:
    rows = [
        _qa_row(
            "page_029_entry_002_qa_english_to_cree",
            "What is the Cree for 'Abandon'?",
            "Wāpi-nāo",
            "english_to_cree",
        ),
        _qa_row(
            "page_029_entry_002_qa_cree_to_english",
            "What is the English meaning of 'Wāpi-nāo'?",
            "Abandon",
            "cree_to_english",
        ),
    ]

    expanded = expand_qa_records(rows, ExpansionConfig(variants_per_record=3, include_original=True))

    assert len(expanded) == 8
    assert len({row["id"] for row in expanded}) == len(expanded)

    by_anchor: dict[str, list[dict[str, object]]] = {}
    for row in expanded:
        anchor_id = str(row["metadata"]["anchor_qa_id"])
        by_anchor.setdefault(anchor_id, []).append(row)

    for source in rows:
        anchored_rows = by_anchor[str(source["id"])]
        assert len(anchored_rows) == 4
        assert {row["answer"] for row in anchored_rows} == {source["answer"]}
        assert {row["direction"] for row in anchored_rows} == {source["direction"]}
        assert any(row["metadata"]["synthetic_expansion"] is True for row in anchored_rows)
        assert any(row["metadata"]["synthetic_expansion"] is False for row in anchored_rows)
        assert len({row["question"] for row in anchored_rows}) == len(anchored_rows)


def test_cree_synthetic_expansion_rl_tasks_are_rubric_compatible() -> None:
    rows = [
        _qa_row(
            "page_029_entry_002_qa_english_to_cree",
            "What is the Cree for 'Abandon'?",
            "Wāpi-nāo",
            "english_to_cree",
            difficulty="medium",
        )
    ]

    expanded = expand_qa_records(rows, ExpansionConfig(variants_per_record=2, include_original=False))
    tasks = qa_rows_to_rl_tasks(expanded)

    assert len(tasks) == 2
    for task in tasks:
        assert task["prompt"] == task["question"]
        assert task["answer"] == "Wāpi-nāo"
        assert task["task_type"] == "word_translation"
        assert task["difficulty"] == "medium"
        assert task["info"]["verification_pattern"] == re.escape("Wāpi-nāo")
        assert task["info"]["special_chars"] == ["ā"]
        assert task["info"]["required_affixes"] == []
        assert task["metadata"]["synthetic_expansion"] is True
        assert task["metadata"]["answer_anchor"] == "dictionary_extraction"


def test_cree_synthetic_expansion_writes_qa_rl_and_report(tmp_path: Path) -> None:
    input_path = tmp_path / "qa_pairs_all.jsonl"
    qa_output = tmp_path / "synthetic_qa_pairs_all.jsonl"
    rl_output = tmp_path / "rl_tasks_synthetic_expanded.jsonl"
    report_output = tmp_path / "synthetic_qa_expansion_report.json"
    source_rows = [
        _qa_row(
            "page_029_entry_003_qa_english_to_cree",
            "What is the Cree for 'Abase'?",
            "Néti-nāo",
            "english_to_cree",
        )
    ]
    input_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in source_rows),
        encoding="utf-8",
    )

    report = write_expansion_outputs(
        qa_input=input_path,
        qa_output=qa_output,
        rl_output=rl_output,
        report_output=report_output,
        config=ExpansionConfig(variants_per_record=2, include_original=True),
    )

    qa_rows = read_jsonl(qa_output)
    rl_rows = read_jsonl(rl_output)
    persisted_report = json.loads(report_output.read_text(encoding="utf-8"))

    assert len(qa_rows) == 3
    assert len(rl_rows) == 3
    assert report["input_records"] == 1
    assert report["output_qa_records"] == 3
    assert report["output_rl_records"] == 3
    assert persisted_report == report
    assert {row["answer"] for row in qa_rows} == {"Néti-nāo"}
