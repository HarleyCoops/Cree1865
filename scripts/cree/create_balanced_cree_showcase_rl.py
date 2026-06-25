#!/usr/bin/env python3
"""Create a weighted, ordered Cree RL showcase dataset from full dictionary tasks."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
from copy import deepcopy
import json
import random
from pathlib import Path
from typing import Any, Iterable

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = ROOT_DIR / "data" / "cree_goal_run_20260624_full_dictionary" / "training_datasets"
DEFAULT_INPUT = DEFAULT_DATA_DIR / "rl_tasks_all.jsonl"
DEFAULT_OUTPUT = DEFAULT_DATA_DIR / "rl_tasks_balanced_cree_showcase.jsonl"
DEFAULT_EVAL_OUTPUT = DEFAULT_DATA_DIR / "rl_tasks_balanced_cree_showcase_eval.jsonl"
DEFAULT_REPORT = DEFAULT_DATA_DIR / "rl_tasks_balanced_cree_showcase_report.json"

DIFFICULTY_MULTIPLIERS = {
    "hard": 8,
    "medium": 4,
    "easy": 1,
}
ORTHOGRAPHY_EASY_MULTIPLIER = 2
BUCKET_ORDER = [
    "hard_orthography",
    "medium_orthography",
    "hard",
    "easy_orthography",
    "medium",
    "hard_orthography",
    "medium_orthography",
    "easy",
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
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
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _listish(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _has_non_ascii(value: Any) -> bool:
    return any(ord(char) > 127 for char in str(value or ""))


def _difficulty(row: dict[str, Any]) -> str:
    info = row.get("info") or {}
    return str(row.get("difficulty") or info.get("difficulty") or "easy").lower()


def _task_type(row: dict[str, Any]) -> str:
    info = row.get("info") or {}
    return str(row.get("task_type") or row.get("task") or info.get("task_type") or "unknown")


def _source_id(row: dict[str, Any], index: int) -> str:
    return str(row.get("id") or row.get("task_id") or f"cree_row_{index:06d}")


def is_orthography_rich(row: dict[str, Any]) -> bool:
    """Return True when the answer or verifier target contains Cree-specific marks.

    Empty required_affixes are intentionally ignored. They are not orthography
    evidence and should never inflate the row weight.
    """

    info = row.get("info") or {}
    special_chars = [str(char).strip() for char in _listish(info.get("special_chars"))]
    if any(special_chars):
        return True
    return _has_non_ascii(row.get("answer")) or _has_non_ascii(info.get("verification_pattern"))


def tier_for_row(row: dict[str, Any]) -> str:
    difficulty = _difficulty(row)
    orthography = is_orthography_rich(row)
    if difficulty == "hard":
        return "hard_orthography" if orthography else "hard"
    if difficulty == "medium":
        return "medium_orthography" if orthography else "medium"
    return "easy_orthography" if orthography else "easy"


def multiplier_for_row(row: dict[str, Any]) -> int:
    difficulty = _difficulty(row)
    if difficulty == "easy" and is_orthography_rich(row):
        return ORTHOGRAPHY_EASY_MULTIPLIER
    return DIFFICULTY_MULTIPLIERS.get(difficulty, 1)


def _weight_reason(row: dict[str, Any]) -> str:
    difficulty = _difficulty(row)
    orthography = is_orthography_rich(row)
    if difficulty in {"hard", "medium"} and orthography:
        return f"{difficulty}+orthography"
    if difficulty in {"hard", "medium"}:
        return difficulty
    if orthography:
        return "orthography"
    return "baseline"


def _priority_score(row: dict[str, Any]) -> float:
    difficulty_score = {"hard": 3.0, "medium": 2.0, "easy": 1.0}.get(_difficulty(row), 1.0)
    orthography_score = 1.0 if is_orthography_rich(row) else 0.0
    answer_len_score = min(len(str(row.get("answer") or "")) / 80.0, 1.0)
    return round(difficulty_score + orthography_score + answer_len_score, 4)


def _copy_for_showcase(
    row: dict[str, Any],
    index: int,
    repeat_index: int,
    weight_total: int,
    *,
    task_balance_extra: bool = False,
) -> dict[str, Any]:
    source_id = _source_id(row, index)
    copied = deepcopy(row)
    if repeat_index == 0:
        showcase_id = source_id
    else:
        showcase_id = f"{source_id}__showcase_r{repeat_index:02d}"
    copied["id"] = showcase_id
    copied["task_id"] = showcase_id

    metadata = dict(copied.get("metadata") or {})
    metadata.update(
        {
            "showcase_original_id": source_id,
            "showcase_repeat_index": repeat_index,
            "showcase_tier": tier_for_row(row),
            "showcase_weight_reason": _weight_reason(row),
            "showcase_weight_total": weight_total,
            "showcase_priority": _priority_score(row),
        }
    )
    if task_balance_extra:
        metadata["showcase_task_balance_extra"] = True
        metadata["showcase_weight_reason"] = f"{metadata['showcase_weight_reason']}+task_balance"
    copied["metadata"] = metadata
    return copied


def _ordered_from_buckets(buckets: dict[str, deque[dict[str, Any]]]) -> list[dict[str, Any]]:
    ordered: list[dict[str, Any]] = []
    while any(buckets.values()):
        moved = False
        for bucket_name in BUCKET_ORDER:
            bucket = buckets.get(bucket_name)
            if bucket:
                ordered.append(bucket.popleft())
                moved = True
        if not moved:
            break
    return ordered


def _summarize(rows: list[dict[str, Any]], *, seed: int, input_records: int) -> dict[str, Any]:
    first_window = rows[: min(512, len(rows))]
    return {
        "seed": seed,
        "input_records": input_records,
        "output_records": len(rows),
        "input_to_output_ratio": round(len(rows) / input_records, 4) if input_records else 0.0,
        "difficulty_multipliers": DIFFICULTY_MULTIPLIERS,
        "easy_orthography_multiplier": ORTHOGRAPHY_EASY_MULTIPLIER,
        "bucket_order": BUCKET_ORDER,
        "difficulty_counts": dict(Counter(_difficulty(row) for row in rows)),
        "task_type_counts": dict(Counter(_task_type(row) for row in rows)),
        "tier_counts": dict(Counter((row.get("metadata") or {}).get("showcase_tier", tier_for_row(row)) for row in rows)),
        "weight_reason_counts": dict(
            Counter((row.get("metadata") or {}).get("showcase_weight_reason", _weight_reason(row)) for row in rows)
        ),
        "orthography_rich_output_records": sum(1 for row in rows if is_orthography_rich(row)),
        "first_512_difficulty_counts": dict(Counter(_difficulty(row) for row in first_window)),
        "first_512_tier_counts": dict(
            Counter((row.get("metadata") or {}).get("showcase_tier", tier_for_row(row)) for row in first_window)
        ),
        "first_512_orthography_rich_records": sum(1 for row in first_window if is_orthography_rich(row)),
    }


def build_balanced_showcase(rows: list[dict[str, Any]], *, seed: int = 1865) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rng = random.Random(seed)
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    next_repeat_index: dict[str, int] = {}

    for index, row in enumerate(rows):
        weight_total = multiplier_for_row(row)
        for repeat_index in range(weight_total):
            copied = _copy_for_showcase(row, index, repeat_index, weight_total)
            buckets[tier_for_row(row)].append(copied)
        next_repeat_index[_source_id(row, index)] = weight_total

    task_balance_added_records = _add_task_balance_records(rows, buckets, next_repeat_index)

    shuffled_buckets: dict[str, deque[dict[str, Any]]] = {}
    for bucket_name, bucket_rows in buckets.items():
        rng.shuffle(bucket_rows)
        shuffled_buckets[bucket_name] = deque(bucket_rows)

    ordered = _ordered_from_buckets(shuffled_buckets)
    report = _summarize(ordered, seed=seed, input_records=len(rows))
    report["orthography_rich_input_records"] = sum(1 for row in rows if is_orthography_rich(row))
    report["input_difficulty_counts"] = dict(Counter(_difficulty(row) for row in rows))
    report["input_task_type_counts"] = dict(Counter(_task_type(row) for row in rows))
    report["task_balance_added_records"] = task_balance_added_records
    return ordered, report


def _add_task_balance_records(
    rows: list[dict[str, Any]],
    buckets: dict[str, list[dict[str, Any]]],
    next_repeat_index: dict[str, int],
) -> int:
    task_counts = Counter(_task_type(row) for bucket_rows in buckets.values() for row in bucket_rows)
    if len(task_counts) < 2:
        return 0

    max_count = max(task_counts.values())
    indexed_by_task: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for index, row in enumerate(rows):
        indexed_by_task[_task_type(row)].append((index, row))

    added = 0
    for task_type, current_count in sorted(task_counts.items()):
        deficit = max_count - current_count
        if deficit <= 0:
            continue
        candidates = sorted(
            indexed_by_task[task_type],
            key=lambda item: (_priority_score(item[1]), multiplier_for_row(item[1])),
            reverse=True,
        )
        if not candidates:
            continue
        for extra_index in range(deficit):
            index, row = candidates[extra_index % len(candidates)]
            source_id = _source_id(row, index)
            repeat_index = next_repeat_index[source_id]
            next_repeat_index[source_id] += 1
            copied = _copy_for_showcase(
                row,
                index,
                repeat_index,
                multiplier_for_row(row),
                task_balance_extra=True,
            )
            buckets[tier_for_row(row)].append(copied)
            added += 1
    return added


def build_eval_probe(rows: list[dict[str, Any]], *, max_records: int = 1024, seed: int = 1865) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    buckets: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for index, row in enumerate(rows):
        buckets[tier_for_row(row)].append((index, row))

    queued: dict[str, deque[tuple[int, dict[str, Any]]]] = {}
    for bucket_name, bucket_rows in buckets.items():
        rng.shuffle(bucket_rows)
        queued[bucket_name] = deque(bucket_rows)

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    while len(selected) < max_records and any(queued.values()):
        moved = False
        for bucket_name in BUCKET_ORDER:
            bucket = queued.get(bucket_name)
            if not bucket:
                continue
            index, row = bucket.popleft()
            source_id = _source_id(row, index)
            if source_id in seen:
                continue
            copied = deepcopy(row)
            metadata = dict(copied.get("metadata") or {})
            metadata.update(
                {
                    "showcase_eval_probe": True,
                    "showcase_original_id": source_id,
                    "showcase_tier": tier_for_row(row),
                }
            )
            copied["metadata"] = metadata
            selected.append(copied)
            seen.add(source_id)
            moved = True
            if len(selected) >= max_records:
                break
        if not moved:
            break
    return selected


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Source full dictionary RL JSONL.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Weighted showcase train JSONL.")
    parser.add_argument("--eval-output", type=Path, default=DEFAULT_EVAL_OUTPUT, help="Unweighted diagnostic eval JSONL.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Dataset summary report JSON.")
    parser.add_argument("--eval-records", type=int, default=1024, help="Rows to write to the diagnostic eval probe.")
    parser.add_argument("--seed", type=int, default=1865, help="Deterministic shuffle/interleave seed.")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    rows = read_jsonl(args.input)
    balanced, report = build_balanced_showcase(rows, seed=args.seed)
    eval_probe = build_eval_probe(rows, max_records=args.eval_records, seed=args.seed)

    report["eval_probe_records"] = len(eval_probe)
    report["eval_probe_tier_counts"] = dict(Counter(tier_for_row(row) for row in eval_probe))
    report["eval_probe_difficulty_counts"] = dict(Counter(_difficulty(row) for row in eval_probe))

    write_jsonl(args.output, balanced)
    write_jsonl(args.eval_output, eval_probe)
    write_report(args.report, report)

    print(json.dumps(report, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
