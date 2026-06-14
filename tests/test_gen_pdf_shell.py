import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "gen_pdf.sh"


class GenPdfShellTests(unittest.TestCase):
    def test_help_describes_input_and_optional_output(self):
        result = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Usage: ./gen_pdf.sh INPUT.md [OUTPUT.pdf]", result.stdout)

    def test_dry_run_uses_first_heading_and_default_pdf_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "sample.md"
            source.write_text("# 中文标题\n\n正文。\n", encoding="utf-8")

            result = subprocess.run(
                ["bash", str(SCRIPT), "--dry-run", str(source)],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("python -m md2pdf.build_pdf", result.stdout)
        self.assertIn(str(source.with_suffix(".pdf")), result.stdout)
        self.assertIn("--title", result.stdout)
        self.assertIn("中文标题", result.stdout)


if __name__ == "__main__":
    unittest.main()
