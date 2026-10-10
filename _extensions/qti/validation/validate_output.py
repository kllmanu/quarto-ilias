"""Post-render hook: validate rendered QTI files against the official QTI 3.0 XSD.

Reads the files to check from QUARTO_PROJECT_OUTPUT_FILES, or from the command line.
Requires `xmllint` (libxml2).
"""

import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
XSD = HERE / "xsd" / "imsqti_asiv3p0p1_v1p0.xsd"
CATALOG = HERE / "catalog.xml"
QTI_NAMESPACE = "http://www.imsglobal.org/xsd/imsqtiasi_v3p0"


def output_files():
    listed = sys.argv[1:] or os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "").split()
    return [pathlib.Path(name) for name in listed if name.endswith(".xml")]


def is_qti(path):
    return QTI_NAMESPACE in path.read_text(errors="replace")[:2000]


def main():
    xmllint = shutil.which("xmllint")
    if not xmllint:
        sys.exit("xmllint not found. Install libxml2 (Debian/Ubuntu: libxml2-utils, "
                 "Fedora: libxml2, macOS: brew install libxml2).")

    # The catalog redirects the schemas the XSD imports to local copies, so no network is needed.
    env = {**os.environ, "XML_CATALOG_FILES": str(CATALOG)}
    failed = False

    for path in output_files():
        if not is_qti(path):
            continue
        result = subprocess.run(
            [xmllint, "--noout", "--nonet", "--schema", str(XSD), str(path)],
            env=env, capture_output=True, text=True,
        )
        print((result.stdout + result.stderr).strip(), file=sys.stderr)
        failed = failed or result.returncode != 0

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
