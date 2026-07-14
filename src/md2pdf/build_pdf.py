from __future__ import annotations

import argparse
import html
import math
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date as local_date
from importlib import metadata
from pathlib import Path


TOOL_DIR = Path(__file__).resolve().parent
DEFAULT_CSS = TOOL_DIR / "style.css"
# PyPI distribution name; the import package is `md2pdf` (see pyproject.toml).
DIST_NAME = "md2pdf-tool"


def resolve_version() -> str:
    try:
        return metadata.version(DIST_NAME)
    except metadata.PackageNotFoundError:
        # Running from a source checkout (e.g. PYTHONPATH=src) with nothing installed.
        return "unknown (source checkout)"


@dataclass(frozen=True)
class BuildConfig:
    source: Path
    output: Path
    title: str
    subtitle: str
    date: str
    cover_label: str
    css: Path
    build_dir: Path
    footer_title: str
    toc: bool
    toc_depth: int
    qa: bool
    required_text: tuple[str, ...]


def default_output_path(source: Path) -> Path:
    return source.with_suffix(".pdf")


def build_metadata(title: str, subtitle: str = "", date: str = "", lang: str = "zh-CN") -> str:
    lines = ["---", f"title: {title}"]
    if subtitle:
        lines.append(f"subtitle: {subtitle}")
    if date:
        lines.append(f"date: {date}")
    lines.extend([f"lang: {lang}", "---", ""])
    return "\n".join(lines)


def css_string_literal(text: str) -> str:
    """Quote text for use as a CSS string value (e.g. the `content` property)."""
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    # The literal is emitted inside an inline <style>, where "</style" would
    # close the element early. CSS unicode escapes keep the text intact.
    escaped = escaped.replace("<", "\\3c ")
    escaped = escaped.replace("\n", "\\A ")
    return f'"{escaped}"'


def cover_label_style(label: str) -> str:
    return f"<style>:root {{ --cover-label: {css_string_literal(label)}; }}</style>\n"


