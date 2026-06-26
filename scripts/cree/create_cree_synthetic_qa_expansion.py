#!/usr/bin/env python3
"""Create anchored synthetic Cree Q&A and RL expansion files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dakota_extraction.datasets.cree_synthetic_qa_expander import ExpansionConfig, write_expansion_outputs


DEFAULT_DATA_DIR = ROOT_DIR / "data" / "cree_goal_run_20260624_full_dictionary" / "training_datasets"
DEFAULT_QA_INPUT = DEFAULT_DATA_DIR / "qa_pairs_all.jsonl"
DEFAULT_QA_OUTPUT = DEFAULT_DATA_DIR / "synthetic_qa_pairs_all.jsonl"
DEFAULT_RL_OUTPUT = DEFAULT_DATA_DIR / "rl_tasks_synthetic_expanded.jsonl"
DEFAULT_REPORT = DEFAULT_DATA_DIR / "synthetic_qa_expansion_report.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qa-input", type=Path, default=DEFAULT_QA_INPUT, help="Anchored source Q&A JSONL.")
    parser.add_argument("--qa-output", type=Path, default=DEFAULT_QA_OUTPUT, help="Expanded Q&A JSONL output.")
    parser.add_argument("--rl-output", type=Path, default=DEFAULT_RL_OUTPUT, help="Expanded RL JSONL output.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Expansion report JSON output.")
    parser.add_argument("--variants-per-record", type=int, default=6, help="Synthetic variants to add per Q&A row.")
    parser.add_argument(
        "--expansion-only",
        action="store_true",
        help="Omit original Q&A anchors from the output files.",
    )
    parser.add_argument("--limit", type=int, help="Optional source row cap for smoke tests.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = ExpansionConfig(
        variants_per_record=args.variants_per_record,
        include_original=not args.expansion_only,
    )
    report = write_expansion_outputs(
        qa_input=args.qa_input,
        qa_output=args.qa_output,
        rl_output=args.rl_output,
        report_output=args.report,
        config=config,
        limit=args.limit,
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
