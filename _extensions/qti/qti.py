#!/usr/bin/env python3
"""Convert QTI question JSON to an IMS QTI 1.2.1 question collection for ILIAS 11.

Usage:
    qti.py QUESTIONS.json [-o OUTPUT.xml]   convert one file
    qti.py                                  Quarto project hook: convert every rendered .qmd
                                            whose front matter provides `qti` (directly or via
                                            `metadata-files`)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from lxml import etree

ROOT = Path(__file__).resolve().parent
SCHEMA_FILE = ROOT / "qti.schema.json"
DTD_FILE = ROOT / "validation" / "ims_qtiasiv1p2p1.dtd"
DOCTYPE = '<!DOCTYPE questestinterop SYSTEM "ims_qtiasiv1p2p1.dtd">'
AUTHOR = "Quarto QTI"
SAFE_FILE_STEM = re.compile(r"^[A-Za-z0-9_.-]+$")


class QtiError(Exception):
    pass


# --- JSON Schema validation -------------------------------------------------


def validate_schema(data, source):
    validator = Draft202012Validator(json.loads(SCHEMA_FILE.read_text(encoding="utf-8")))
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if errors:
        lines = [f"{source}: schema validation failed:"]
        for error in errors:
            location = "/".join(str(part) for part in error.absolute_path) or "(root)"
            lines.append(f"  {location}: {error.message}")
        raise QtiError("\n".join(lines))

    seen = set()
    for index, question in enumerate(data["qti"]["questions"], start=1):
        identifier = question_identifier(question, index)
        if identifier in seen:
            raise QtiError(f"{source}: duplicate question identifier: {identifier}")
        seen.add(identifier)
        choice_ids = [choice_identifier(c, i) for i, c in enumerate(question.get("choices", []), start=1)]
        if len(choice_ids) != len(set(choice_ids)):
            raise QtiError(f"{source}: duplicate choice identifier in question {identifier}")


# --- QTI construction -------------------------------------------------------


def _slug(value):
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")[:48]
    slug = slug or "QUESTION"
    return slug if re.match(r"[A-Za-z_]", slug) else "Q_" + slug


def question_identifier(question, index):
    if question.get("identifier"):
        return question["identifier"]
    return f"ITEM_{_slug(question.get('title') or question['prompt'])}_{index}"


def choice_identifier(choice, position):
    return choice.get("identifier") or f"CHOICE_{position}"


def _sub(parent, tag, text=None, **attrs):
    element = etree.SubElement(parent, tag, {k: str(v) for k, v in attrs.items()})
    if text is not None:
        element.text = str(text)
    return element


def _material(parent, text):
    _sub(_sub(parent, "material"), "mattext", text, texttype="text/plain")


def _item(parent, question, index, question_type, extra_metadata):
    external_id = question_identifier(question, index)
    title = question.get("title") or external_id
    # ILIAS 11 derives the source installation ID from this pattern.
    item = _sub(parent, "item", ident=f"il_0_qst_{index}", title=title, maxattempts=0)

    metadata = _sub(_sub(item, "itemmetadata"), "qtimetadata")
    fields = [("externalId", external_id), ("QUESTIONTYPE", question_type), ("AUTHOR", AUTHOR),
              ("additional_cont_edit_mode", "default"), *extra_metadata]
    for label, entry in fields:
        field = _sub(metadata, "qtimetadatafield")
        _sub(field, "fieldlabel", label)
        _sub(field, "fieldentry", entry)

    flow = _sub(_sub(item, "presentation", label=title), "flow")
    _material(flow, question["prompt"])

    resprocessing = _sub(item, "resprocessing")
    outcomes = _sub(resprocessing, "outcomes")
    _sub(outcomes, "decvar", varname="SCORE", vartype="Decimal", defaultval=0, minvalue=0, maxvalue=1)
    return flow, resprocessing


def _score(resprocessing, value, points, **varequal_attrs):
    condition = _sub(resprocessing, "respcondition", **{"continue": "Yes"})
    _sub(_sub(condition, "conditionvar"), "varequal", value, respident="RESPONSE", **varequal_attrs)
    _sub(condition, "setvar", points, varname="SCORE", action="Add")


def build_choice(parent, question, index):
    flow, resprocessing = _item(parent, question, index, "assSingleChoice", [("singleline", 1)])
    render = _sub(_sub(flow, "response_lid", ident="RESPONSE", rcardinality="Single"),
                  "render_choice", shuffle="No")
    for position, choice in enumerate(question["choices"], start=1):
        identifier = choice_identifier(choice, position)
        _material(_sub(render, "response_label", ident=identifier), choice["text"])
        _score(resprocessing, identifier, 1 if choice.get("correct") else 0)


def build_text_entry(parent, question, index):
    flow, resprocessing = _item(parent, question, index, "assClozeTest",
                                [("textgaprating", "cs"), ("identicalScoring", 1)])
    correct = question["correct"]
    response = _sub(flow, "response_str", ident="RESPONSE", rcardinality="Single")
    render = _sub(response, "render_fib", fibtype="String", prompt="Box", maxchars=max(20, len(correct)))
    _sub(render, "response_label", ident="GAP_1")
    _score(resprocessing, correct, 1, case="Yes")


BUILDERS = {
    "choice": build_choice,
    "text_entry": build_text_entry,
}


def build(data):
    root = etree.Element("questestinterop")
    for index, question in enumerate(data["qti"]["questions"], start=1):
        BUILDERS[question["type"]](root, question, index)
    etree.indent(root, space="    ")
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", doctype=DOCTYPE) + b"\n"


# --- Output validation ------------------------------------------------------


def validate_output(xml_bytes, target):
    parser = etree.XMLParser(no_network=True, load_dtd=False, resolve_entities=False)
    try:
        root = etree.fromstring(xml_bytes, parser)
    except etree.XMLSyntaxError as error:
        raise QtiError(f"{target}: output is not well-formed XML: {error}") from error
    dtd = etree.DTD(str(DTD_FILE))
    if not dtd.validate(root):
        errors = "\n".join(f"  line {e.line}: {e.message}" for e in dtd.error_log.filter_from_errors())
        raise QtiError(f"{target}: output does not validate against the QTI 1.2.1 DTD:\n{errors}")


# --- Entry points -----------------------------------------------------------


def convert(data, source, target):
    if not SAFE_FILE_STEM.match(target.stem):
        raise QtiError(f"Output file name may only contain letters, digits, '_', '-' and '.': {target.name}")
    validate_schema(data, source)
    xml_bytes = build(data)
    validate_output(xml_bytes, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(xml_bytes)
    print(f"{target}: wrote {len(data['qti']['questions'])} questions, validated", file=sys.stderr)


def load_file(path):
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix == ".json" else yaml.safe_load(text) or {}


def front_matter(path):
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\s*(\r?\n|\Z)", path.read_text(encoding="utf-8"), re.S)
    return (yaml.safe_load(match.group(1)) or {}) if match else {}


def document_data(qmd):
    meta = front_matter(qmd)
    merged = {}
    files = meta.get("metadata-files") or []
    for name in [files] if isinstance(files, str) else files:
        merged.update(load_file(qmd.parent / name))
    merged.update(meta)
    return {"qti": merged["qti"]} if "qti" in merged else None


def run_quarto_hook():
    inputs = [Path(p) for p in os.environ["QUARTO_PROJECT_INPUT_FILES"].splitlines() if p.endswith(".qmd")]
    output_dir = os.environ.get("QUARTO_PROJECT_OUTPUT_DIR")
    for qmd in inputs:
        data = document_data(qmd)
        if data is None:
            continue
        target_dir = Path(output_dir) / qmd.resolve().parent.relative_to(Path.cwd()) if output_dir else qmd.parent
        convert(data, str(qmd), target_dir / f"{qmd.stem}.xml")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("questions", nargs="?", type=Path, help="question JSON or YAML file")
    parser.add_argument("-o", "--output", type=Path, help="output XML file (default: <questions>.xml)")
    args = parser.parse_args(argv)

    try:
        if args.questions:
            convert(load_file(args.questions), str(args.questions),
                    args.output or args.questions.with_suffix(".xml"))
        elif "QUARTO_PROJECT_INPUT_FILES" in os.environ:
            run_quarto_hook()
        else:
            parser.error("a questions file is required outside a Quarto render")
    except (QtiError, OSError, json.JSONDecodeError, yaml.YAMLError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
