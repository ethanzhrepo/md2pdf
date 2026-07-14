# Relative Images in PDF Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make local images referenced relative to a Markdown file render reliably and at sensible dimensions in the final PDF.

**Architecture:** Pandoc will resolve resources from the Markdown source directory and embed them into the standalone HTML before Playwright opens it from the build directory. The existing print stylesheet will constrain block images to the printable A4 area while preserving intrinsic aspect ratio.

**Tech Stack:** Python 3.10+, unittest, Pandoc standalone HTML, CSS print layout, Playwright/Chromium, PyMuPDF/Pillow QA.

## Global Constraints

- Relative image paths resolve against the Markdown source directory, even when the HTML build directory is elsewhere.
- Images retain their aspect ratio; small images are not enlarged.
- Large or tall figures stay within the printable A4 content area where practical.
- Absolute paths and data URLs remain accepted; remote URLs continue to require network access during conversion.
- Do not add image conversion, recompression, caching, CLI sizing flags, or custom download/error-recovery logic.

---

### Task 1: Embed Markdown Image Resources

**Files:**
- Create: `tests/fixtures/relative_image/document.md`
- Create: `tests/fixtures/relative_image/assets/marker.svg`
- Modify: `tests/test_build_pdf.py:1-72`
- Modify: `src/md2pdf/build_pdf.py:163-175`

**Interfaces:**
- Consumes: `parse_args(argv: list[str] | None) -> BuildConfig` and `run_pandoc(config: BuildConfig) -> Path`.
- Produces: standalone HTML whose local image `src` values contain embedded data instead of unresolved relative filesystem paths.

- [ ] **Step 1: Add the relative-image fixture**

Create `tests/fixtures/relative_image/document.md`:

```markdown
# Relative image fixture

The colored marker should appear below.

![marker](assets/marker.svg)
```

Create `tests/fixtures/relative_image/assets/marker.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="500" height="220" viewBox="0 0 500 220">
  <rect width="500" height="220" fill="#e11d48"/>
  <circle cx="250" cy="110" r="70" fill="#0ea5e9"/>
</svg>
```

- [ ] **Step 2: Write the failing Pandoc regression test**

Add `shutil` and `tempfile` imports, import `run_pandoc`, define the fixture directory, and add this test to `Md2PdfUtilityTests` in `tests/test_build_pdf.py`:

```python
import shutil
import tempfile


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "relative_image"


@unittest.skipUnless(shutil.which("pandoc"), "pandoc is required")
def test_run_pandoc_embeds_image_relative_to_source_directory(self):
    with tempfile.TemporaryDirectory() as tmp:
        temp_dir = Path(tmp)
        config = parse_args(
            [
                str(FIXTURE_DIR / "document.md"),
                "--output",
                str(temp_dir / "document.pdf"),
                "--build-dir",
                str(temp_dir / "build"),
                "--no-toc",
                "--no-qa",
            ]
        )

        html_path = run_pandoc(config)
        generated_html = html_path.read_text(encoding="utf-8")

    self.assertIn('src="data:image/svg+xml', generated_html)
    self.assertNotIn('src="assets/marker.svg"', generated_html)
```

Also add `run_pandoc` to the existing `from md2pdf.build_pdf import (...)` list.

- [ ] **Step 3: Run the regression test and confirm RED**

Run:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_build_pdf.py' -v
```

Expected: `test_run_pandoc_embeds_image_relative_to_source_directory` fails because the HTML contains `src="assets/marker.svg"` and no `data:image/svg+xml` source.

- [ ] **Step 4: Add the minimal Pandoc resource options**

Update the `command` list in `run_pandoc` immediately after `--standalone`:

```python
        "--standalone",
        "--resource-path",
        str(config.source.parent),
        "--embed-resources",
```

Keep the existing `cwd=config.source.parent`; it remains useful for Pandoc inputs other than embedded images.

- [ ] **Step 5: Run the regression test and confirm GREEN**

Run:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_build_pdf.py' -v
```

Expected: all `test_build_pdf.py` tests pass, with the new test confirming an embedded SVG data URL.

- [ ] **Step 6: Commit the resource fix**

```bash
git add tests/fixtures/relative_image/document.md tests/fixtures/relative_image/assets/marker.svg tests/test_build_pdf.py src/md2pdf/build_pdf.py
git commit -m "Fix relative image resources in PDFs"
```

---

### Task 2: Constrain Figure Layout for Print

**Files:**
- Modify: `tests/test_build_pdf.py:1-90`
- Modify: `src/md2pdf/style.css:356-358`
- Modify: `README.md:48-50`

