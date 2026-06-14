# Homebrew formula for the md2pdf CLI (personal tap).
#
# The formula is named `md2pdf` (nice `brew install …/md2pdf`) but installs the
# PyPI distribution `md2pdf-tool`.
#
# Before publishing the tap, fill in:
#   - homepage URL
#   - url + sha256 of the published sdist on PyPI (see PUBLISHING.md)
#
# Why pip-install instead of vendored `resource` blocks: Homebrew's install
# sandbox permits network access, so we let pip pull the heavy deps
# (playwright, PyMuPDF, Pillow) as prebuilt wheels from PyPI. That avoids
# compiling MuPDF from source. This is fine for a personal tap (homebrew-core
# would instead require every dependency vendored as a `resource`).
class Md2pdf < Formula
  include Language::Python::Virtualenv

  desc "Convert Markdown to a styled, Chinese-friendly A4 PDF"
  homepage "https://github.com/ethanzhrepo/md2pdf"
  url "https://files.pythonhosted.org/packages/source/m/md2pdf-tool/md2pdf_tool-0.1.0.tar.gz"
  sha256 "FILL_IN_AFTER_PUBLISH"
  license "MIT"

  depends_on "pandoc"
  depends_on "python@3.12"

  def install
    virtualenv_create(libexec, "python3.12")
    # Install the verified sdist (buildpath) and resolve its deps from PyPI as
    # binary wheels.
    system libexec/"bin/pip", "install", "--prefer-binary", buildpath
    bin.install_symlink libexec/"bin/md2pdf"
  end

  def caveats
    <<~EOS
      md2pdf needs two more things at runtime:

        1. pandoc — installed as a dependency of this formula.
        2. A headless Chromium for PDF rendering. Download it once with the
           playwright bundled in this formula's virtualenv:

             #{libexec}/bin/playwright install chromium

      QA/intermediate artifacts are written to .build/ next to the output PDF.
      When converting a file in a read-only location, pass
      --build-dir <writable-dir>.
    EOS
  end

  test do
    # --help only touches the stdlib (playwright/fitz/PIL are imported lazily),
    # so this passes without a browser or network.
    assert_match "usage: md2pdf", shell_output("#{bin}/md2pdf --help")
  end
end
