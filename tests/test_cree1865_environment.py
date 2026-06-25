from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "environments" / "cree1865_dictionary_qa"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from cree1865_dictionary_qa import environment as cree_environment
from cree1865_dictionary_qa.environment import CreeDictionaryRubric, build_dataset, load_environment


def _write_cree_tasks(path: Path, count: int = 10) -> None:
    rows: list[dict[str, Any]] = []
    for idx in range(count):
        page = 29 + idx
        answer = f"Wapi-nao-{idx}"
        rows.append(
            {
                "id": f"page_{page:03d}_entry_001_english_to_cree",
                "task_id": f"page_{page:03d}_entry_001_english_to_cree",
                "prompt": f"Translate the following English headword into Cree.\nEnglish: Headword {idx}\n",
                "question": f"Translate the following English headword into Cree.\nEnglish: Headword {idx}\n",
                "answer": answer,
                "task_type": "word_translation",
                "difficulty": "easy",
                "info": {
                    "rule_id": f"page_{page:03d}_entry_001",
                    "task_type": "word_translation",
                    "difficulty": "easy",
                    "verification_pattern": answer,
                    "special_chars": [],
                    "required_affixes": [],
                    "hints": [answer],
                    "orthography_chars": ["a", "e", "i", "o", "u", "ā", "ē", "ī", "ō", "ū"],
                },
                "metadata": {
                    "direction": "english_to_cree",
                    "entry_id": f"page_{page:03d}_entry_001",
                    "page": page,
                },
            }
        )
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")


async def _score_total(rubric: CreeDictionaryRubric, completion: Any, answer: str, info: dict[str, Any]) -> float:
    total = 0.0
    weights = getattr(rubric, "weights", [1.0] * len(rubric.funcs))
    for weight, func in zip(weights, rubric.funcs):
        total += weight * await func(completion=completion, answer=answer, info=info)
    return total


def test_cree_rubric_scores_exact_answer_above_bad_answer() -> None:
    rubric = CreeDictionaryRubric()
    answer = "Wāpi-nāo"
    info = {"special_chars": ["ā"], "required_affixes": []}
    good = [{"role": "assistant", "content": answer}]
    bad = [{"role": "assistant", "content": "I do not know."}]

    good_score = asyncio.run(_score_total(rubric, good, answer, info))
    bad_score = asyncio.run(_score_total(rubric, bad, answer, info))

    assert good_score > bad_score


def test_cree_rubric_has_no_free_affix_channel() -> None:
    rubric = CreeDictionaryRubric()
    answer = "Wāpi-nāo"
    info = {"special_chars": ["ā"], "required_affixes": []}
    bad = [{"role": "assistant", "content": "I do not know."}]

    assert not any("affix" in func.__name__.lower() for func in rubric.funcs)
    bad_score = asyncio.run(_score_total(rubric, bad, answer, info))
    assert bad_score < 0.5


def test_cree_dataset_builder_preserves_fields_and_shuffles_before_cap(tmp_path: Path) -> None:
    dataset_path = tmp_path / "rl_tasks_all.jsonl"
    _write_cree_tasks(dataset_path, count=10)

    dataset = build_dataset(dataset_path=dataset_path, max_examples=3, seed=1865, shuffle=True)

    assert len(dataset) == 3
    first_pages = [row["info"]["page"] for row in dataset]
    assert first_pages != [29, 30, 31]
    row = dataset[0]
    assert row["question"]
    assert row["answer"]
    assert row["task"] == "word_translation"
    assert row["info"]["task_type"] == "word_translation"
    assert row["info"]["direction"] == "english_to_cree"
    assert row["info"]["page"] >= 29


def test_cree_dataset_builder_uses_packaged_smoke_data_when_repo_data_is_absent(
    monkeypatch: Any, tmp_path: Path
) -> None:
    monkeypatch.setattr(cree_environment, "DEFAULT_DATASET", tmp_path / "missing.jsonl")

    dataset = cree_environment.build_dataset(max_examples=1, shuffle=False)

    assert len(dataset) == 1
    row = dataset[0]
    assert row["question"]
    assert row["answer"]
    assert row["info"]["task_type"] == "dictionary_lookup"


def test_cree_load_environment_builds_train_and_eval_split(tmp_path: Path) -> None:
    dataset_path = tmp_path / "rl_tasks_all.jsonl"
    _write_cree_tasks(dataset_path, count=20)

    env = load_environment(dataset_path=dataset_path, max_examples=12, eval_fraction=0.25, eval_examples=3, seed=1865)

    assert len(env.dataset) == 9
    assert env.eval_dataset is not None
    assert len(env.eval_dataset) == 3
    assert "Cree" in env.system_prompt


def test_cree_load_environment_accepts_prime_eval_kwargs(tmp_path: Path) -> None:
    dataset_path = tmp_path / "rl_tasks_all.jsonl"
    _write_cree_tasks(dataset_path, count=8)

    env = load_environment(
        dataset_path=dataset_path,
        max_examples=4,
        eval_fraction=0,
        max_turns=5,
    )

    assert len(env.dataset) == 4


def test_tinker_cree_adapter_uses_cree_rubric_not_dakota() -> None:
    from dakota_rl_training.tinker_integration.cree import create_cree_rubric

    rubric = create_cree_rubric()

    assert rubric.__class__.__name__ == "CreeDictionaryRubric"


def test_tinker_train_accepts_explicit_cree_rubric_name() -> None:
    from dakota_rl_training.tinker_train import build_argument_parser, build_dataset_builder

    args = build_argument_parser().parse_args(["--rubric-name", "cree"])
    builder = build_dataset_builder(args)

    assert builder.rubric_name == "cree"