def selected_qa_pages(page_count: int) -> list[int]:
    if page_count < 1:
        raise ValueError("PDF has no pages")
    candidates = {0, page_count // 2, page_count - 1}
    if page_count > 1:
        candidates.add(1)
    if page_count > 2:
        candidates.add(2)
    return sorted(candidates)


def parse_args(argv: list[str] | None = None) -> BuildConfig:
    parser = argparse.ArgumentParser(
        description="Convert Markdown to a styled Chinese-friendly PDF and render QA previews.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"md2pdf {resolve_version()}",
        help="Show the installed version and exit.",
    )
    parser.add_argument("source", type=Path, help="Markdown source file")
    parser.add_argument("--output", type=Path, help="PDF output path. Defaults to SOURCE with .pdf suffix.")
    parser.add_argument("--title", help="Cover/title metadata. Defaults to the source filename stem.")
    parser.add_argument("--subtitle", default="", help="Optional subtitle shown on the cover.")
    parser.add_argument(
        "--cover-label",
        default="",
        help='Optional badge above the cover title, e.g. "需求说明书". Hidden when omitted.',
    )
    parser.add_argument("--date", default=local_date.today().isoformat(), help="Cover date. Defaults to today.")
    parser.add_argument("--css", type=Path, default=DEFAULT_CSS, help="Print CSS file.")
    parser.add_argument("--build-dir", type=Path, help="Intermediate HTML, metadata, and QA output directory.")
    parser.add_argument("--footer-title", help="Footer document title. Defaults to --title.")
    parser.add_argument("--toc-depth", type=int, default=2, help="Pandoc table-of-contents depth.")
    parser.add_argument("--no-toc", action="store_true", help="Disable generated table of contents.")
    parser.add_argument("--no-qa", action="store_true", help="Skip PyMuPDF/Pillow QA rendering.")
    parser.add_argument(
        "--required-text",
        action="append",
        default=[],
        help="Text that must be extractable from the final PDF. Can be passed multiple times.",
    )
    args = parser.parse_args(argv)

    source = args.source.resolve()
    output = (args.output or default_output_path(source)).resolve()
    title = args.title or source.stem
    # Default build dir lives next to the OUTPUT, not inside the package install
    # location (which may be read-only, e.g. a Homebrew cellar or system
    # site-packages). The output dir is user-owned and writable.
    build_dir = (
        args.build_dir.resolve()
        if args.build_dir
        else (output.parent / ".build" / source.stem)
    )

    return BuildConfig(
        source=source,
        output=output,
        title=title,
        subtitle=args.subtitle,
        date=args.date,
        cover_label=args.cover_label,
        css=args.css.resolve(),
        build_dir=build_dir,
        footer_title=args.footer_title or title,
        toc=not args.no_toc,
        toc_depth=args.toc_depth,
        qa=not args.no_qa,
        required_text=tuple(args.required_text),
    )


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Required command not found: {name}")


def run_pandoc(config: BuildConfig) -> Path:
    require_tool("pandoc")
    config.build_dir.mkdir(parents=True, exist_ok=True)
    metadata = config.build_dir / "metadata.yaml"
    html_path = config.build_dir / f"{config.source.stem}.html"
    metadata.write_text(
        build_metadata(config.title, config.subtitle, config.date),
        encoding="utf-8",
    )

    command = [
        "pandoc",
        str(config.source),
        "--from=markdown+smart",
        "--to=html5",
        "--standalone",
        "--metadata-file",
        str(metadata),
        "--css",
        str(config.css),
        "--output",
        str(html_path),
    ]
    if config.toc:
        command.extend(["--toc", "--toc-depth", str(config.toc_depth)])
    if config.cover_label:
        # style.css defaults --cover-label to `none`, which drops the badge; this
        # overrides it only when the caller asked for one.
        header = config.build_dir / "cover-label.html"
        header.write_text(cover_label_style(config.cover_label), encoding="utf-8")
        command.extend(["--include-in-header", str(header)])

    subprocess.run(command, check=True, cwd=config.source.parent)
    return html_path


def footer_template(title: str) -> str:
    escaped_title = html.escape(title)
    return f"""
    <style>
      .pdf-footer {{
        width: 100%;
        padding: 0 17mm;
        color: #697386;
        font-family: "Hiragino Sans GB", "STHeiti", "PingFang SC", Arial, sans-serif;
        font-size: 8px;
        display: flex;
        justify-content: space-between;
      }}
    </style>
    <div class="pdf-footer">
      <span>{escaped_title}</span>
      <span>第 <span class="pageNumber"></span> / <span class="totalPages"></span> 页</span>
    </div>
    """


def launch_chromium(playwright):
    launch_errors: list[str] = []
    launchers = [
        lambda: playwright.chromium.launch(channel="chrome", headless=True),
        lambda: playwright.chromium.launch(
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            headless=True,
        ),
        lambda: playwright.chromium.launch(headless=True),
    ]
    for launcher in launchers:
        try:
            return launcher()
        except Exception as exc:  # noqa: BLE001 - preserve diagnostics for all fallbacks
            launch_errors.append(str(exc))
    raise RuntimeError("\n\n".join(launch_errors))


def print_pdf(config: BuildConfig, html_path: Path) -> None:
    from playwright.sync_api import sync_playwright

    config.output.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = launch_chromium(p)
        page = browser.new_page(viewport={"width": 1240, "height": 1754})
        page.goto(html_path.as_uri(), wait_until="networkidle")
        page.emulate_media(media="print")
        page.pdf(
            path=str(config.output),
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template="<div></div>",
            footer_template=footer_template(config.footer_title),
            prefer_css_page_size=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        browser.close()


def render_page(doc, page_index: int, scale: float, path: Path) -> None:
    import fitz

    page = doc.load_page(page_index)
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    pix.save(str(path))


def make_contact_sheets(doc, qa_dir: Path) -> None:
    import fitz
    from PIL import Image, ImageDraw, ImageFont

    per_sheet = 12
    cols = 3
    rows = 4
    thumb_scale = 0.27
    pad = 22
    label_h = 24
    font = ImageFont.load_default()

    for sheet_index in range(math.ceil(doc.page_count / per_sheet)):
        start = sheet_index * per_sheet
        end = min(start + per_sheet, doc.page_count)
        thumbs: list[Image.Image] = []
        for page_index in range(start, end):
            pix = doc.load_page(page_index).get_pixmap(
                matrix=fitz.Matrix(thumb_scale, thumb_scale),
                alpha=False,
            )
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            canvas = Image.new("RGB", (img.width, img.height + label_h), "white")
            canvas.paste(img, (0, 0))
            draw = ImageDraw.Draw(canvas)
            draw.rectangle((0, 0, img.width - 1, img.height - 1), outline="#c7ced8", width=1)
            draw.text((8, img.height + 5), f"Page {page_index + 1}", fill="#334155", font=font)
            thumbs.append(canvas)

        cell_w = max(t.width for t in thumbs)
        cell_h = max(t.height for t in thumbs)
        sheet = Image.new(
            "RGB",
            (cols * cell_w + (cols + 1) * pad, rows * cell_h + (rows + 1) * pad),
            "#f2f5f9",
        )
        for i, thumb in enumerate(thumbs):
            x = pad + (i % cols) * (cell_w + pad)
            y = pad + (i // cols) * (cell_h + pad)
            sheet.paste(thumb, (x, y))

        sheet.save(qa_dir / f"contact_sheet_{sheet_index + 1:02d}.png")


def qa_render(config: BuildConfig, html_path: Path) -> Path:
    import fitz

    qa_dir = config.build_dir / "qa"
    if qa_dir.exists():
        shutil.rmtree(qa_dir)
    qa_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(config.output)
    for page_index in selected_qa_pages(doc.page_count):
        render_page(doc, page_index, 1.45, qa_dir / f"page_{page_index + 1:03d}.png")
    make_contact_sheets(doc, qa_dir)

    extracted = "\n".join(page.get_text() for page in doc)
    required_results = {
        item: item in extracted
        for item in (config.title, *config.required_text)
        if item
    }
    summary = {
        "pdf": str(config.output),
        "html": str(html_path),
        "pages": doc.page_count,
        "page_size_points": [round(doc[0].rect.width, 2), round(doc[0].rect.height, 2)],
        "replacement_character_count": extracted.count("\ufffd"),
        "required_text": required_results,
        "very_low_text_pages": [
            (i + 1, len(page.get_text().strip()))
            for i, page in enumerate(doc)
            if len(page.get_text().strip()) < 40
        ],
    }
    summary_path = qa_dir / "summary.txt"
    summary_path.write_text(
        "\n".join(f"{key}: {value}" for key, value in summary.items()) + "\n",
        encoding="utf-8",
    )
    doc.close()
    return summary_path


def build(config: BuildConfig) -> tuple[Path, Path | None]:
    if not config.source.exists():
        raise FileNotFoundError(config.source)
    if not config.css.exists():
        raise FileNotFoundError(config.css)

    html_path = run_pandoc(config)
    print_pdf(config, html_path)
    summary_path = qa_render(config, html_path) if config.qa else None
    return config.output, summary_path


def main(argv: list[str] | None = None) -> int:
    try:
        config = parse_args(argv)
        pdf_path, summary_path = build(config)
    except Exception as exc:  # noqa: BLE001 - CLI should report concise failure
        print(f"md2pdf failed: {exc}", file=sys.stderr)
        return 1

    print(f"PDF: {pdf_path}")
    if summary_path:
        print(f"QA: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
