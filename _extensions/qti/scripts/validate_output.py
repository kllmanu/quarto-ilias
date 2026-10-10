"""Post-render hook: validate rendered QTI files against the official QTI 3.0 XSD.

Reads the files to check from QUARTO_PROJECT_OUTPUT_FILES, or from the command line.
For a test file, every item it references is validated too.
"""

import os
import pathlib
import sys

from environment import run_in_environment

run_in_environment()

HERE = pathlib.Path(__file__).resolve().parent
XSD = HERE.parent / "validation" / "xsd" / "imsqti_asiv3p0p1_v1p0.xsd"
CATALOG = HERE.parent / "validation" / "catalog.xml"
QTI_NAMESPACE = "http://www.imsglobal.org/xsd/imsqtiasi_v3p0"

# libxml2 reads the catalog on first use, so set it before importing lxml.
# It redirects the schemas the XSD imports to local copies, so no network is needed.
os.environ["XML_CATALOG_FILES"] = str(CATALOG)

try:
    from lxml import etree
except ImportError as error:
    print(f"QTI validation failed: missing Python package '{error.name}'. "
        f"Dependencies are listed in {HERE.parent / 'requirements.txt'}. "
        "Remove the cached QTI environment and rerun the setup hook.", file=sys.stderr)
    sys.exit(1)


def output_files():
    listed = sys.argv[1:] or os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "").split()
    return [pathlib.Path(name) for name in listed if name.endswith(".xml")]


def is_qti(path):
    return QTI_NAMESPACE in path.read_text(errors="replace")[:2000]


def check(schema, path):
    """Validate one file. Returns its parsed document (None if unreadable) and any error messages."""
    try:
        document = etree.parse(str(path))
    except (OSError, etree.XMLSyntaxError) as error:
        return None, [f"{path}: {error}"]

    if schema.validate(document):
        return document, []
    return document, [f"{path}:{error.line}: {error.message}" for error in schema.error_log]


def referenced_items(path, document):
    refs = document.getroot().iter(f"{{{QTI_NAMESPACE}}}qti-assessment-item-ref")
    return [path.parent / ref.get("href") for ref in refs]


def main():
    queue = [path for path in output_files() if is_qti(path)]
    if not queue:
        return 0

    schema = etree.XMLSchema(etree.parse(str(XSD)))
    checked = set()
    failed = False

    while queue:
        path = queue.pop(0)
        if path in checked:
            continue
        checked.add(path)

        document, errors = check(schema, path)
        if errors:
            failed = True
            print(f"{path} fails to validate", file=sys.stderr)
            print("\n".join(errors), file=sys.stderr)
        else:
            print(f"{path} validates", file=sys.stderr)

        if document is not None:
            queue.extend(referenced_items(path, document))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
