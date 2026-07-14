#!/usr/bin/env bash
#
# Convenience wrapper around `python -m md2pdf.build_pdf`.
# Reads the first level-1 Markdown heading as the PDF cover title.
# When OUTPUT is omitted, writes <input>.pdf next to the source.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./gen_pdf.sh [--cover-label LABEL] INPUT.md [OUTPUT.pdf]

Convert a Markdown file to a styled, Chinese-friendly A4 PDF.
The first "# heading" in INPUT.md becomes the cover title.

Options:
  --cover-label LABEL  Badge above the cover title (e.g. 需求说明书).
                       Omitted by default, which hides the badge.
  --dry-run            Print the build command without running it.
  -h, --help           Show this help and exit.
EOF
}

dry_run=0
cover_label=""
args=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --dry-run) dry_run=1 ;;
    --cover-label)
      if [ "$#" -lt 2 ]; then
        echo "--cover-label needs a value" >&2
        exit 1
      fi
      cover_label="$2"
      shift
      ;;
    --cover-label=*) cover_label="${1#*=}" ;;
    *) args+=("$1") ;;
  esac
  shift
done

if [ "${#args[@]}" -lt 1 ]; then
  usage >&2
  exit 1
fi

input="${args[0]}"
output="${args[1]:-${input%.md}.pdf}"

# First level-1 heading ("# Title"), stripped of the leading marker.
title="$(grep -m1 '^# ' "$input" | sed 's/^# *//' || true)"

label_args=()
if [ -n "$cover_label" ]; then
  label_args=(--cover-label "$cover_label")
fi

if [ "$dry_run" -eq 1 ]; then
  line="python -m md2pdf.build_pdf \"$input\" --output \"$output\" --title \"$title\""
  if [ -n "$cover_label" ]; then
    line="$line --cover-label \"$cover_label\""
  fi
  echo "$line"
  exit 0
fi

# ${arr[@]+"${arr[@]}"} keeps an empty array from tripping `set -u` on bash 3.2,
# which is what macOS still ships as /bin/bash.
exec python -m md2pdf.build_pdf "$input" --output "$output" --title "$title" \
  ${label_args[@]+"${label_args[@]}"}
