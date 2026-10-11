# Quarto QTI 1.2.1 Extension

This extension converts question JSON into an IMS QTI 1.2.1 question collection
for ILIAS 11: one `questestinterop` XML file containing all questions as `item`
elements. The conversion is done by a Python script,
`_extensions/qti/qti.py`, which validates the input against the JSON Schema,
builds the XML, and validates the result against the QTI 1.2.1 DTD before
writing it. Run it from the command line with the questions file and an output
path.

## Install

Start a new assessment project with the starter template:

```sh
quarto use template kllmanu/quarto-qti
```

Choose a directory name when prompted. Quarto copies the extension,
`_quarto.yml`, and `questions.json`, and renames `template.qmd` to match the
directory name. Edit `questions.json`, then run the converter (see
[Convert](#convert)). It needs Python 3 with the packages in
`_extensions/qti/requirements.txt`:

```sh
pip install -r _extensions/qti/requirements.txt
```

To add only the extension to an existing project instead:

```sh
quarto add kllmanu/quarto-qti
```

This copies `_extensions/qti/` into your project.

## Use

Keep an exam's questions in a JSON file. `questions.json` uses the extension's
JSON Schema, so VS Code can validate and complete the question structure while
editing it.

```json
{
  "$schema": "./_extensions/qti/qti.schema.json",
  "qti": {
    "title": "Fractions & decimals",
    "questions": [
      {
        "type": "choice",
        "prompt": "What is 1/2 + 1/4?",
        "choices": [{ "text": "1/4" }, { "text": "3/4", "correct": true }]
      },
      {
        "type": "text_entry",
        "prompt": "Write 1/2 as a decimal:",
        "correct": "0.5"
      }
    ]
  }
}
```

See [questions.json](questions.json) for the complete example. Use one JSON
file per exam.

Every question has a `type` and a `prompt`, and an optional `identifier` and
`title`:

- **`choice`** needs at least two `choices`, each with `text` and an optional
  `identifier`. Mark exactly one `correct: true`.
- **`text_entry`** needs a `correct` string.

`choice` exports as ILIAS `assSingleChoice`, with one selection, one point for
the correct choice, and zero for other choices. Answer order is fixed.
`text_entry` exports as `assClozeTest` with one string gap and a case-sensitive
correct answer worth one point. It is not a manually graded essay or a numeric
gap. The prompt becomes the question text and the gap is the answer field.
The author metadata defaults to `Quarto QTI`, and the content editing mode is
`default` (ILIAS's regular editor).

## Convert

```sh
python3 _extensions/qti/qti.py questions.json -o _output/quiz.xml
```

Both the questions file and `-o/--output` are required. The output directory
is created if needed. The XML contains all questions; no separate item files or
assessment references are produced.

The output file name may contain only letters, digits, underscores, hyphens and
periods.

Identifiers begin with a letter or underscore and may contain letters, digits,
underscores, periods and hyphens. They must be unique within a file, but two files may reuse
the same ones. Question identifiers are optional; when omitted, one is generated
from the question title, or from its prompt if there is no title. The question
position is included so repeated titles still produce unique identifiers.
In exported XML, item `ident` values use `il_0_qst_1`, `il_0_qst_2`, and so on.
ILIAS 11 requires this pattern to derive a non-null source installation ID for
text-gap imports, even without images. Authored or generated question identifiers
are retained separately in the `externalId` metadata; question titles are unchanged.
Choice identifiers default to `CHOICE_1`, `CHOICE_2`, and so on. The collection
title and identifier are optional and do not create or configure an ILIAS test
or rename the destination pool. They are not emitted in question-only XML:
a root `qticomment` followed by formatting whitespace triggers a parent-lookup
bug in ILIAS 11's importer. Question titles and identifiers are still emitted.
Generated identifiers replace characters outside the QTI identifier pattern
with underscores and are valid even when the source text starts with a digit.

## ILIAS Import

In an existing ILIAS 11 test question pool, open the questions list, select
Import, and upload the generated XML. Select the questions to import, then
check their prompts, correct answers, points, and previews. Add the imported
questions to a test and configure delivery settings within ILIAS.

The generated XML targets the [ILIAS 11 QTI 1.2 importers](https://github.com/ILIAS-eLearning/ILIAS/tree/release_11/components/ILIAS/TestQuestionPool/classes/import/qti12).
The DTD validates QTI structure, but an actual import into your ILIAS
installation is still needed to verify importer-specific behavior.

The JSON Schema is `_extensions/qti/qti.schema.json`. `$defs/question` picks
the definition for each question's type (`$defs/choice`, `$defs/text_entry`),
and shared fields are `$defs/identifier`, `$defs/title` and `$defs/prompt`.

## Adding an interaction type

Write a `build_<type>(parent, question, index)` function in
`_extensions/qti/qti.py` (use `_item()` for the shared item skeleton) and
register it in `BUILDERS`. In `_extensions/qti/qti.schema.json`, add a
`$defs/<type>` definition for the question's shape, and add the type to the
`enum` and an `if/then` branch in `$defs/question`. lxml escapes text and attribute values.

## Validation

`qti.py`:

1. validates the questions against the JSON Schema and checks that question
   and choice identifiers are unique,
2. builds the `questestinterop` XML,
3. checks the XML is well-formed and validates it against the IMS QTI 1.2.1 DTD,
4. writes the output file.

Any error is reported with its location and exits with status 1; nothing is
written for an invalid collection.

To cross-check an output file with `xmllint`:

```sh
xmllint --noout --nonet --path _extensions/qti --valid _output/example.xml
```

DTD validation uses the local `_extensions/qti/qti.dtd` file and disables
network access. The output's DOCTYPE refers to `qti.dtd`; `catalog.xml` maps it
to the extension's copy for VS Code. The final IMS DTD (14 February 2003) is preserved unchanged from
[Pyslet's QTI 1.2.1 fixtures](https://github.com/swl10/pyslet/blob/master/unittests/data_imsqtiv1p2p1/ims_qtiasiv1p2p1.dtd).

## Development

The repository also serves as a [Quarto starter template](https://quarto.org/docs/extensions/starter-templates.html).
`template.qmd` is the starter document; `.quartoignore` excludes the development
example, rendered output, and Python bytecode from generated projects.

This repository renders every `.qmd` file with the hooks above, so
`quarto render` checks the extension itself. Keep one question of each
interaction type in `questions.json`.
