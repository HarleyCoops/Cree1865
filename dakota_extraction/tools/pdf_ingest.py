"""Render PDF pages into image files for VLM extraction."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import fitz


def render_pdf_pages(
    pdf_path: str | Path,
    output_dir: str | Path,
    *,
    start_page: int = 1,
    end_page: int | None = None,
    dpi: int = 200,
    image_format: str = "png",
    prefix: str = "page",
) -> list[Path]:
    """Render a page range from a PDF into raster images.

    Args:
        pdf_path: Path to the input PDF.
        output_dir: Directory for rendered images.
        start_page: 1-based starting page.
        end_page: 1-based ending page inclusive. Defaults to final page.
        dpi: Rasterization DPI.
        image_format: Output format accepted by PyMuPDF, typically `png` or `jpg`.
        prefix: Filename prefix for output pages.

    Returns:
        Rendered image paths in page order.
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if start_page < 1:
        raise ValueError("start_page must be >= 1")

    with fitz.open(pdf_path) as document:
        final_page = end_page or document.page_count
        if final_page < start_page:
            raise ValueError("end_page must be >= start_page")
        if final_page > document.page_count:
            raise ValueError("end_page exceeds PDF page count")

        scale = dpi / 72.0
        matrix = fitz.Matrix(scale, scale)
        rendered_paths: list[Path] = []

        for page_number in range(start_page, final_page + 1):
            page = document[page_number - 1]
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            output_path = output_dir / f"{prefix}_{page_number:03d}.{image_format}"
            pixmap.save(output_path)
            rendered_paths.append(output_path)

    return rendered_paths


def summarize_rendered_pages(paths: Iterable[Path]) -> dict[str, object]:
    """Return a compact summary of rendered image output."""
    page_paths = list(paths)
    return {
        "count": len(page_paths),
        "first": page_paths[0].name if page_paths else None,
        "last": page_paths[-1].name if page_paths else None,
    }
