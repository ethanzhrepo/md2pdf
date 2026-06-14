#!/usr/bin/env bash
#
# Convenience wrapper around `python -m md2pdf.build_pdf`.
# Reads the first level-1 Markdown heading as the PDF cover title.
# When OUTPUT is omitted, writes <input>.pdf next to the source.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./gen_pdf.sh INPUT.md [OUTPUT.pdf]

Convert a Markdown file to a styled, Chinese-friendly A4 PDF.
The first "# heading" in INPUT.md becomes the cover title.

Options:
  --dry-run   Print the build command without running it.
  -h, --help  Show this help and exit.
EOF
}

dry_run=0
args=()
for arg in "$@"; do
  case "$arg" in
    -h|--help) usage; exit 0 ;;
    --dry-run) dry_run=1 ;;
    *) args+=("$arg") ;;
  esac
done

if [ "${#args[@]}" -lt 1 ]; then
  usage >&2
  exit 1
fi

input="${args[0]}"
output="${args[1]:-${input%.md}.pdf}"

# First level-1 heading ("# Title"), stripped of the leading marker.
title="$(grep -m1 '^# ' "$input" | sed 's/^# *//' || true)"

if [ "$dry_run" -eq 1 ]; then
  echo "python -m md2pdf.build_pdf \"$input\" --output \"$output\" --title \"$title\""
  exit 0
fi

exec python -m md2pdf.build_pdf "$input" --output "$output" --title "$title"
