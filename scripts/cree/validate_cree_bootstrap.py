"""Offline synthetic validation for the Cree1865 extraction scaffolding."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pypdf import PdfReader

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dakota_extraction.datasets.cree_training_dataset_builder import CreeTrainingDatasetBuilder
from dakota_extraction.profiles.cree1865 import CREE1865_PROFILE
from dakota_extraction.tools.pdf_ingest import render_pdf_pages, summarize_rendered_pages


SAMPLE_EXTRACTIONS = {
    29: [
        {
            "english_headword": "Abandon",
            "cree_primary": "Wapi-nao",
            "part_of_speech": "v. t.",
            "cree_variants": ["-num", "nuku-tao", "-tum"],
            "qualifiers": [],
            "example_pairs": [],
            "usage_notes": None,
            "confidence": 0.82,
        },
        {
            "english_headword": "Abash",
            "cree_primary": "Wuwanatuchehao",
            "part_of_speech": "v. t.",
            "cree_variants": [],
            "qualifiers": [],
            "example_pairs": [],
            "usage_notes": None,
            "confidence": 0.84,
        },
    ],
    40: [
        {
            "english_headword": "Backbone",
            "cree_primary": "Oospiskwunikun",
            "part_of_speech": "n.",
            "cree_variants": ["owikun"],
            "qualifiers": [],
            "example_pairs": [],
            "usage_notes": "See Spine",
            "confidence": 0.87,
        },
        {
            "english_headword": "Bank",
            "cree_primary": "Ispuchow",
            "part_of_speech": "n. (high)",
            "cree_variants": ["ispetowukow", "keskutowukow"],
            "qualifiers": ["steep"],
            "example_pairs": [
                {"english": "He goes up the bank", "cree": "koosepamuchewāo"},
                {"english": "He takes it down the bank", "cree": "nasepātumik"},
            ],
            "usage_notes": None,
            "confidence": 0.79,
        },
    ],
    100: [
        {
            "english_headword": "Freeze",
            "cree_primary": "Muskowuti-māo",
            "part_of_speech": "v. t.",
            "cree_variants": ["-tum", "ākwuchehāo", "-tow"],
            "qualifiers": [],
            "example_pairs": [],
            "usage_notes": None,
            "confidence": 0.8,
        },
        {
            "english_headword": "Friend",
            "cree_primary": "Mitootām",
            "part_of_speech": "n.",
            "cree_variants": ["netootām"],
            "qualifiers": [],
            "example_pairs": [
                {"english": "My friend", "cree": "netootām"},
                {"english": "A good friend", "cree": "meyootootām"},
            ],
            "usage_notes": None,
            "confidence": 0.85,
        },
    ],
}


def _write_sample_extractions(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for page_number, entries in SAMPLE_EXTRACTIONS.items():
        payload = {
            "layout": CREE1865_PROFILE.column_layout,
            "entries": [
                {"entry_id": f"page_{page_number:03d}_entry_{index+1:03d}", **entry}
                for index, entry in enumerate(entries)
            ],
            "metadata": {
                "page_number": page_number,
                "image_path": f"page_{page_number:03d}.png",
            },
        }
        path = output_dir / f"page_{page_number:03d}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        paths.append(path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Cree1865 extraction scaffolding offline.")
    parser.add_argument("--pdf", default=CREE1865_PROFILE.pdf_path, help="Path to the Cree PDF.")
    parser.add_argument(
        "--output-root",
        default="data/cree_validation",
        help="Output directory for rendered pages and validation artifacts.",
    )
    parser.add_argument("--dpi", type=int, default=180, help="Rendering DPI for inspection pages.")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    output_root = Path(args.output_root)
    render_dir = output_root / "inspection_pages"
    extraction_dir = output_root / "sample_extracted"
    dataset_dir = output_root / "sample_datasets"

    reader = PdfReader(str(pdf_path))
    page_count = len(reader.pages)
    if page_count != CREE1865_PROFILE.page_count:
        raise ValueError(
            f"Unexpected page count for {pdf_path}: {page_count} (expected {CREE1865_PROFILE.page_count})"
        )

    pages_to_render = sorted(
        {
            *CREE1865_PROFILE.sample_front_matter_pages,
            *CREE1865_PROFILE.sample_dictionary_pages,
            *CREE1865_PROFILE.sample_reverse_dictionary_pages,
        }
    )
    rendered = []
    for page_number in pages_to_render:
        rendered.extend(
            render_pdf_pages(
                pdf_path,
                render_dir,
                start_page=page_number,
                end_page=page_number,
                dpi=args.dpi,
            )
        )

    extraction_paths = _write_sample_extractions(extraction_dir)
    builder = CreeTrainingDatasetBuilder(
        extraction_dir=str(extraction_dir),
        output_dir=str(dataset_dir),
        validation_split=0.33,
    )
    stats = builder.build_all_datasets()

    report = {
        "profile": CREE1865_PROFILE.to_dict(),
        "resolved_pdf_path": str(pdf_path.resolve()),
        "render_summary": summarize_rendered_pages(rendered),
        "rendered_pages": [path.name for path in rendered],
        "sample_extractions": [path.name for path in extraction_paths],
        "dataset_stats": stats.to_dict(),
        "notes": [
            "Part I English-Cree begins at PDF page 29.",
            "The Part II transition lands at printed page 183 / PDF page 211, with first full Cree-English entries on printed page 184 / PDF page 212.",
            "This validation uses offline sample entries derived from manual inspection pages.",
            "Current structured extraction scaffolding is schema-ready for Part I English-Cree pages only.",
            "Use scripts/cree/run_cree_pipeline.py for live local extraction against the PDF.",
        ],
    }

    output_root.mkdir(parents=True, exist_ok=True)
    report_path = output_root / "bootstrap_validation_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Cree synthetic validation complete.")
    print(f"Rendered pages: {len(rendered)}")
    print(f"Sample extraction files: {len(extraction_paths)}")
    print(f"SFT/RL dataset output: {dataset_dir}")
    print(f"Validation report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
