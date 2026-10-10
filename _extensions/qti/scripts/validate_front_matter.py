"""Pre-render hook: validate each document's `qti` front matter against the JSON Schema.

Reads the files to check from QUARTO_PROJECT_INPUT_FILES, or from the command line.
"""

import json
import os
import pathlib
import re
import sys
from urllib.parse import urlparse
from urllib.request import url2pathname

from environment import run_in_environment

run_in_environment()

HERE = pathlib.Path(__file__).resolve().parent
SCHEMA_PATH = HERE.parent / "schema" / "qti.schema.json"
FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)


try:
    import yaml
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import best_match
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012
except ImportError as error:
    print(f"Front matter validation failed: missing Python package '{error.name}'. "
        f"Dependencies are listed in {HERE.parent / 'requirements.txt'}. "
        "Remove the cached QTI environment and rerun the setup hook.", file=sys.stderr)
    sys.exit(1)


def retrieve(uri):
    path = pathlib.Path(url2pathname(urlparse(uri).path))
    return Resource.from_contents(json.loads(path.read_text()), default_specification=DRAFT202012)


def build_validator():
    schema = json.loads(SCHEMA_PATH.read_text()) | {"$id": SCHEMA_PATH.as_uri()}
    return Draft202012Validator(schema, registry=Registry(retrieve=retrieve))


def input_files():
    listed = sys.argv[1:] or os.environ.get("QUARTO_PROJECT_INPUT_FILES", "").split()
    return [pathlib.Path(name) for name in listed if name.endswith(".qmd")]


def front_matter(path):
    match = FRONT_MATTER.match(path.read_text())
    return (yaml.safe_load(match.group(1)) if match else None) or {}


def document_metadata(path):
    data = front_matter(path)
    metadata_files = data.get("metadata-files", [])
    if isinstance(metadata_files, str):
        metadata_files = [metadata_files]
    if not isinstance(metadata_files, list):
        raise ValueError("metadata-files must be a path or a list of paths")

    for name in metadata_files:
        metadata_path = path.parent / name
        try:
            contents = metadata_path.read_text()
            included = json.loads(contents) if metadata_path.suffix.lower() == ".json" else yaml.safe_load(contents)
        except (OSError, json.JSONDecodeError, yaml.YAMLError) as error:
            raise ValueError(f"cannot read metadata file {metadata_path}: {error}") from error
        if not isinstance(included, dict):
            raise ValueError(f"metadata file {metadata_path} must contain a mapping")
        data = included | data
    return data


def main():
    validator = build_validator()
    failed = False

    for path in input_files():
        try:
            data = document_metadata(path)
        except ValueError as error:
            failed = True
            print(f"{path}: {error}", file=sys.stderr)
            continue
        if "qti" not in data:
            continue
        error = best_match(validator.iter_errors(data))
        if error:
            failed = True
            location = ".".join(str(part) for part in error.absolute_path) or "(root)"
            print(f"{path}: {location}: {error.message}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
