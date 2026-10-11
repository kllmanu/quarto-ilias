#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
questions_file=${QTI_QUESTIONS_FILE:-questions.json}

if [ -f "$questions_file" ]; then
  jsonschema validate "$script_dir/../schema/qti.schema.json" "$questions_file"
fi