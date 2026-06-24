"""Build presentation-grade source-story assets for the Cree1865 dossier."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[2]
DOSSIER_DIR = REPO_ROOT / "docs" / "source_dossier"
SCREENS_DIR = DOSSIER_DIR / "screens"
IA_DIR = DOSSIER_DIR / "internet_archive"
THUMBS_DIR = IA_DIR / "thumbs"
IA_PREVIEW_DIR = SCREENS_DIR / "ia_preview_pages"

BG = "#efe7d8"
PANEL = "#f8f4ec"
BORDER = "#9c835c"
TEXT = "#2f261c"
MUTED = "#6e5a3e"
ACCENT = "#836743"


def _load_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\georgiab.ttf" if bold else r"C:\Windows\Fonts\georgia.ttf",
        r"C:\Windows\Fonts\Garamond.ttf",
        r"C:\Windows\Fonts\timesbd.ttf" if bold else r"C:\Windows\Fonts\times.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


FONT_H1 = _load_font(42, bold=True)
FONT_H2 = _load_font(28, bold=True)
FONT_H3 = _load_font(22, bold=True)
FONT_BODY = _load_font(18)
FONT_SMALL = _load_font(15)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [text]


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    *,
    font: ImageFont.ImageFont,
    fill: str,
    max_width: int,
    line_gap: int = 6,
) -> int:
    x, y = xy
    for line in wrap_text(draw, text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, y), line, font=font)
        y = bbox[3] + line_gap
    return y


def fit_image(image: Image.Image, box: tuple[int, int], *, pad: int = 0, bg: str = "#ffffff") -> Image.Image:
    width, height = box
    canvas = Image.new("RGB", (width, height), bg)
    copy = image.copy().convert("RGB")
    copy.thumbnail((width - pad * 2, height - pad * 2))
    x = (width - copy.width) // 2
    y = (height - copy.height) // 2
    canvas.paste(copy, (x, y))
    return canvas


def panel(
    canvas: Image.Image,
    xyxy: tuple[int, int, int, int],
    *,
    radius: int = 24,
    fill: str = PANEL,
    outline: str = BORDER,
    width: int = 3,
) -> ImageDraw.ImageDraw:
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(xyxy, radius=radius, fill=fill, outline=outline, width=width)
    return draw


@dataclass(frozen=True)
class DossierImages:
    cover_1865: Path = SCREENS_DIR / "local_page_001-001.png"
    title_1865: Path = SCREENS_DIR / "local_page_005-005.png"
    preface_1865: Path = SCREENS_DIR / "local_page_024-024.png"
    pronunciation_1865: Path = SCREENS_DIR / "local_page_028-028.png"
    part1_1865: Path = SCREENS_DIR / "local_page_029-029.png"
    part2_1865: Path = SCREENS_DIR / "local_page_212-212.png"
    ia_cover_large: Path = THUMBS_DIR / "dictionaryofcree0000reve_cover_large.jpg"
    ia_title_preview: Path = IA_PREVIEW_DIR / "dictionaryofcree0000reve_leaf005_ia_preview.png"
    ia_dedication_preview: Path = IA_PREVIEW_DIR / "dictionaryofcree0000reve_leaf006_ia_preview.png"


IMAGES = DossierImages()


def build_hero_banner() -> Path:
    output_path = DOSSIER_DIR / "cree_dictionary_hero_banner.png"
    canvas = Image.new("RGB", (1800, 1200), BG)
    draw = ImageDraw.Draw(canvas)

    draw.text((48, 34), "Cree1865: One Source Book, Two Dictionary Worlds", font=FONT_H1, fill=TEXT)
    draw.text(
        (48, 94),
        "Watkins' 1865 Cree dictionary is a bilingual bridge document: front matter, Part I English-Cree, and Part II Cree-English in one historical volume.",
        font=FONT_BODY,
        fill=MUTED,
    )

    panel(canvas, (36, 150, 1764, 1160))

    left_x = 72
    center_x = 640
    right_x = 1218
    top_y = 186

    cover = fit_image(Image.open(IMAGES.cover_1865), (500, 420), bg="#faf7f0")
    canvas.paste(cover, (left_x, top_y))
    title = fit_image(Image.open(IMAGES.title_1865), (500, 420), bg="#faf7f0")
    canvas.paste(title, (left_x, top_y + 446))

    part1 = fit_image(Image.open(IMAGES.part1_1865), (520, 355), bg="#faf7f0")
    part2 = fit_image(Image.open(IMAGES.part2_1865), (520, 355), bg="#faf7f0")
    canvas.paste(part1, (center_x, top_y + 20))
    canvas.paste(part2, (center_x, top_y + 420))

    ia_cover = fit_image(Image.open(IMAGES.ia_cover_large), (470, 500), bg="#faf7f0")
    ia_title = fit_image(Image.open(IMAGES.ia_title_preview), (470, 330), bg="#faf7f0")
    canvas.paste(ia_cover, (right_x, top_y))
    canvas.paste(ia_title, (right_x, top_y + 540))

    draw.text((left_x, top_y - 36), "1865 object on disk", font=FONT_H2, fill=ACCENT)
    draw.text((center_x, top_y - 36), "Internal structure", font=FONT_H2, fill=ACCENT)
    draw.text((right_x, top_y - 36), "Later Archive companion", font=FONT_H2, fill=ACCENT)

    draw_wrapped_text(
        draw,
        "The title page states that the 1865 book already contains Part I English-Cree and Part II Cree-English. That makes it a two-direction lexical machine, not just a one-way missionary glossary.",
        (center_x, top_y + 795),
        font=FONT_BODY,
        fill=TEXT,
        max_width=520,
    )
    draw_wrapped_text(
        draw,
        "The later Internet Archive item carries the same two-part structure in revised form. It matters as a historical companion, but the local RL pipeline still starts from the single 1865 source file.",
        (right_x, top_y + 895),
        font=FONT_BODY,
        fill=TEXT,
        max_width=500,
    )
    draw_wrapped_text(
        draw,
        "Cultural significance: this is a bilingual bridge text shaped by missionary print culture, orthographic compromise, and practical translation work across the Hudson's Bay territories. For the pipeline, that means archival structure is strong, but community pragmatics still live outside the book.",
        (72, 1050),
        font=FONT_BODY,
        fill=TEXT,
        max_width=1500,
    )

    canvas.save(output_path)
    return output_path


def build_second_volume_access_story() -> Path:
    output_path = DOSSIER_DIR / "cree_second_volume_ia_access_story.png"
    canvas = Image.new("RGB", (1800, 1160), BG)
    draw = ImageDraw.Draw(canvas)

    draw.text((48, 34), "Internet Archive Second-Volume Access Reality", font=FONT_H1, fill=TEXT)
    draw.text(
        (48, 92),
        "The item exists, exposes metadata and preview leaves anonymously, but the full borrow/download path requires Archive authentication.",
        font=FONT_BODY,
        fill=MUTED,
    )

    panel(canvas, (36, 150, 1764, 1118))

    left = Image.open(IMAGES.ia_cover_large)
    right = Image.open(IMAGES.ia_title_preview)
    dedication = Image.open(IMAGES.ia_dedication_preview)

    canvas.paste(fit_image(left, (400, 640), bg="#faf7f0"), (72, 220))
    canvas.paste(fit_image(right, (470, 390), bg="#faf7f0"), (540, 220))
    canvas.paste(fit_image(dedication, (470, 390), bg="#faf7f0"), (540, 660))

    draw.text((72, 178), "Directly downloadable from IA", font=FONT_H2, fill=ACCENT)
    draw.text((540, 178), "Direct IA preview leaves", font=FONT_H2, fill=ACCENT)

    proof_x = 1088
    draw.text((proof_x, 178), "Acquisition proof", font=FONT_H2, fill=ACCENT)
    bullet_lines = [
        "Item identifier: dictionaryofcree0000reve",
        "Metadata endpoint: 200 OK",
        "Auth document: 200 OK",
        "Borrow surface: 401 without login",
        "Anonymous preview leaves exposed by BookReader: 11",
        "Official cover image downloaded directly from IA",
        "Full local companion PDF already stored on disk for offline use",
    ]
    y = 235
    for line in bullet_lines:
        draw.text((proof_x, y), f"• {line}", font=FONT_BODY, fill=TEXT)
        y += 42

    y += 14
    draw.text((proof_x, y), "What this means", font=FONT_H3, fill=ACCENT)
    y += 44
    y = draw_wrapped_text(
        draw,
        "The second-volume step is partly complete from the network side: the Internet Archive item is identified and the public preview surface is downloaded. The exact official full-file download remains gated behind Archive authentication, so the remaining delta is credentials, not discovery.",
        (proof_x, y),
        font=FONT_BODY,
        fill=TEXT,
        max_width=620,
    )

    y += 24
    draw.text((proof_x, y), "Why the dictionary matters culturally", font=FONT_H3, fill=ACCENT)
    y += 42
    draw_wrapped_text(
        draw,
        "The companion volume shows that Watkins' lexical foundation continued to circulate and be revised across regions. That gives the project historical depth: one archival source can seed extraction and RL scaffolding, while later witnesses help situate the tradition without replacing community authority.",
        (proof_x, y),
        font=FONT_BODY,
        fill=TEXT,
        max_width=620,
    )

    canvas.save(output_path)
    return output_path


def main() -> int:
    outputs: Iterable[Path] = [
        build_hero_banner(),
        build_second_volume_access_story(),
    ]
    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
