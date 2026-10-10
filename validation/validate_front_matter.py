#!/usr/bin/env python3
"""Pre-render hook: validate each document's `qti` front matter against the JSON Schema."""

import json
import os
import pathlib
import re
import sys
from urllib.parse import urlparse
from urllib.request import url2pathname

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "_extensions/qti/schema/qti.schema.json"
FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)


def retrieve(uri):
    path = pathlib.Path(url2pathname(urlparse(uri).path))
    return Resource.from_contents(json.loads(path.read_text()), default_specification=DRAFT202012)


def build_validator():
    schema = json.loads(SCHEMA_PATH.read_text()) | {"$id": SCHEMA_PATH.as_uri()}
    return Draft202012Validator(schema, registry=Registry(retrieve=retrieve))


def input_files():
    listed = os.environ.get("QUARTO_PROJECT_INPUT_FILES", "").split()
    files = [pathlib.Path(name) for name in listed] or sorted(PROJECT_ROOT.glob("examples/*.qmd"))
    return [path for path in files if path.suffix == ".qmd"]


def front_matter(path):
    match = FRONT_MATTER.match(path.read_text())
    return yaml.safe_load(match.group(1)) if match else {}


def main():
    validator = build_validator()
    failed = False

    for path in input_files():
        error = best_match(validator.iter_errors(front_matter(path)))
        if error:
            failed = True
            location = ".".join(str(part) for part in error.absolute_path) or "(root)"
            print(f"{path}: {location}: {error.message}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
