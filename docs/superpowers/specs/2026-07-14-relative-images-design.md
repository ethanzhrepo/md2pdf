# Relative Images in PDF Design

## Goal

Ensure local images referenced with paths relative to a Markdown document are rendered in the final PDF even when the intermediate HTML is written to a separate build directory.

Images should retain their aspect ratio. Small images should not be enlarged, while large or tall images should be constrained to the printable page area. Captions should remain visually subordinate to body text, and figures should avoid page breaks where practical.

## Scope

This change covers images referenced through normal Markdown image syntax, including nested relative paths such as `assets/diagram.svg`. PNG, JPEG, GIF, WebP, and SVG are handled through Pandoc and Chromium's existing image support.

Absolute paths and data URLs remain accepted. Remote URLs are fetched by Pandoc while resources are embedded, so they still require network access during conversion. This change does not add a custom downloader, caching, conversion, or custom error recovery.

## Conversion Design

`run_pandoc` will explicitly set the Markdown source directory as Pandoc's resource path and request embedded resources in the standalone HTML output.

The conversion flow is:

1. Pandoc reads the Markdown from its source directory.
2. Relative image paths are resolved against that directory.
3. Image bytes are embedded into the generated standalone HTML.
4. Playwright opens the HTML from the build directory and prints it to PDF without needing the original relative paths.

Embedding at the Pandoc boundary fixes the path at its source and avoids filesystem-dependent absolute links or copied resource trees. It also keeps the existing separation between source files and build artifacts.

## Presentation Design

The print stylesheet will apply the following figure behavior:

- Images use `display: block`, retain their intrinsic aspect ratio, and are centered.
- `max-width: 100%` prevents horizontal overflow without enlarging small images.
- A page-aware maximum height prevents tall images from overflowing the printable A4 area.
- Figures avoid internal page breaks where Chromium can honor that constraint.
- Captions are centered, use muted text, and have compact spacing.

## Error Handling

Pandoc remains responsible for warning about unreadable or missing image resources. The command continues to run with `check=True`, so fatal Pandoc failures propagate through the existing concise CLI error handling; non-fatal resource warnings retain Pandoc's normal behavior.

No silent path rewriting or fallback placeholder is introduced. The existing QA previews remain available for visual inspection.

## Testing

An integration-style unit test will create a Markdown file and SVG image in a temporary source directory while placing generated HTML in a different build directory. The test will verify that Pandoc embeds the image instead of leaving the relative `src` unchanged.

Implementation will follow test-driven development:

1. Add the regression test and confirm that it fails with the current implementation.
2. Add the minimal Pandoc resource options and confirm the test passes.
3. Add the image presentation CSS.
4. Run the complete unit test suite.
5. Generate a real PDF from a relative image fixture and inspect the rendered page to confirm correct inclusion and sizing.

## Non-goals

- Rewriting raw HTML image markup beyond Pandoc's normal resource handling.
- Adding command-line flags for image sizing.
- Optimizing or recompressing image files.
- Making the intermediate HTML portable as a separately distributed artifact beyond what resource embedding naturally provides.
