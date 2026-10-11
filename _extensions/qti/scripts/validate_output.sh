#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
dtd_dir="$script_dir/../validation"
output_files=${QUARTO_PROJECT_OUTPUT_FILES:-}

[ -n "$output_files" ] || exit 0

printf '%s\n' "$output_files" | while IFS= read -r output_file; do
  case "$output_file" in
    *.xml)
      root=$(xmllint --noout --nonet --path "$dtd_dir" --xpath 'name(/*)' "$output_file")
      if [ "$root" = questestinterop ]; then
        xmllint --noout --nonet --path "$dtd_dir" --valid "$output_file"
        printf '%s validates\n' "$output_file" >&2
      fi
      ;;
  esac
done