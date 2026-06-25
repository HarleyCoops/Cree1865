"""Prime/verifiers environment for Watkins 1865 Cree dictionary QA tasks."""

from __future__ import annotations

import json
import logging
import math
import random
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Sequence
from urllib.request import urlopen

import verifiers as vf
from datasets import Dataset

logger = logging.getLogger(__name__)

PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[2]
DEFAULT_DATASET = REPO_ROOT / "data" / "cree_goal_run_20260624_full_dictionary" / "training_datasets" / "rl_tasks_all.jsonl"

DEFAULT_SYSTEM_PROMPT = (
    "You are a careful Cree language assistant working from Watkins' 1865 Cree dictionary. "
    "Answer the user's question directly and concisely. Preserve Cree orthography exactly, "
    "including macrons, acutes, circumflexes, hyphens, and apostrophes. Do not invent unsupported forms."
)

CREE_ORTHOGRAPHY_CHARS = set(
    "āēīōūâêîôûáéíóúĀĒĪŌŪÂÊÎÔÛÁÉÍÓÚ-'’"
)
WORD_CHARS = set("-'’")


def _normalize(text: Any) -> str:
    value = "" if text is None else str(text)
    value = unicodedata.normalize("NFC", value)
    value = value.replace("`", " ").replace("*", " ")
    value = value.replace("“", '"').replace("”", '"').replace("’", "'")
    return re.sub(r"\s+", " ", value.lower()).strip()


def _compact(text: Any) -> str:
    chars: list[str] = []
    for char in _normalize(text):
        if char.isalnum() or char in WORD_CHARS:
            chars.append(char)
    return "".join(chars)


def _char_f1(prediction: str, target: str) -> float:
    pred_chars = Counter(_compact(prediction))
    target_chars = Counter(_compact(target))
    if not target_chars:
        return 0.0
    overlap = sum(min(pred_chars[ch], target_chars[ch]) for ch in target_chars)
    precision = overlap / max(sum(pred_chars.values()), 1)
    recall = overlap / max(sum(target_chars.values()), 1)
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def _orthography_marks(text: Any) -> list[str]:
    normalized = unicodedata.normalize("NFC", "" if text is None else str(text))
    return [char for char in normalized if char in CREE_ORTHOGRAPHY_CHARS]


def _extract_response(completion: Any) -> str:
    if isinstance(completion, str):
        return completion
    if isinstance(completion, Sequence):
        for message in reversed(completion):
            if isinstance(message, dict) and message.get("role") == "assistant":
                return str(message.get("content") or "")
        if completion and isinstance(completion[-1], dict):
            return str(completion[-1].get("content") or "")
    return str(completion or "")


def _read_jsonl(path_or_url: str | Path) -> list[dict[str, Any]]:
    if isinstance(path_or_url, str) and path_or_url.startswith(("http://", "https://")):
        with urlopen(path_or_url, timeout=60) as response:
            lines = response.read().decode("utf-8").splitlines()
    else:
        lines = Path(path_or_url).expanduser().read_text(encoding="utf-8").splitlines()

    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            logger.warning("Skipping malformed JSONL line %d: %s", line_no, exc)
            continue
        if (row.get("question") or row.get("prompt")) and row.get("answer"):
            rows.append(row)
    return rows


