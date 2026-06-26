#!/usr/bin/env python3
"""Export compact Cree1865 metric traces for the Three.js companion view."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "dakota_rl_training" / "outputs" / "cree1865_synthetic_expansion_v1" / "metrics.jsonl"
DEFAULT_OUTPUT = ROOT / "visualizations" / "cree3d" / "public" / "cree_metrics.json"
RUN_URL = "https://wandb.ai/christian-cooper-us/thinking-machines-qwen3-30b/runs/hda2wqhl"


METRICS = {
    "reward_mean": "reward/mean",
    "target_cree_char_f1": "slice/english_to_cree/char_f1",
    "target_english_char_f1": "slice/cree_to_english/char_f1",
    "target_cree_orthography": "slice/english_to_cree/orthography",
    "target_english_orthography": "slice/cree_to_english/orthography",
    "target_cree_exact": "slice/english_to_cree/exact",
    "target_cree_containment": "slice/english_to_cree/target_containment",
    "entropy": "optim/entropy",
    "kl_v1": "optim/kl_sample_train_v1",
    "kl_v2": "optim/kl_sample_train_v2",
    "loss_sum": "loss:sum",
    "tokens_per_sec": "perf/tokens_per_sec",
    "samples_per_sec": "perf/samples_per_sec",
    "step_time": "perf/step_time",
    "expert_token_utilization": "e_frac_with_tokens:mean",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def numeric(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def make_point(row: dict[str, Any]) -> dict[str, Any]:
    point: dict[str, Any] = {
        "step": int(row.get("step") or 0),
        "done_frac": numeric(row.get("progress/done_frac")),
    }
    for name, source_key in METRICS.items():
        point[name] = numeric(row.get(source_key))
    return point


def summarize(points: list[dict[str, Any]]) -> dict[str, Any]:
    latest = points[-1] if points else {}
    return {
        "rows": len(points),
        "latest_step": latest.get("step"),
        "latest_done_frac": latest.get("done_frac"),
        "latest_reward_mean": latest.get("reward_mean"),
        "latest_entropy": latest.get("entropy"),
        "run_url": RUN_URL,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    rows = read_jsonl(args.input)
    points = [make_point(row) for row in rows if "step" in row]
    payload = {
        "run": {
            "name": "cree1865-synthetic-expansion-v1",
            "id": "hda2wqhl",
            "url": RUN_URL,
            "planned_steps": 800,
        },
        "metrics": METRICS,
        "summary": summarize(points),
        "points": points,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
