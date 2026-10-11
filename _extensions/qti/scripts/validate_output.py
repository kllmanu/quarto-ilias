"""Post-render hook: validate QTI 1.2.1 question documents for ILIAS 11.

Reads the files to check from QUARTO_PROJECT_OUTPUT_FILES, or from the command line.
"""

import os
import pathlib
import re
import sys

from environment import run_in_environment

run_in_environment()

HERE = pathlib.Path(__file__).resolve().parent
DTD = HERE.parent / "validation" / "ims_qtiasiv1p2p1.dtd"

try:
    from lxml import etree
except ImportError as error:
    print(f"QTI validation failed: missing Python package '{error.name}'. "
        f"Dependencies are listed in {HERE.parent / 'requirements.txt'}. "
        "Remove the cached QTI environment and rerun the setup hook.", file=sys.stderr)
    sys.exit(1)


def output_files():
    listed = sys.argv[1:] or os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "").splitlines()
    return [pathlib.Path(name.strip()) for name in listed if name.strip().endswith(".xml")]


def is_qti(path):
    return "questestinterop" in path.read_text(errors="replace")[:2000]


def check(schema, path):
    try:
        parser = etree.XMLParser(load_dtd=False, resolve_entities=False, no_network=True)
        document = etree.parse(str(path), parser)
    except (OSError, etree.XMLSyntaxError) as error:
        return None, [f"{path}: {error}"]

    errors = []
    if document.docinfo.internalDTD is not None and list(document.docinfo.internalDTD.iterentities()):
        errors.append(f"{path}: custom XML entities are not supported")
    if not schema.validate(document):
        errors.extend(f"{path}:{error.line}: {error.message}" for error in schema.error_log)
    root = document.getroot()
    if root.tag != "questestinterop" or any(child.tag not in ("item", "qticomment") for child in root):
        errors.append(f"{path}: expected question-only questestinterop containing items")
    seen = set()
    for item in root.findall("item"):
        identifier = item.get("ident")
        if not re.fullmatch(r"il_[0-9]+_qst_[0-9]+", identifier or ""):
            errors.append(f"{path}: {identifier}: missing ILIAS source installation identifier")
        if identifier in seen:
            errors.append(f"{path}: duplicate item identifier {identifier}")
        seen.add(identifier)
        metadata = {field.findtext("fieldlabel"): field.findtext("fieldentry")
                    for field in item.findall("./itemmetadata/qtimetadata/qtimetadatafield")}
        question_type = metadata.get("QUESTIONTYPE")
        response_tag = {"assSingleChoice": "response_lid", "assClozeTest": "response_str"}.get(question_type)
        responses = item.findall(f".//{response_tag}") if response_tag else []
        if len(responses) != 1 or responses[0].get("rcardinality") != "Single":
            errors.append(f"{path}: {identifier}: unsupported question type or response cardinality")
            continue
        if not item.get("title") or not metadata.get("AUTHOR") or not item.findtext(".//presentation/flow/material/mattext"):
            errors.append(f"{path}: {identifier}: missing title, author, or prompt")
        response = responses[0]
        conditions = item.findall("./resprocessing/respcondition")
        answers = []
        points = []
        for condition in conditions:
            equal = condition.find("./conditionvar/varequal")
            score = condition.find("setvar")
            if equal is None or equal.get("respident") != response.get("ident") or score is None:
                errors.append(f"{path}: {identifier}: invalid scoring response reference")
                continue
            answers.append(equal.text)
            try:
                points.append(float(score.text))
            except (ValueError, TypeError):
                errors.append(f"{path}: {identifier}: invalid score")
            if score.get("action") != "Add" or score.get("varname", "SCORE") != "SCORE":
                errors.append(f"{path}: {identifier}: unsupported scoring action")
        if points.count(1.0) != 1 or any(point not in (0.0, 1.0) for point in points):
            errors.append(f"{path}: {identifier}: expected exactly one one-point answer")
        if question_type == "assSingleChoice":
            labels = [label.get("ident") for label in response.findall("./render_choice/response_label")]
            if len(labels) < 2 or len(set(labels)) != len(labels) or len(answers) != len(labels) or set(answers) != set(labels):
                errors.append(f"{path}: {identifier}: choice labels and scoring answers must match uniquely")
        else:
            equal = item.find("./resprocessing/respcondition/conditionvar/varequal")
            renderer = response.find("render_fib")
            if (len(conditions) != 1 or not answers or not answers[0] or metadata.get("textgaprating") != "cs"
                    or equal is None or equal.get("case") != "Yes"
                    or renderer is None or renderer.get("fibtype") != "String"):
                errors.append(f"{path}: {identifier}: expected one case-sensitive text gap answer")
    return document, errors


def main():
    queue = [path for path in output_files() if is_qti(path)]
    if not queue:
        return 0

    schema = etree.DTD(str(DTD))
    failed = False

    for path in queue:
        _, errors = check(schema, path)
        if errors:
            failed = True
            print(f"{path} fails to validate", file=sys.stderr)
            print("\n".join(errors), file=sys.stderr)
        else:
            print(f"{path} validates", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
