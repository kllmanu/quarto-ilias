# Quarto QTI 1.2.1 Extension

This extension renders a Quarto document as an IMS QTI 1.2.1 question collection
for ILIAS 11: one `questestinterop` XML file containing all questions as `item`
elements. Each question's `type` selects its interaction template. QTI 3.0 is
no longer emitted.

## Install

Start a new assessment project with the starter template:

```sh
quarto use template kllmanu/quarto-qti
```

Choose a directory name when prompted. Quarto copies the extension,
`_quarto.yml`, and `questions.json`, and renames `template.qmd` to match the
directory name. Edit `questions.json`, then run `quarto render` from the new
directory. The `jsonschema` CLI and `xmllint` must be installed and available on
`PATH` for validation. The validated question XML files are written to
`_output/`.

To add only the extension to an existing project instead:

```sh
quarto add kllmanu/quarto-qti
```

This copies `_extensions/qti/` into your project. Base rendering needs nothing
else. Use the format as `format: qti-docbook`.

## Use

Keep an exam's metadata in a JSON sidecar and include it from that document's
front matter. `questions.json` uses the extension's JSON Schema, so VS Code can
validate and complete the question structure while editing the data file.

```yaml
---
format: qti-docbook
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
quarto render quiz.qmd --to qti-docbook
```

Rendering writes `quiz.xml` with all questions embedded. A project with an
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
identifier is also optional. When omitted, it is generated deterministically
from the collection title, or from the output file name if there is no title.
The collection title and identifier do not create or configure an ILIAS test
or rename the destination pool. They are not emitted in question-only XML:
a root `qticomment` followed by formatting whitespace triggers a parent-lookup
bug in ILIAS 11's importer. Question titles and identifiers are still emitted.
Generated identifiers replace characters outside the QTI identifier pattern
with underscores and are valid even when the source text starts with a digit.
Quote choice text that YAML could interpret as a boolean or number, such as
`"Yes"`, `"No"` or `"1"`.

## ILIAS Import

In an existing ILIAS 11 test question pool, open the questions list, select
Import, and upload the generated XML. Select the questions to import, then
check their prompts, correct answers, points, and previews. Add the imported
questions to a test and configure delivery settings within ILIAS.

The templates target the [ILIAS 11 QTI 1.2 importers](https://github.com/ILIAS-eLearning/ILIAS/tree/release_11/components/ILIAS/TestQuestionPool/classes/import/qti12).
The DTD validates QTI structure, but an actual import into your ILIAS
installation is still needed to verify importer-specific behavior.

The JSON Schema entry point is `_extensions/qti/schema/qti.schema.json`. It
describes the assessment, `schema/question.schema.json` picks the schema for each
question's type, and shared fields live in `schema/item.schema.json`.

## Adding an interaction type

Each type lives in `_extensions/qti/interactions/<type>/` as `<type>.lua`
(returns `context(question, index)`, the template values), `<type>.xml` (a
complete QTI item template), and `<type>.schema.json` (the question's shape).
Register the module in `INTERACTIONS` in `_extensions/qti/filter.lua`, and add the
type to the `enum` and an `if/then` branch in `schema/question.schema.json`.
Values are XML-escaped by the dispatcher, so modules return plain strings.

Filter guards must use `assert`, not `error`: under Quarto, `error()` only logs
and the filter keeps running.

## Validation

The render hooks in `_extensions/qti/scripts/` use the `jsonschema` and
`xmllint` command-line tools. Configure them in your project's `_quarto.yml`:

```yaml
project:
  pre-render:
    - _extensions/qti/scripts/validate_front_matter.sh
  post-render: _extensions/qti/scripts/validate_output.sh
```

- **pre-render** validates `questions.json` against the assessment JSON Schema
  and stops the render on an error. Set `QTI_QUESTIONS_FILE` if the file has a
  different path. For projects with multiple assessment JSON files, run the
  `jsonschema validate` command for each file.
- **post-render** validates generated `questestinterop` XML against the IMS QTI
  1.2.1 DTD. Other XML files are skipped. This checks XML syntax and DTD
  structure; it does not perform the additional ILIAS profile checks previously
  handled by the Python validator.

Install the `jsonschema` CLI and `xmllint` yourself; no Python environment or
package setup is needed. Then render normally:

```sh
quarto render
```

To run the checks manually:

```sh
jsonschema validate _extensions/qti/schema/qti.schema.json questions.json
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
