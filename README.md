# md2pdf

A Markdown-to-PDF tool tuned for Chinese / CJK documents:

1. Pandoc converts Markdown to standalone HTML with a table of contents.
2. `md2pdf/style.css` handles CJK fonts, the cover page, TOC, headings, blockquotes, tables, and page breaks.
3. Playwright / headless Chrome prints the HTML to an A4 PDF.
4. PyMuPDF + Pillow render QA images and a `summary.txt` to check page count, page size, garbled (replacement) characters, and spot-check pages.

> The PyPI distribution name is **`md2pdf-tool`** (the plain `md2pdf` name was already taken on PyPI). The installed command is still **`md2pdf`**.

## Install

Two system dependencies must be installed first (pip cannot install them):

- **pandoc** — `brew install pandoc` (macOS) / `apt install pandoc` (Debian/Ubuntu).
- **A headless browser** — after installing the Python package, run `playwright install chromium` to download Playwright's bundled Chromium. On macOS an existing Google Chrome is reused automatically.

Then install the tool. For end users:

```bash
# Homebrew (personal tap)
brew install ethanzhrepo/md2pdf/md2pdf
playwright install chromium

# or pipx
pipx install md2pdf-tool
playwright install chromium
```

From source / for development:

```bash
pipx install .          # install from the repo, gives a global `md2pdf` command
# or an editable install:
python -m venv .venv && source .venv/bin/activate
pip install -e .
playwright install chromium
```

## Usage

After installing, use the `md2pdf` command:

```bash
md2pdf docs/requirements.md
```

Without `--output`, the PDF is written next to the source with a `.pdf` suffix. Without `--title`, the filename stem is used.

There is also a `gen_pdf.sh` wrapper that reads the first level-1 Markdown heading as the cover title:

```bash
./gen_pdf.sh docs/requirements.md docs/requirements.pdf
./gen_pdf.sh --dry-run docs/requirements.md   # print the command without running it
```

To set the title, subtitle, date, or required text explicitly, pass the matching flags:

```bash
md2pdf docs/requirements.md \
  --output docs/requirements.pdf \
  --title "项目需求说明" \
  --subtitle "Private-deployment authoring, publishing, and playback platform" \
  --date "2026-06-03" \
  --required-text "Final one-line goal"
```

Without installing, you can also run it as a module from the repo root (requires `pip install -e .` or `PYTHONPATH=src`):

```bash
python -m md2pdf.build_pdf path/to/input.md --output path/to/output.pdf
```

## Output

A run produces (using `requirements` as an example):

- PDF: `docs/requirements.pdf`
- Intermediate HTML: `<build-dir>/requirements.html`
- QA summary: `<build-dir>/qa/summary.txt`
- Spot-check page images and thumbnails: `<build-dir>/qa/*.png`

`<build-dir>` defaults to `.build/<stem>/` **next to the output PDF** (user-writable, never written into a read-only install location). Use `--build-dir` to point it elsewhere, e.g. `--build-dir ./.md2pdf-build`.

## Dependencies

- `pandoc`
- Python packages: `playwright`, `PyMuPDF` (`fitz`), `Pillow` (installed automatically by `pip install`)
- Google Chrome or Playwright Chromium

Pandoc may print `Could not load translations for zh-CN`; this is harmless and does not affect Chinese content or PDF text extraction.

## Tests

```bash
pip install -e .
python -m unittest discover -s tests -v
```
