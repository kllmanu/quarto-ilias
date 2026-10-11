# Quarto QTI 1.2.1 Extension

This extension converts question JSON into an IMS QTI 1.2.1 question collection
for ILIAS 11: one `questestinterop` XML file containing all questions as `item`
elements. The conversion is done by a Python script,
`_extensions/qti/qti.py`, which validates the input against the JSON Schema,
builds the XML, and validates the result against the QTI 1.2.1 DTD before
writing it. It runs as a Quarto pre-render hook or standalone.

## Install

Start a new assessment project with the starter template:

```sh
quarto use template kllmanu/quarto-qti
```

Choose a directory name when prompted. Quarto copies the extension,
`_quarto.yml`, and `questions.json`, and renames `template.qmd` to match the
directory name. Edit `questions.json`, then run `quarto render` from the new
directory. Python 3 with the packages in `_extensions/qti/requirements.txt`
must be available to Quarto (`pip install -r _extensions/qti/requirements.txt`;
set `QUARTO_PYTHON` to pick a specific interpreter or virtual environment).
The validated question XML files are written to `_output/`.

To add only the extension to an existing project instead:

```sh
quarto add kllmanu/quarto-qti
```

This copies `_extensions/qti/` into your project. Add the hook to your
`_quarto.yml` (see [Validation](#validation)) and use `format: qti-html`.

## Use

Keep an exam's metadata in a JSON sidecar and include it from that document's
front matter. `questions.json` uses the extension's JSON Schema, so VS Code can
validate and complete the question structure while editing the data file.

```yaml
---
format: qti-html
metadata-files:
  - questions.json
---
```

The JSON file contains the `qti` object. Identifiers and titles are optional:

```json
{
  "$schema": "./_extensions/qti/schema/qti.schema.json",
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

See [template.qmd](template.qmd) and [questions.json](questions.json) for the
complete example. Each document can include its own metadata file, allowing
several exams in one project.

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

Render with:

```sh
quarto render
```

or convert a question file directly, without Quarto:

```sh
python3 _extensions/qti/qti.py questions.json -o quiz.xml
```

Rendering writes `quiz.xml` (named after `quiz.qmd`) with all questions
embedded, next to a `quiz.html` preview page. A project with an
`output-dir` gets its XML there. No separate item files or
assessment references are produced.

Each document gets its own output file, so one project can hold several
question collections:

```
_output/
  quiz.xml
  exam2.xml
```

The output file name may contain only letters, digits, underscores, hyphens and
periods.

Identifiers begin with a letter or underscore and may contain letters, digits,
underscores, periods and hyphens. They must be unique within a document, but two documents may reuse
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
Quote choice text that YAML could interpret as a boolean or number, such as
`"Yes"`, `"No"` or `"1"`, when writing questions in YAML.

## ILIAS Import

In an existing ILIAS 11 test question pool, open the questions list, select
Import, and upload the generated XML. Select the questions to import, then
check their prompts, correct answers, points, and previews. Add the imported
questions to a test and configure delivery settings within ILIAS.

The generated XML targets the [ILIAS 11 QTI 1.2 importers](https://github.com/ILIAS-eLearning/ILIAS/tree/release_11/components/ILIAS/TestQuestionPool/classes/import/qti12).
The DTD validates QTI structure, but an actual import into your ILIAS
installation is still needed to verify importer-specific behavior.

The JSON Schema entry point is `_extensions/qti/schema/qti.schema.json`. It
describes the assessment, `schema/question.schema.json` picks the schema for each
question's type, and shared fields live in `schema/item.schema.json`.

## Adding an interaction type

Write a `build_<type>(parent, question, index)` function in
`_extensions/qti/qti.py` (use `_item()` for the shared item skeleton) and
register it in `BUILDERS`. Add `interactions/<type>/<type>.schema.json` for the
question's shape, and add the type to the `enum` and an `if/then` branch in
`schema/question.schema.json`. lxml escapes text and attribute values.

## Validation

`qti.py` runs as a pre-render hook in your project's `_quarto.yml`:

```yaml
project:
  pre-render:
    - _extensions/qti/qti.py
```

For every rendered `.qmd` whose front matter provides `qti` (directly or via
`metadata-files`), it:

1. validates the questions against the JSON Schema and checks that question
   and choice identifiers are unique,
2. builds the `questestinterop` XML,
3. checks the XML is well-formed and validates it against the IMS QTI 1.2.1 DTD,
4. writes `<output-dir>/<document>.xml`.

Any error is reported with its location and stops the render; nothing is
written for an invalid collection. The standalone command performs the same
steps.

To cross-check an output file with `xmllint`:

```sh
xmllint --noout --nonet --path _extensions/qti/validation --valid _output/example.xml
```

DTD validation uses the local `validation/ims_qtiasiv1p2p1.dtd` file and disables
network access. The final IMS DTD (14 February 2003) is preserved unchanged from
[Pyslet's QTI 1.2.1 fixtures](https://github.com/swl10/pyslet/blob/master/unittests/data_imsqtiv1p2p1/ims_qtiasiv1p2p1.dtd).
The old QTI 3 XSD and catalog are removed.

## Development

The repository also serves as a [Quarto starter template](https://quarto.org/docs/extensions/starter-templates.html).
`template.qmd` is the starter document; `.quartoignore` excludes the development
example, rendered output, and Python bytecode from generated projects.

This repository renders every `.qmd` file with the hooks above, so
`quarto render` checks the extension itself. Keep one question of each
interaction type in `questions.json`.
