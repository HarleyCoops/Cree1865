from __future__ import annotations

import json
from pathlib import Path

import fitz

from dakota_extraction.datasets.cree_training_dataset_builder import CreeTrainingDatasetBuilder
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

    rl_records = [
        json.loads(line)
        for line in (dataset_dir / "rl_tasks_all.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    directions = {record["metadata"]["direction"] for record in rl_records}
    assert directions == {"english_to_cree", "cree_to_english"}


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
