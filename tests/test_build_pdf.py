import contextlib
import io
import unittest
from pathlib import Path

from md2pdf.build_pdf import (
    build_metadata,
    default_output_path,
    parse_args,
    resolve_version,
    selected_qa_pages,
)


class Md2PdfUtilityTests(unittest.TestCase):
    def test_default_output_path_reuses_source_stem(self):
        self.assertEqual(
            default_output_path(Path("docs/requirements.md")),
            Path("docs/requirements.pdf"),
        )

    def test_build_metadata_preserves_chinese_fields(self):
        metadata = build_metadata(
            title="中文标题",
            subtitle="中文副标题",
            date="2026-06-03",
        )

        self.assertIn("title: 中文标题", metadata)
        self.assertIn("subtitle: 中文副标题", metadata)
        self.assertIn("date: 2026-06-03", metadata)
        self.assertIn("lang: zh-CN", metadata)

    def test_selected_qa_pages_deduplicates_small_documents(self):
        self.assertEqual(selected_qa_pages(1), [0])
        self.assertEqual(selected_qa_pages(2), [0, 1])
        self.assertEqual(selected_qa_pages(70), [0, 1, 2, 35, 69])

    def test_resolve_version_is_never_empty(self):
        self.assertTrue(resolve_version())

    def test_version_flag_prints_and_exits_without_a_source(self):
        # The version action must fire before argparse enforces the required
        # `source` positional, so `md2pdf --version` works on its own.
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as exit_info:
                parse_args(["--version"])

        self.assertEqual(exit_info.exception.code, 0)
        self.assertEqual(stdout.getvalue().strip(), f"md2pdf {resolve_version()}")


if __name__ == "__main__":
    unittest.main()
