"""Dataset builder for Cree dictionary extractions."""

from __future__ import annotations

import json
import random
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from dakota_extraction.datasets.cree_task_generator import (
    NormalizedCreeEntry,
    build_rl_tasks,
    build_sft_example,
)


def _ensure_list(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if item]
    return [str(value).strip()]


def _flatten_examples(value: Any) -> List[str]:
    if not value:
        return []
    examples: list[str] = []
    for item in value if isinstance(value, list) else [value]:
        if isinstance(item, dict):
            english = str(item.get("english") or "").strip()
            cree = str(item.get("cree") or "").strip()
            if english and cree:
                examples.append(f"{english} => {cree}")
            elif english:
                examples.append(english)
            elif cree:
                examples.append(cree)
        elif item:
            examples.append(str(item).strip())
    return examples


@dataclass
class CreeDatasetBuildStats:
    total_pages: int = 0
    raw_entries: int = 0
    deduplicated_entries: int = 0
    rejected_entries: int = 0
    identical_language_pairs: int = 0
    missing_fields: int = 0
    multi_variant_entries: int = 0
    sample_for_review: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_pages": self.total_pages,
            "raw_entries": self.raw_entries,
            "deduplicated_entries": self.deduplicated_entries,
            "rejected_entries": self.rejected_entries,
            "identical_language_pairs": self.identical_language_pairs,
            "missing_fields": self.missing_fields,
            "multi_variant_entries": self.multi_variant_entries,
        }


