"""Run the local Cree extraction pipeline on selected pages of CreeDictionary.pdf."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Sequence

from pypdf import PdfReader

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dakota_extraction.core.cree_extraction_prompt import build_cree_extraction_prompt
from dakota_extraction.core.cree_grammar_extraction_prompt import build_cree_grammar_extraction_prompt
from dakota_extraction.core.page_processor import PageProcessor
from dakota_extraction.datasets.cree_training_dataset_builder import CreeTrainingDatasetBuilder
from dakota_extraction.profiles.cree1865 import CREE1865_PROFILE
from dakota_extraction.tools.pdf_ingest import render_pdf_pages, summarize_rendered_pages


def _parse_page_list(values: Sequence[int] | None) -> list[int]:
    if not values:
        return []
    deduped = sorted({int(value) for value in values})
    if deduped and deduped[0] < 1:
        raise ValueError("Page numbers must be >= 1")
    return deduped


def _resolve_pages(
    explicit_pages: Sequence[int] | None,
    start_page: int | None,
    end_page: int | None,
    fallback_pages: Sequence[int],
) -> list[int]:
    if explicit_pages:
        return _parse_page_list(explicit_pages)
    if start_page is not None:
        final_page = end_page if end_page is not None else start_page
        if final_page < start_page:
            raise ValueError("end_page must be >= start_page")
        return list(range(start_page, final_page + 1))
    return list(fallback_pages)


def _render_selected_pages(
    pdf_path: Path,
    output_dir: Path,
    pages: Sequence[int],
    dpi: int,
) -> dict[int, Path]:
    rendered: dict[int, Path] = {}
    for page_number in pages:
        paths = render_pdf_pages(
            pdf_path,
            output_dir,
            start_page=page_number,
            end_page=page_number,
            dpi=dpi,
        )
        rendered[page_number] = paths[0]
    return rendered


def _write_report(report_path: Path, payload: dict[str, object]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _extract_selected_pages(
    *,
    rendered_pages: dict[int, Path],
    output_dir: Path,
    reasoning_dir: Path,
    prompt_builder,
    max_tokens: int,
) -> list[str]:
    processor = PageProcessor(
        output_dir=str(output_dir),
        reasoning_dir=str(reasoning_dir),
        prompt_builder=prompt_builder,
    )
    extracted_pages: list[str] = []
    for page_number, image_path in rendered_pages.items():
        processor.extract_page(
            image_path=image_path,
            page_number=page_number,
            max_tokens=max_tokens,
        )
        extracted_pages.append(f"page_{page_number:03d}.json")
    return extracted_pages


def _existing_extraction_pages(output_dir: Path) -> list[str]:
    return [path.name for path in sorted(output_dir.glob("page_*.json"))]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local Cree extraction pipeline on selected pages.")
    parser.add_argument("--pdf", default=CREE1865_PROFILE.pdf_path, help="Path to CreeDictionary.pdf")
    parser.add_argument("--output-root", default="data/cree_pipeline", help="Root directory for rendered pages and artifacts")
    parser.add_argument("--render-dpi", type=int, default=180, help="Rasterization DPI for rendered page images")
    parser.add_argument("--dictionary-pages", nargs="*", type=int, help="Explicit dictionary PDF pages to render/extract")
    parser.add_argument("--dictionary-start-page", type=int, help="Dictionary range start page")
    parser.add_argument("--dictionary-end-page", type=int, help="Dictionary range end page inclusive")
    parser.add_argument("--grammar-pages", nargs="*", type=int, help="Explicit grammar/front-matter PDF pages to render")
    parser.add_argument("--grammar-start-page", type=int, help="Grammar/front-matter range start page")
    parser.add_argument("--grammar-end-page", type=int, help="Grammar/front-matter range end page inclusive")
    parser.add_argument("--max-tokens", type=int, default=12000, help="Claude max output tokens per page")
    parser.add_argument("--skip-dictionary-extraction", action="store_true", help="Only render pages; do not call Anthropic")
    parser.add_argument("--skip-grammar-extraction", action="store_true", help="Render grammar pages only; do not call Anthropic")
    parser.add_argument("--skip-dataset-build", action="store_true", help="Do not build SFT/RL datasets from extracted JSON")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    dictionary_pages = _resolve_pages(
        args.dictionary_pages,
        args.dictionary_start_page,
        args.dictionary_end_page,
        CREE1865_PROFILE.sample_dictionary_pages,
    )
    grammar_pages = _resolve_pages(
        args.grammar_pages,
        args.grammar_start_page,
        args.grammar_end_page,
        CREE1865_PROFILE.sample_front_matter_pages,
    )

    output_root = Path(args.output_root)
    rendered_dictionary_dir = output_root / "rendered" / "dictionary_pages"
    rendered_grammar_dir = output_root / "rendered" / "grammar_pages"
    extracted_dictionary_dir = output_root / "extracted_dictionary"
    extracted_grammar_dir = output_root / "extracted_grammar"
    reasoning_dir = output_root / "reasoning_traces"
    dictionary_reasoning_dir = reasoning_dir / "dictionary"
    grammar_reasoning_dir = reasoning_dir / "grammar"
    dataset_dir = output_root / "training_datasets"
    report_path = output_root / "cree_pipeline_report.json"

    reader = PdfReader(str(pdf_path))
    page_count = len(reader.pages)

    print("Cree1865 local extraction pipeline")
    print(f"PDF: {pdf_path}")
    print(f"Page count: {page_count}")
    print(f"Dictionary pages: {dictionary_pages}")
    print(f"Grammar pages: {grammar_pages}")

    rendered_dictionary = _render_selected_pages(pdf_path, rendered_dictionary_dir, dictionary_pages, args.render_dpi)
    rendered_grammar = _render_selected_pages(pdf_path, rendered_grammar_dir, grammar_pages, args.render_dpi)

    extracted_dictionary_pages: list[str] = []
    extracted_grammar_pages: list[str] = []
    extraction_mode = "render_only"
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set; rendered pages are ready for a later live extraction pass.")
    else:
        extraction_mode = "anthropic_live"
        if args.skip_dictionary_extraction:
            print("Skipping dictionary extraction by request.")
        else:
            extracted_dictionary_pages = _extract_selected_pages(
                rendered_pages=rendered_dictionary,
                output_dir=extracted_dictionary_dir,
                reasoning_dir=dictionary_reasoning_dir,
                prompt_builder=lambda: build_cree_extraction_prompt(
                    page_context=(
                        "This is a Part I English-to-Cree dictionary page. "
                        "Treat English headwords as the source side and Cree forms as the target side."
                    )
                ),
                max_tokens=args.max_tokens,
            )
        if args.skip_grammar_extraction:
            print("Skipping grammar extraction by request.")
        else:
            extracted_grammar_pages = _extract_selected_pages(
                rendered_pages=rendered_grammar,
                output_dir=extracted_grammar_dir,
                reasoning_dir=grammar_reasoning_dir,
                prompt_builder=lambda: build_cree_grammar_extraction_prompt(
                    page_context=(
                        "This page is from the front matter or grammar section of the same Cree source. "
                        "Extract only rules and aligned examples that can later become verifiable RL tasks."
                    )
                ),
                max_tokens=args.max_tokens,
            )

    dataset_stats: dict[str, object] | None = None
    if args.skip_dataset_build:
        print("Skipping dataset build by request.")
    elif extracted_dictionary_dir.exists() and list(extracted_dictionary_dir.glob("page_*.json")):
        builder = CreeTrainingDatasetBuilder(
            extraction_dir=str(extracted_dictionary_dir),
            output_dir=str(dataset_dir),
        )
        dataset_stats = builder.build_all_datasets().to_dict()
        print(f"Built Cree datasets at {dataset_dir}")
    else:
        print("No extracted dictionary JSON found; dataset build skipped.")

    reported_dictionary_pages = extracted_dictionary_pages or _existing_extraction_pages(extracted_dictionary_dir)
    reported_grammar_pages = extracted_grammar_pages or _existing_extraction_pages(extracted_grammar_dir)

    report = {
        "profile": CREE1865_PROFILE.to_dict(),
        "resolved_pdf_path": str(pdf_path.resolve()),
        "page_count": page_count,
        "dictionary_pages": dictionary_pages,
        "grammar_pages": grammar_pages,
        "rendered_dictionary": summarize_rendered_pages(rendered_dictionary.values()),
        "rendered_grammar": summarize_rendered_pages(rendered_grammar.values()),
        "extraction_mode": extraction_mode,
        "extracted_dictionary_pages": reported_dictionary_pages,
        "extracted_grammar_pages": reported_grammar_pages,
        "dataset_stats": dataset_stats,
        "notes": [
            "This report reflects the local single-source PDF only: CreeDictionary.pdf.",
            "Dictionary extraction currently targets Part I English-to-Cree pages with a dedicated Cree schema.",
            "Grammar extraction now runs live on selected front-matter pages and saves raw rule JSON for later RL-gym conversion.",
            "scripts/cree/validate_cree_bootstrap.py remains an offline synthetic validation helper; it is not live extraction.",
        ],
    }
    _write_report(report_path, report)
    print(f"Pipeline report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
