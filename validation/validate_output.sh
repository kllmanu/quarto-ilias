#!/usr/bin/env bash
# Post-render hook: validate every rendered XML file against the QTI 2.1 XSD.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export XML_CATALOG_FILES="$here/catalog.xml"

status=0
while IFS= read -r file; do
    [[ "$file" == *.xml ]] || continue
    xmllint --noout --nonet --schema "$here/xsd/imsqti_v2p1.xsd" "$file" || status=1
done <<< "${QUARTO_PROJECT_OUTPUT_FILES:-}"

exit "$status"
