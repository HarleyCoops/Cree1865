from __future__ import annotations

from collections import Counter

from scripts.cree.create_balanced_cree_showcase_rl import build_balanced_showcase


def _row(row_id: str, difficulty: str, answer: str, special_chars: list[str] | None = None) -> dict:
    return {
        "id": row_id,
        "task_id": row_id,
        "question": f"Translate test row {row_id}.",
        "answer": answer,
        "task_type": "word_translation",
        "difficulty": difficulty,
        "info": {
            "difficulty": difficulty,
            "task_type": "word_translation",
            "special_chars": special_chars or [],
            "required_affixes": [],
            "verification_pattern": answer,
        },
        "metadata": {
            "entry_id": row_id,
            "page": 100,
        },
    }


def test_balanced_showcase_covers_full_dataset_and_weights_priority_rows() -> None:
    rows = [
        _row("easy_plain", "easy", "misko"),
        _row("easy_orthography", "easy", "w\u0101pis", ["\u0101"]),
        _row("medium_plain", "medium", "maskwa"),
        _row("hard_plain", "hard", "mitoni"),
        _row("hard_orthography", "hard", "n\u0113hiyaw", ["\u0113"]),
    ]

    balanced, report = build_balanced_showcase(rows, seed=1865)

    counts = Counter(row["metadata"]["showcase_original_id"] for row in balanced)
    assert counts == {
        "easy_plain": 1,
        "easy_orthography": 2,
        "medium_plain": 4,
        "hard_plain": 8,
        "hard_orthography": 8,
    }
    assert len({row["id"] for row in balanced}) == len(balanced)
    assert {row["id"] for row in rows}.issubset({row["id"] for row in balanced})
    assert balanced[0]["metadata"]["showcase_tier"].startswith("hard")
    assert report["input_records"] == 5
    assert report["output_records"] == 23


def test_empty_required_affixes_do_not_make_easy_rows_priority() -> None:
    rows = [
        _row("easy_empty_affixes", "easy", "plain-ascii"),
    ]

    balanced, report = build_balanced_showcase(rows, seed=1865)

    assert len(balanced) == 1
    assert balanced[0]["metadata"]["showcase_weight_reason"] == "baseline"
    assert report["orthography_rich_input_records"] == 0


def test_balanced_showcase_tops_up_underrepresented_task_types() -> None:
    word = _row("word_orthography", "easy", "w\u0101pis", ["\u0101"])
    word["task_type"] = "word_translation"
    word["info"]["task_type"] = "word_translation"
    reverse = _row("reverse_plain", "easy", "bear")
    reverse["task_type"] = "reverse_translation"
    reverse["info"]["task_type"] = "reverse_translation"

    balanced, report = build_balanced_showcase([word, reverse], seed=1865)

    task_counts = Counter(row["task_type"] for row in balanced)
    assert task_counts == {"word_translation": 2, "reverse_translation": 2}
    assert report["task_balance_added_records"] == 1
    assert any((row["metadata"].get("showcase_task_balance_extra") is True) for row in balanced)