def _prepare_records(raw_rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for idx, row in enumerate(raw_rows):
        info = dict(row.get("info") or {})
        metadata = dict(row.get("metadata") or {})
        question = str(row.get("question") or row.get("prompt") or "").strip()
        answer = str(row.get("answer") or "").strip()
        if not question or not answer:
            continue
        task_type = str(row.get("task_type") or info.get("task_type") or "dictionary_lookup")
        difficulty = str(row.get("difficulty") or info.get("difficulty") or "medium")
        direction = metadata.get("direction") or info.get("direction")
        entry_id = metadata.get("entry_id") or info.get("rule_id")
        page = metadata.get("page") or info.get("page")
        prepared_info: dict[str, Any] = {
            **info,
            "task_type": task_type,
            "difficulty": difficulty,
            "direction": direction,
            "entry_id": entry_id,
            "page": page,
            "verification_pattern": info.get("verification_pattern"),
            "hints": info.get("hints") or [],
            "special_chars": info.get("special_chars") or [],
            "orthography_chars": info.get("orthography_chars") or [],
            "metadata": metadata,
        }
        records.append(
            {
                "id": row.get("id") or row.get("task_id") or f"cree1865_{idx:05d}",
                "question": question,
                "answer": answer,
                "task": task_type,
                "info": prepared_info,
            }
        )
    return records


class CreeDictionaryRubric(vf.Rubric):
    """Continuous reward for Watkins 1865 Cree dictionary lookup tasks."""

    def __init__(self) -> None:
        super().__init__(
            funcs=[
                self.exact_reward,
                self.target_containment_reward,
                self.orthography_reward,
                self.char_f1_reward,
                self.length_reward,
            ],
            weights=[0.20, 0.25, 0.20, 0.20, 0.15],
        )

    async def exact_reward(self, completion: Any, answer: str, **_: Any) -> float:
        return float(_normalize(_extract_response(completion)) == _normalize(answer))

    async def target_containment_reward(self, completion: Any, answer: str, **_: Any) -> float:
        response = _normalize(_extract_response(completion))
        target = _normalize(answer)
        if not target:
            return 0.0
        if target in response:
            return 1.0
        compact_target = _compact(answer)
        compact_response = _compact(response)
        return float(bool(compact_target and compact_target in compact_response))

    async def orthography_reward(self, completion: Any, answer: str, **_: Any) -> float:
        expected_marks = _orthography_marks(answer)
        if not expected_marks:
            return 0.0
        response_marks = Counter(_orthography_marks(_extract_response(completion)))
        expected_counts = Counter(expected_marks)
        hits = sum(min(response_marks[char], count) for char, count in expected_counts.items())
        return hits / sum(expected_counts.values())

    async def char_f1_reward(self, completion: Any, answer: str, **_: Any) -> float:
        return float(_char_f1(_extract_response(completion), answer))

    async def length_reward(self, completion: Any, answer: str, **_: Any) -> float:
        response = _extract_response(completion).strip()
        if not response:
            return 0.0
        answer_len = max(len(answer.strip()), 1)
        ratio = len(response) / answer_len
        if 0.5 <= ratio <= 2.0:
            return 1.0
        distance = min(abs(math.log(max(ratio, 1e-6) / 0.5)), abs(math.log(max(ratio, 1e-6) / 2.0)))
        return max(0.0, 1.0 - distance / 2.0)


def build_dataset(
    dataset_path: str | Path | None = None,
    max_examples: int = -1,
    seed: int = 42,
    shuffle: bool = True,
) -> Dataset:
    source = dataset_path or DEFAULT_DATASET
    if not (isinstance(source, str) and source.startswith(("http://", "https://"))) and not Path(source).exists():
        raise FileNotFoundError(f"Cree dataset not found: {source}")

    records = _prepare_records(_read_jsonl(source))
    if not records:
        raise ValueError("No usable Cree dictionary QA records found")
    if shuffle:
        random.Random(seed).shuffle(records)
    if max_examples and max_examples > 0:
        records = records[:max_examples]
    return Dataset.from_list(records)


def _split_dataset(dataset: Dataset, eval_fraction: float, eval_examples: int, seed: int) -> tuple[Dataset, Dataset | None]:
    if eval_fraction <= 0 or len(dataset) < 2:
        return dataset, None
    split = dataset.train_test_split(test_size=eval_fraction, seed=seed)
    eval_dataset = split["test"]
    if eval_examples and eval_examples > 0:
        eval_dataset = eval_dataset.select(range(min(eval_examples, len(eval_dataset))))
    return split["train"], eval_dataset


def load_environment(
    dataset_path: str | Path | None = None,
    max_examples: int = -1,
    eval_fraction: float = 0.10,
    eval_examples: int = 128,
    system_prompt: str | None = None,
    sampling_args: dict[str, Any] | None = None,
    seed: int = 42,
    shuffle: bool = True,
) -> vf.Environment:
    dataset = build_dataset(
        dataset_path=dataset_path,
        max_examples=max_examples,
        seed=seed,
        shuffle=shuffle,
    )
    train_dataset, eval_dataset = _split_dataset(dataset, eval_fraction, eval_examples, seed)
    prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
    env = vf.SingleTurnEnv(
        dataset=train_dataset,
        eval_dataset=eval_dataset,
        system_prompt=prompt,
        rubric=CreeDictionaryRubric(),
        sampling_args=sampling_args,
        message_type="chat",
    )
    env.system_prompt = prompt
    return env