class CreeTrainingDatasetBuilder:
    """Build SFT and RL datasets from structured Cree dictionary extractions."""

    def __init__(
        self,
        extraction_dir: str = "data/extracted_cree",
        output_dir: str = "data/training_datasets_cree",
        validation_split: float = 0.05,
    ):
        self.extraction_dir = Path(extraction_dir)
        self.output_dir = Path(output_dir)
        self.validation_split = validation_split
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._last_stats: Optional[CreeDatasetBuildStats] = None

    def build_all_datasets(self) -> CreeDatasetBuildStats:
        """Load extractions, validate them, and materialize SFT/RL artifacts."""
        extraction_files = sorted(self.extraction_dir.glob("page_*.json"))
        if not extraction_files:
            raise FileNotFoundError(
                f"No extraction files found in {self.extraction_dir}. Run the extraction step first."
            )

        entries = self._collect_entries(extraction_files)
        deduped_entries = self._deduplicate(entries)
        stats = CreeDatasetBuildStats(
            total_pages=len(extraction_files),
            raw_entries=len(entries),
            deduplicated_entries=len(deduped_entries),
        )

        valid_entries, rejected_entries = self._partition_entries(deduped_entries)
        stats.rejected_entries = len(rejected_entries)
        stats.missing_fields = len(rejected_entries)
        if not valid_entries:
            raise ValueError("No valid entries remained after filtering incomplete Cree dictionary rows.")

        self._validate_entries(valid_entries, stats)
        self._write_sft_datasets(valid_entries)
        self._write_rl_tasks(valid_entries)
        stats.sample_for_review = self._write_spot_check(valid_entries)
        self._write_rejected_entries(rejected_entries)
        self._write_report(stats)
        self._last_stats = stats
        return stats

    def generate_statistics(self) -> Dict[str, Any]:
        """Return the most recent build statistics."""
        if self._last_stats is None:
            return {"total_pages": len(list(self.extraction_dir.glob("page_*.json"))), "total_entries": 0}
        return self._last_stats.to_dict()

    def _collect_entries(self, extraction_files: Iterable[Path]) -> List[NormalizedCreeEntry]:
        entries: list[NormalizedCreeEntry] = []
        for path in extraction_files:
            payload = json.loads(path.read_text(encoding="utf-8"))
            page_meta = payload.get("metadata", {})
            page_number = page_meta.get("page_number")
            source_image = page_meta.get("image_path")
            for index, item in enumerate(payload.get("entries", [])):
                entry_id = item.get("entry_id") or f"page_{page_number or 0:03d}_entry_{index+1:03d}"
                entries.append(
                    NormalizedCreeEntry(
                        entry_id=entry_id,
                        english_headword=str(
                            item.get("english_headword") or item.get("headword") or ""
                        ).strip(),
                        cree_primary=str(
                            item.get("cree_primary") or item.get("cree") or ""
                        ).strip(),
                        part_of_speech=item.get("part_of_speech") or item.get("pos"),
                        qualifiers=_ensure_list(item.get("qualifiers")),
                        variants=_ensure_list(item.get("cree_variants") or item.get("variants")),
                        examples=_flatten_examples(item.get("example_pairs") or item.get("examples")),
                        usage_notes=item.get("usage_notes") or item.get("notes"),
                        page_number=page_number,
                        source_image=source_image,
                        confidence=item.get("confidence"),
                    )
                )
        return entries

    def _canonical_key(self, entry: NormalizedCreeEntry) -> str:
        text = f"{entry.english_headword}|{entry.part_of_speech or ''}|{entry.cree_primary}"
        normalized = unicodedata.normalize("NFD", text).lower()
        return "".join(ch for ch in normalized if ch.isalnum())

    def _deduplicate(self, entries: List[NormalizedCreeEntry]) -> List[NormalizedCreeEntry]:
        merged: dict[str, NormalizedCreeEntry] = {}
        for entry in entries:
            key = self._canonical_key(entry) or entry.entry_id
            if key not in merged:
                merged[key] = entry
                continue
            existing = merged[key]
            for variant in entry.variants:
                if variant and variant not in existing.variants:
                    existing.variants.append(variant)
            for example in entry.examples:
                if example and example not in existing.examples:
                    existing.examples.append(example)
            if not existing.usage_notes and entry.usage_notes:
                existing.usage_notes = entry.usage_notes
        return list(merged.values())

    def _validate_entries(self, entries: List[NormalizedCreeEntry], stats: CreeDatasetBuildStats) -> None:
        identical = [
            entry for entry in entries
            if entry.english_headword.strip().lower() == entry.cree_primary.strip().lower()
            and entry.english_headword.strip()
        ]
        multi_variant = [entry for entry in entries if entry.variants]

        stats.identical_language_pairs = len(identical)
        stats.multi_variant_entries = len(multi_variant)

    def _partition_entries(
        self,
        entries: List[NormalizedCreeEntry],
    ) -> tuple[List[NormalizedCreeEntry], List[Dict[str, Any]]]:
        valid_entries: list[NormalizedCreeEntry] = []
        rejected_entries: list[Dict[str, Any]] = []
        for entry in entries:
            if entry.english_headword and entry.cree_primary:
                valid_entries.append(entry)
                continue
            rejected_entries.append(
                {
                    "entry_id": entry.entry_id,
                    "english_headword": entry.english_headword,
                    "cree_primary": entry.cree_primary,
                    "part_of_speech": entry.part_of_speech,
                    "variants": entry.variants,
                    "examples": entry.examples,
                    "usage_notes": entry.usage_notes,
                    "page_number": entry.page_number,
                    "source_image": entry.source_image,
                    "reason": "missing_english_or_cree_primary",
                }
            )
        return valid_entries, rejected_entries

    def _write_sft_datasets(self, entries: List[NormalizedCreeEntry]) -> None:
        rng = random.Random(42)
        shuffled = entries[:]
        rng.shuffle(shuffled)
        split_index = int(len(shuffled) * (1 - self.validation_split))
        self._write_jsonl(
            self.output_dir / "sft_train.jsonl",
            (build_sft_example(entry) for entry in shuffled[:split_index]),
        )
        self._write_jsonl(
            self.output_dir / "sft_valid.jsonl",
            (build_sft_example(entry) for entry in shuffled[split_index:]),
        )

    def _write_rl_tasks(self, entries: List[NormalizedCreeEntry]) -> None:
        self._write_jsonl(
            self.output_dir / "rl_tasks_all.jsonl",
            (task for entry in entries for task in build_rl_tasks(entry)),
        )

    def _write_spot_check(self, entries: List[NormalizedCreeEntry]) -> List[Dict[str, Any]]:
        if not entries:
            return []
        rng = random.Random(171)
        sample_size = max(1, round(len(entries) * 0.1))
        sampled = rng.sample(entries, k=min(sample_size, len(entries)))
        payload = [
            {
                "entry_id": entry.entry_id,
                "english_headword": entry.english_headword,
                "cree_primary": entry.cree_primary,
                "part_of_speech": entry.part_of_speech,
                "variants": entry.variants,
                "page_number": entry.page_number,
            }
            for entry in sampled
        ]
        (self.output_dir / "manual_spot_check.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return payload

    def _write_report(self, stats: CreeDatasetBuildStats) -> None:
        (self.output_dir / "dataset_report.json").write_text(
            json.dumps({"stats": stats.to_dict()}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _write_rejected_entries(self, rejected_entries: List[Dict[str, Any]]) -> None:
        (self.output_dir / "rejected_entries.json").write_text(
            json.dumps(rejected_entries, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _write_jsonl(self, path: Path, records: Iterable[Dict[str, Any]]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
