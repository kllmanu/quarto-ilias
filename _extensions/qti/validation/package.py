"""Post-render hook: bundle each rendered QTI test and its items into a QTI 3.0 content package.

For every rendered qti-assessment-test, writes <name>.zip beside it, containing
imsmanifest.xml, the test file, and the items it references (<name>/<id>.xml).

Reads the files to package from QUARTO_PROJECT_OUTPUT_FILES, or from the command line.
Uses only the standard library, so it never needs the validation packages.
"""

import os
import pathlib
import posixpath
import sys
import zipfile
from xml.etree import ElementTree

TEST_NAMESPACE = "http://www.imsglobal.org/xsd/imsqtiasi_v3p0"
MANIFEST_NAMESPACE = "http://www.imsglobal.org/xsd/qti/qtiv3p0/imscp_v1p1"
MANIFEST_XSD = "https://purl.imsglobal.org/spec/qti/v3p0/schema/xsd/imsqtiv3p0_imscpv1p2_v1p0.xsd"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"

TEST_RESOURCE_TYPE = "imsqti_test_xmlv3p0"
ITEM_RESOURCE_TYPE = "imsqti_item_xmlv3p0"

MANIFEST_NAME = "imsmanifest.xml"


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
    return root.tag == f"{{{TEST_NAMESPACE}}}qti-assessment-test"


def item_path(test_path, href):
    """Resolve an item href, refusing anything that points outside the test's folder."""
    normalized = posixpath.normpath(href)
    if posixpath.isabs(normalized) or normalized == ".." or normalized.startswith("../"):
        raise PackageError(f"{test_path}: item href '{href}' points outside the output folder")
    path = test_path.parent / normalized
    if not path.is_file():
        raise PackageError(f"{test_path}: referenced item '{href}' does not exist")
    return normalized, path


def collect_items(test_path, test_root):
    """Returns [(href, identifier)] for the items a test references, in order and without duplicates."""
    items, seen = [], set()
    for ref in test_root.iter(f"{{{TEST_NAMESPACE}}}qti-assessment-item-ref"):
        href, path = item_path(test_path, ref.get("href", ""))
        if href in seen:
            continue
        seen.add(href)

        identifier = parse(path).get("identifier")
        if not identifier:
            raise PackageError(f"{path}: item has no identifier")
        items.append((href, identifier))
    return items


def build_manifest(test_path, test_identifier, items):
    ElementTree.register_namespace("", MANIFEST_NAMESPACE)
    ElementTree.register_namespace("xsi", XSI_NAMESPACE)

    def element(parent, name, **attributes):
        return ElementTree.SubElement(parent, f"{{{MANIFEST_NAMESPACE}}}{name}", attributes)

    manifest = ElementTree.Element(f"{{{MANIFEST_NAMESPACE}}}manifest", {
        "identifier": f"manifest_{test_path.stem}",
        f"{{{XSI_NAMESPACE}}}schemaLocation": f"{MANIFEST_NAMESPACE} {MANIFEST_XSD}",
    })

    metadata = element(manifest, "metadata")
    element(metadata, "schema").text = "QTI Package"
    element(metadata, "schemaversion").text = "3.0.0"
    element(manifest, "organizations")
    resources = element(manifest, "resources")

    # Prefixes keep resource ids unique even when a test and an item share an identifier.
    test_resource = element(resources, "resource",
                            identifier=f"test_{test_identifier}", type=TEST_RESOURCE_TYPE, href=test_path.name)
    element(test_resource, "file", href=test_path.name)
    for _, identifier in items:
        element(test_resource, "dependency", identifierref=f"item_{identifier}")

    for href, identifier in items:
        item_resource = element(resources, "resource",
                                identifier=f"item_{identifier}", type=ITEM_RESOURCE_TYPE, href=href)
        element(item_resource, "file", href=href)

    ElementTree.indent(manifest)
    return ElementTree.tostring(manifest, encoding="unicode", xml_declaration=False)


def package(test_path, test_root):
    test_identifier = test_root.get("identifier")
    if not test_identifier:
        raise PackageError(f"{test_path}: test has no identifier")

    items = collect_items(test_path, test_root)
    manifest = '<?xml version="1.0" encoding="UTF-8"?>\n' + build_manifest(test_path, test_identifier, items)

    target = test_path.with_suffix(".zip")
    # Write beside the target first, so a failure never leaves a truncated package behind.
    partial = target.with_name(target.name + ".partial")
    with zipfile.ZipFile(partial, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(MANIFEST_NAME, manifest)
        archive.write(test_path, test_path.name)
        for href, _ in items:
            archive.write(test_path.parent / href, href)
    partial.replace(target)
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
        except PackageError as error:
            failed = True
            print(f"Packaging failed: {error}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
