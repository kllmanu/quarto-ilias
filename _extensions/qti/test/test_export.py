"""Regression checks for the QTI 1.2.1 export and ILIAS 11 question profile."""

import copy
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from xml.parsers import expat

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "_extensions" / "qti" / "scripts"))

from environment import run_in_environment

run_in_environment()

from lxml import etree
from validate_output import DTD, check


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temporary.cleanup)
        cls.output = pathlib.Path(temporary.name)
        subprocess.run(["quarto", "render", "--output-dir", str(cls.output)], cwd=ROOT, check=True, capture_output=True,
                       env=os.environ | {"PYTHONDONTWRITEBYTECODE": "1"})
        cls.path = cls.output / "example.xml"
        cls.document = etree.parse(str(cls.path), etree.XMLParser(load_dtd=False, no_network=True))

    def test_dtd_and_profile(self):
        _, errors = check(etree.DTD(str(DTD)), self.path)
        self.assertEqual(errors, [])
        self.assertEqual(self.document.docinfo.system_url, "ims_qtiasiv1p2p1.dtd")
        self.assertEqual(len(self.document.getroot().findall("item")), 3)

    def test_ilias_comment_parent_lookup(self):
        for path in (self.path, self.output / "template.xml"):
            parser = expat.ParserCreate()
            state = {"depth": 0, "element": "", "path": {}}

            def begin(name, attributes):
                state["depth"] += 1
                state["path"][state["depth"]] = name
                state["element"] = name

            def end(name):
                state["depth"] -= 1

            def characters(text):
                if state["element"] in ("qticomment", "duration") and state["depth"] > 0:
                    self.assertIn(state["depth"] - 1, state["path"],
                                  f"{path.name}: ILIAS getParent would read an undefined path index")

            parser.StartElementHandler = begin
            parser.EndElementHandler = end
            parser.CharacterDataHandler = characters
            parser.Parse(path.read_bytes(), True)

    def test_single_choice_scoring_and_escaping(self):
        item = self.document.getroot().findall("item")[2]
        response = item.find(".//response_lid")
        self.assertEqual(response.get("rcardinality"), "Single")
        labels = response.findall("./render_choice/response_label")
        self.assertEqual(labels[0].findtext("./material/mattext"), "1/3 < 1/2")
        conditions = item.findall("./resprocessing/respcondition")
        scores = {condition.findtext("./conditionvar/varequal"): float(condition.findtext("setvar"))
                  for condition in conditions}
        self.assertEqual(scores, {labels[0].get("ident"): 1, labels[1].get("ident"): 0})

    def test_case_sensitive_text_gap(self):
        item = self.document.getroot().findall("item")[1]
        self.assertEqual(item.findtext("./presentation/flow/material/mattext"), "Schreibe 1/2 als Dezimalzahl:")
        equal = item.find("./resprocessing/respcondition/conditionvar/varequal")
        self.assertEqual(equal.text, "0.5")
        self.assertEqual(equal.get("case"), "Yes")
        self.assertEqual(item.find(".//render_fib").get("fibtype"), "String")

    def test_ilias_source_identifiers_and_external_ids(self):
        for position, item in enumerate(self.document.getroot().findall("item"), 1):
            self.assertRegex(item.get("ident"), r"^il_0_qst_[0-9]+$")
            self.assertEqual(item.get("ident"), f"il_0_qst_{position}")
            external_id = item.findtext(
                './itemmetadata/qtimetadata/qtimetadatafield[fieldlabel="externalId"]/fieldentry')
            self.assertTrue(external_id.startswith("ITEM_"))
        gap = self.document.getroot().findall("item")[1]
        self.assertEqual(gap.findtext(
            './itemmetadata/qtimetadata/qtimetadatafield[fieldlabel="externalId"]/fieldentry'),
            "ITEM_Fraction_to_decimal_2")

    def assert_rejected(self, document, message):
        with tempfile.TemporaryDirectory() as temporary:
            path = pathlib.Path(temporary) / "invalid.xml"
            document.write(str(path), encoding="UTF-8")
            _, errors = check(etree.DTD(str(DTD)), path)
            self.assertTrue(any(message in error for error in errors), errors)

    def test_duplicate_items_rejected(self):
        document = copy.deepcopy(self.document)
        document.getroot().append(copy.deepcopy(document.getroot().find("item")))
        self.assert_rejected(document, "duplicate item")

    def test_broken_scoring_reference_rejected(self):
        document = copy.deepcopy(self.document)
        document.find(".//varequal").set("respident", "MISSING")
        self.assert_rejected(document, "scoring response reference")

    def test_missing_ilias_source_identifier_rejected(self):
        document = copy.deepcopy(self.document)
        document.getroot().findall("item")[1].set("ident", "ITEM_Fraction_to_decimal_2")
        self.assert_rejected(document, "source installation identifier")

    def test_invalid_dtd_structure_rejected(self):
        document = copy.deepcopy(self.document)
        document.find(".//render_choice").set("shuffle", "invalid")
        self.assert_rejected(document, "shuffle")

    def test_xml_only_output(self):
        self.assertEqual({path.name for path in self.output.iterdir()}, {"example.xml", "template.xml"})


if __name__ == "__main__":
    unittest.main()