# Quarto QTI 3.0 Extension

This extension renders a Quarto document as an IMS QTI 3.0 assessment: one
`qti-assessment-test` file that references one `qti-assessment-item` file per
question. Each question's `type` selects its interaction template.

## Install

```sh
quarto add <owner>/<repo>
```

This copies `_extensions/qti/` into your project. Rendering needs nothing else.
Use the format as `format: qti-docbook`.

## Use

Define the assessment in the root `qti` YAML field: an optional `identifier` and
`title`, and a list of `questions`. See [example.qmd](example.qmd) for a complete
document.

```yaml
qti:
  identifier: FRACTIONS_QUIZ
  title: "Fractions & decimals"
  questions:
    - type: choice
      identifier: ADD_FRACTIONS
      prompt: "What is 1/2 + 1/4?"
      choices:
        - identifier: A
          text: 1/4
        - identifier: B
          text: 3/4
          correct: true
    - type: text_entry
      identifier: HALF_AS_DECIMAL
      prompt: "Write 1/2 as a decimal:"
      correct: "0.5"
```

Every question has a `type` and a `prompt`, and an optional `identifier` and
`title`:

- **`choice`** needs at least two `choices`, each with `text` and an optional
  `identifier`. Mark exactly one `correct: true`.
- **`text_entry`** needs a `correct` string.

Render with:

```sh
quarto render quiz.qmd --to qti-docbook
```

This writes `quiz.xml` (the test) and a `quiz/` folder holding one
`<identifier>.xml` per question. The test refers to the items by relative path,
such as `quiz/ADD_FRACTIONS.xml`. A project with an `output-dir` gets all of them
there.

Each document gets its own folder, named after its output file, so one project can
hold several exams without their items colliding:

```
_output/
  quiz.xml   quiz/ADD_FRACTIONS.xml …   quiz.zip
  exam2.xml  exam2/ADD_FRACTIONS.xml …  exam2.zip
```

The output file name may contain only letters, digits, underscores, hyphens and
periods, because it becomes part of the item paths.

Identifiers begin with a letter or underscore and may contain letters, digits,
underscores, periods and hyphens, because a question's identifier is also its
file name. They must be unique within a document, but two documents may reuse
the same ones. Question identifiers default to `ITEM_1`, `ITEM_2` and so on,
choice identifiers to `CHOICE_1`, `CHOICE_2`, and the test's to `TEST_1`. Quote
choice text that YAML could interpret as a boolean or number, such as `"Yes"`,
`"No"` or `"1"`.

## Content packages

Importers usually expect a QTI content package. The optional `package.py`
post-render hook writes `<name>.zip` beside each test. It holds `imsmanifest.xml`
at the root, the test, and the items the test references. The manifest follows
the QTI 3.0 content packaging profile and lists the test with a dependency on
each item. It needs only Python 3 and no extra packages.

```yaml
project:
  render:
    - "*.qmd"
  post-render:
    - _extensions/qti/validation/validate_output.py
    - _extensions/qti/validation/package.py
```

List it after the validation hook: Quarto stops at the first failing hook, so an
invalid exam is never packaged. Packaging also fails, leaving no zip, if the test
references a missing item or a path outside the output folder.

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

Validation is optional and ships with the extension. Add the two hooks to your
project's `_quarto.yml` (see above for adding packaging as well):

```yaml
project:
  pre-render: _extensions/qti/validation/validate_front_matter.py
  post-render: _extensions/qti/validation/validate_output.py
```

- **pre-render** validates each document's `qti` front matter against the JSON
  Schema and stops the render on an error. Documents without a `qti` key are
  skipped.
- **post-render** validates every generated QTI test against the official IMS
  QTI 3.0 XSD using `lxml`, and every item file it references. A missing item
  file fails. Other XML files are skipped.

Both hooks need Python 3 and a few packages from `requirements.txt` (`jsonschema`,
`pyyaml` and `lxml`):

```sh
python3 -m venv .venv
.venv/bin/pip install -r _extensions/qti/validation/requirements.txt
PATH="$PWD/.venv/bin:$PATH" quarto render
```

If a dependency is missing, the affected hook prints a message naming it and
skips its check, and the render continues. Invalid front matter or invalid XML
still fails the render.

The XSD is validated offline. `validation/catalog.xml` maps the schemas it
imports to local copies in `validation/xsd/`, with a small stub standing in for
MathML, which this extension never emits. The IMS schemas keep their original
licence notices.

## Development

This repository renders every `.qmd` file with the hooks above, so
`quarto render` checks the extension itself. Keep one question of each
interaction type in `example.qmd`.
