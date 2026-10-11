"""Post-render hook: bundle a QTI 1.2.1 question document with its DTD.

Reads the files to package from QUARTO_PROJECT_OUTPUT_FILES, or from the command line.
Import the XML directly into an existing ILIAS question pool, not this portable ZIP.
"""

import os
import pathlib
import sys
import zipfile
from xml.etree import ElementTree

DTD = pathlib.Path(__file__).resolve().parent.parent / "validation" / "ims_qtiasiv1p2p1.dtd"


class PackageError(Exception):
    pass


def output_files():
    listed = sys.argv[1:] or os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "").split("\n")
    return [pathlib.Path(name.strip()) for name in listed if name.strip().endswith(".xml")]


def parse(path):
    try:
        return ElementTree.parse(path).getroot()
    except (OSError, ElementTree.ParseError) as error:
        raise PackageError(f"{path}: {error}") from error


def is_test(root):
    return root.tag == "questestinterop"


def package(test_path, test_root):
    items = test_root.findall("item")
    identifiers = [item.get("ident") for item in items]
    if (not items or any(child.tag not in ("item", "qticomment") for child in test_root)
            or not all(identifiers) or len(set(identifiers)) != len(items)):
        raise PackageError(f"{test_path}: expected question items with unique identifiers")
    if not DTD.is_file():
        raise PackageError(f"{test_path}: missing QTI 1.2.1 DTD")

    target = test_path.with_suffix(".zip")
    partial = target.with_name(target.name + ".partial")
    try:
        with zipfile.ZipFile(partial, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.write(test_path, test_path.name)
            archive.write(DTD, DTD.name)
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)
    return target, len(items)


def main():
    failed = False
    for path in output_files():
        try:
            root = parse(path)
            if not is_test(root):
                continue
            target, count = package(path, root)
            print(f"{target} packaged ({count} items)", file=sys.stderr)
        except (PackageError, OSError) as error:
            failed = True
            print(f"Packaging failed: {error}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