**Interfaces:**
- Consumes: `DEFAULT_CSS: Path`, Pandoc's `figure > img` and `figcaption` HTML structure.
- Produces: print CSS that preserves aspect ratio, avoids horizontal overflow, limits tall figures, centers block images, and styles captions.

- [ ] **Step 1: Write the failing stylesheet contract test**

Add `DEFAULT_CSS` to the existing `from md2pdf.build_pdf import (...)` list and add this test to `Md2PdfUtilityTests`:

```python
def test_default_css_constrains_figures_to_printable_area(self):
    css = DEFAULT_CSS.read_text(encoding="utf-8")

    for required_rule in (
        "max-width: 100%;",
        "height: auto;",
        "max-height: 220mm;",
        "object-fit: contain;",
        "break-inside: avoid;",
        "figcaption {",
    ):
        with self.subTest(required_rule=required_rule):
            self.assertIn(required_rule, css)
```

- [ ] **Step 2: Run the stylesheet test and confirm RED**

Run:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_build_pdf.py' -v
```

Expected: `test_default_css_constrains_figures_to_printable_area` fails because the current stylesheet only sets `figure { margin: 0; }`.

- [ ] **Step 3: Implement the print-safe figure styles**

Replace the existing `figure` rule in `src/md2pdf/style.css` with:

```css
img {
  max-width: 100%;
  height: auto;
}

figure {
  margin: 4mm 0 5mm 0;
  break-inside: avoid;
}

figure img {
  display: block;
  max-height: 220mm;
  margin: 0 auto;
  object-fit: contain;
}

figcaption {
  margin-top: 1.5mm;
  color: var(--muted);
  font-size: 9pt;
  line-height: 1.45;
  text-align: center;
}
```

- [ ] **Step 4: Document relative image behavior**

After the default output/title paragraph in `README.md`, add:

```markdown
Local image paths are resolved relative to the Markdown source file and embedded in the generated HTML before printing. Large images are scaled down to fit the printable page area while retaining their aspect ratio; smaller images keep their natural size.
```

- [ ] **Step 5: Run the stylesheet test and confirm GREEN**

Run:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_build_pdf.py' -v
```

Expected: all `test_build_pdf.py` tests pass.

- [ ] **Step 6: Commit the layout and documentation change**

```bash
git add tests/test_build_pdf.py src/md2pdf/style.css README.md
git commit -m "Style embedded images for print"
```

---

### Task 3: Full Regression and PDF Verification

**Files:**
- Verify: `tests/test_build_pdf.py`
- Verify: `tests/test_gen_pdf_shell.py`
- Verify: `tests/fixtures/relative_image/document.md`
- Verify: `tests/fixtures/relative_image/assets/marker.svg`

**Interfaces:**
- Consumes: the `md2pdf.build_pdf` CLI and its QA-rendered page PNGs.
- Produces: fresh automated and visual evidence that the complete Markdown-to-PDF path includes the relative image at sensible dimensions.

- [ ] **Step 1: Run the complete unit test suite**

Run:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Expected: every test passes with no failures or errors. The harmless Pandoc zh-CN translation warning may appear during the integration test.

- [ ] **Step 2: Generate a real PDF from the relative-image fixture**

Run:

```bash
PYTHONPATH=src python -m md2pdf.build_pdf tests/fixtures/relative_image/document.md --output /tmp/md2pdf-relative-image-e2e.pdf --build-dir /tmp/md2pdf-relative-image-e2e-build --no-toc
```

Expected: exit code 0, a PDF at `/tmp/md2pdf-relative-image-e2e.pdf`, and QA previews under `/tmp/md2pdf-relative-image-e2e-build/qa/`.

- [ ] **Step 3: Confirm the embedded data and rendered marker**

Inspect `/tmp/md2pdf-relative-image-e2e-build/document.html` and `/tmp/md2pdf-relative-image-e2e-build/qa/page_002.png`. The HTML must contain `data:image/svg+xml`; the rendered page must show the full red rectangle and blue circle, centered and contained within the text area, with the caption below it.

Use this read-only pixel check as an additional objective assertion:

```bash
python -c "from PIL import Image; image=Image.open('/tmp/md2pdf-relative-image-e2e-build/qa/page_002.png').convert('RGB'); pixels=list(image.getdata()); assert sum(1 for r,g,b in pixels if r>180 and g<70 and b<120)>1000; assert sum(1 for r,g,b in pixels if r<50 and 100<g<200 and b>150)>1000"
```

Expected: exit code 0.

- [ ] **Step 4: Check the final worktree and diff**

Run:

```bash
git status --short
git diff --check HEAD~2..HEAD
git log -3 --oneline
```

Expected: the worktree is clean, `git diff --check` reports no whitespace errors, and the two implementation commits appear above the design/plan documentation history.
