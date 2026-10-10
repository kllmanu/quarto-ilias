"""Post-render hook: validate rendered QTI files against the official QTI 3.0 XSD.

Reads the files to check from QUARTO_PROJECT_OUTPUT_FILES, or from the command line.
"""

import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
XSD = HERE / "xsd" / "imsqti_asiv3p0p1_v1p0.xsd"
CATALOG = HERE / "catalog.xml"
QTI_NAMESPACE = "http://www.imsglobal.org/xsd/imsqtiasi_v3p0"

# libxml2 reads the catalog on first use, so set it before importing lxml.
# It redirects the schemas the XSD imports to local copies, so no network is needed.
os.environ["XML_CATALOG_FILES"] = str(CATALOG)

try:
    from lxml import etree
except ImportError as error:
    # Validation is optional, so a missing package must not fail the render.
    print(f"Skipping QTI validation: missing Python package '{error.name}'. "
          f"Install with: pip install -r {HERE / 'requirements.txt'}", file=sys.stderr)
    sys.exit(0)


def output_files():
    listed = sys.argv[1:] or os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "").split()
    return [pathlib.Path(name) for name in listed if name.endswith(".xml")]


def is_qti(path):
    return QTI_NAMESPACE in path.read_text(errors="replace")[:2000]


def main():
    paths = [path for path in output_files() if is_qti(path)]
    if not paths:
        return 0

    schema = etree.XMLSchema(etree.parse(str(XSD)))
    failed = False

    for path in paths:
        try:
            valid = schema.validate(etree.parse(str(path)))
            errors = [f"{path}:{error.line}: {error.message}" for error in schema.error_log]
        except etree.XMLSyntaxError as error:
            valid, errors = False, [f"{path}: {error}"]

        if valid:
            print(f"{path} validates", file=sys.stderr)
        else:
            failed = True
            print(f"{path} fails to validate", file=sys.stderr)
            print("\n".join(errors), file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
