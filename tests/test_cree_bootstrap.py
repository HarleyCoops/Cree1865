from __future__ import annotations

import json
from pathlib import Path

import fitz

from dakota_extraction.core.cree_reverse_extraction_prompt import build_cree_reverse_extraction_prompt
from dakota_extraction.datasets.cree_training_dataset_builder import CreeTrainingDatasetBuilder
from dakota_extraction.datasets.cree_task_generator import NormalizedCreeEntry, build_rl_tasks
from dakota_extraction.profiles.cree1865 import CREE1865_PROFILE
from dakota_extraction.tools.pdf_ingest import render_pdf_pages


def _write_extraction(path: Path, page_number: int, entries: list[dict[str, object]]) -> None:
    payload = {
        "layout": "two-column",
        "entries": entries,
        "metadata": {
            "page_number": page_number,
            "image_path": f"page_{page_number:03d}.png",
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_cree_profile_boundaries_are_pinned() -> None:
    assert CREE1865_PROFILE.front_matter_end_pdf_page == 28
    assert CREE1865_PROFILE.dictionary_start_pdf_page == 29
    assert CREE1865_PROFILE.reverse_dictionary_transition_pdf_page == 211
    assert CREE1865_PROFILE.reverse_dictionary_start_pdf_page == 212
    assert CREE1865_PROFILE.reverse_dictionary_transition_printed_page == 183
    assert CREE1865_PROFILE.reverse_dictionary_start_printed_page == 184
    assert CREE1865_PROFILE.dictionary_direction == "english_to_cree"


def test_pdf_ingest_renders_selected_pages(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    document = fitz.open()
    for index in range(2):
        page = document.new_page()
        page.insert_text((72, 72), f"Sample page {index + 1}")
    document.save(pdf_path)
    document.close()

    output_dir = tmp_path / "rendered"
    rendered = render_pdf_pages(pdf_path, output_dir, start_page=1, end_page=2, dpi=72)

    assert len(rendered) == 2
    assert rendered[0].name == "page_001.png"
    assert rendered[1].exists()


def test_cree_dataset_builder_end_to_end(tmp_path: Path) -> None:
    extraction_dir = tmp_path / "extracted"
    dataset_dir = tmp_path / "datasets"
    extraction_dir.mkdir()

    _write_extraction(
        extraction_dir / "page_029.json",
        29,
        [
            {
                "entry_id": "page_029_entry_001",
                "english_headword": "Abandon",
                "cree_primary": "Wapi-nao",
                "part_of_speech": "v. t.",
                "cree_variants": ["-num", "nuku-tao", "-tum"],
                "example_pairs": [],
                "confidence": 0.82,
            },
            {
                "entry_id": "page_029_entry_002",
                "english_headword": "Backbone",
                "cree_primary": "Oospiskwunikun",
                "part_of_speech": "n.",
                "cree_variants": ["owikun"],
                "usage_notes": "See Spine",
                "example_pairs": [],
                "confidence": 0.87,
            },
        ],
    )

    builder = CreeTrainingDatasetBuilder(
        extraction_dir=str(extraction_dir),
        output_dir=str(dataset_dir),
        validation_split=0.5,
    )
    stats = builder.build_all_datasets()

    assert stats.raw_entries == 2
    assert stats.deduplicated_entries == 2
    assert (dataset_dir / "sft_train.jsonl").exists()
    assert (dataset_dir / "sft_valid.jsonl").exists()
    assert (dataset_dir / "rl_tasks_all.jsonl").exists()
    assert (dataset_dir / "qa_pairs_all.jsonl").exists()

    rl_records = [
        json.loads(line)
        for line in (dataset_dir / "rl_tasks_all.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    directions = {record["metadata"]["direction"] for record in rl_records}
    assert directions == {"english_to_cree", "cree_to_english"}
    assert all(record["question"] == record["prompt"] for record in rl_records)
    assert {record["task_type"] for record in rl_records} == {"word_translation", "reverse_translation"}
    assert all("info" in record for record in rl_records)

    qa_records = [
        json.loads(line)
        for line in (dataset_dir / "qa_pairs_all.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert {record["direction"] for record in qa_records} == {"english_to_cree", "cree_to_english"}


def test_cree_dataset_builder_allows_retained_loanword_entries(tmp_path: Path) -> None:
    extraction_dir = tmp_path / "extracted"
    dataset_dir = tmp_path / "datasets"
    extraction_dir.mkdir()

    _write_extraction(
        extraction_dir / "page_036.json",
        36,
        [
            {
                "entry_id": "page_036_entry_001",
                "english_headword": "Ark",
                "cree_primary": "Ark",
                "part_of_speech": "n.",
                "cree_variants": ["napikwan", "mistaoot"],
                "usage_notes": "English loanword listed first, followed by Cree forms.",
                "example_pairs": [
                    {
                        "english": "The ark of the covenant",
                        "cree": "nuskoomitoowemistikoowut",
                    }
                ],
                "confidence": 0.93,
            }
        ],
    )

    builder = CreeTrainingDatasetBuilder(
        extraction_dir=str(extraction_dir),
        output_dir=str(dataset_dir),
        validation_split=0.5,
    )
    stats = builder.build_all_datasets()

    assert stats.raw_entries == 1
    assert stats.deduplicated_entries == 1
    assert stats.identical_language_pairs == 1
    assert (dataset_dir / "rl_tasks_all.jsonl").exists()


def test_cree_dataset_builder_replaces_placeholder_entry_ids(tmp_path: Path) -> None:
    extraction_dir = tmp_path / "extracted"
    dataset_dir = tmp_path / "datasets"
    extraction_dir.mkdir()

    _write_extraction(
        extraction_dir / "page_212.json",
        212,
        [
            {
                "entry_id": "auto-generated later",
                "english_headword": "Fish",
                "cree_primary": "Kinosayw",
                "part_of_speech": "n.",
                "example_pairs": [],
                "confidence": 0.9,
            },
            {
                "entry_id": "auto-generated later",
                "english_headword": "Fire",
                "cree_primary": "Iskootayw",
                "part_of_speech": "n.",
                "example_pairs": [],
                "confidence": 0.9,
            },
        ],
    )

    builder = CreeTrainingDatasetBuilder(
        extraction_dir=str(extraction_dir),
        output_dir=str(dataset_dir),
        validation_split=0.5,
    )
    builder.build_all_datasets()

    rl_records = [
        json.loads(line)
        for line in (dataset_dir / "rl_tasks_all.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    ids = [record["id"] for record in rl_records]

    assert len(ids) == len(set(ids))
    assert ids == [
        "page_212_entry_001_english_to_cree",
        "page_212_entry_001_cree_to_english",
        "page_212_entry_002_english_to_cree",
        "page_212_entry_002_cree_to_english",
    ]


def test_cree_dataset_builder_scopes_local_numeric_entry_ids_by_page(tmp_path: Path) -> None:
    extraction_dir = tmp_path / "extracted"
    dataset_dir = tmp_path / "datasets"
    extraction_dir.mkdir()

    for page_number, headword, cree in [(29, "Abandon", "Wapi-nao"), (30, "Arrow", "Atush")]:
        _write_extraction(
            extraction_dir / f"page_{page_number:03d}.json",
            page_number,
            [
                {
                    "entry_id": "1",
                    "english_headword": headword,
                    "cree_primary": cree,
                    "part_of_speech": "n.",
                    "example_pairs": [],
                    "confidence": 0.9,
                },
            ],
        )

    builder = CreeTrainingDatasetBuilder(
        extraction_dir=str(extraction_dir),
        output_dir=str(dataset_dir),
        validation_split=0.5,
    )
    builder.build_all_datasets()

    rl_records = [
        json.loads(line)
        for line in (dataset_dir / "rl_tasks_all.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    ids = [record["id"] for record in rl_records]

    assert len(ids) == len(set(ids))
    assert ids == [
        "page_029_entry_001_english_to_cree",
        "page_029_entry_001_cree_to_english",
        "page_030_entry_001_english_to_cree",
        "page_030_entry_001_cree_to_english",
    ]


def test_cree_reverse_prompt_preserves_normalized_schema_direction() -> None:
    prompt = build_cree_reverse_extraction_prompt(page_context="First full Part II page.")

    assert '"dictionary_direction": "cree_to_english"' in prompt
    assert "Cree headword" in prompt
    assert '"cree_primary": "Cree entry headword exactly as printed"' in prompt
    assert '"english_headword": "English gloss or gloss phrase exactly as printed"' in prompt


def test_cree_rl_tasks_are_tinker_compatible() -> None:
    entry = NormalizedCreeEntry(
        entry_id="page_029_entry_001",
        english_headword="A good man",
        cree_primary="a meyosit napao",
        part_of_speech="phrase",
        qualifiers=[],
        variants=["payuk napao"],
        examples=["a good man => a meyosit napao"],
        usage_notes=None,
        page_number=29,
        source_image="page_029.png",
        confidence=0.95,
    )

    forward, backward = build_rl_tasks(entry)

    assert forward["question"] == forward["prompt"]
    assert forward["task_type"] == "word_translation"
    assert forward["difficulty"] in {"easy", "medium", "hard"}
    assert forward["info"]["task_type"] == "word_translation"
    assert forward["info"]["special_chars"] == sorted(set("a meyosit napao") & set(forward["info"]["orthography_chars"]))
    assert forward["metadata"]["direction"] == "english_to_cree"

    assert backward["question"] == backward["prompt"]
    assert backward["task_type"] == "reverse_translation"
    assert backward["info"]["task_type"] == "reverse_translation"
    assert backward["info"]["special_chars"] == []
    assert backward["metadata"]["direction"] == "cree_to_english"
