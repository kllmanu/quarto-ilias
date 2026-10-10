# Quarto QTI 3.0 Extension

This extension renders a Quarto document as a standalone IMS QTI 3.0
`qti-assessment-item` XML file. The root `qti.type` selects the interaction template.

## Install

```sh
quarto add <owner>/<repo>
```

This copies `_extensions/qti/` into your project. Rendering needs nothing else.
Use the format as `format: qti-docbook`.

## Use

Define the question in the root `qti` YAML field. Include an item identifier,
title, prompt, and at least two choices. Mark exactly one choice `correct: true`.

```yaml
qti:
  type: choice
  identifier: FRACTIONS_1
  title: "Fractions & addition"
  prompt: "What is 1/2 + 1/4?"
  choices:
    - identifier: A
      text: 1/4
    - identifier: B
      text: 3/4
      correct: true
    - identifier: C
      text: "1"
```

Text-entry questions use `type: text_entry` and a single `correct` string:

```yaml
qti:
  type: text_entry
  identifier: HELLO_ENTRY
  title: Hello
  prompt: "Type the greeting shown below:"
  correct: "Hello, example!"
```

Render with:

```sh
quarto render question.qmd --to qti-docbook
```

The output is written next to the source name with an `.xml` extension, for
example `question.xml`. QTI identifiers must begin with a letter or
underscore and may contain letters, digits, underscores, periods, and hyphens.
Item identifiers default to `ITEM_1`; choice identifiers default to
`CHOICE_1`, `CHOICE_2`, and so on.
Quote choice text that YAML could interpret as a boolean or number, such as
`"Yes"`, `"No"`, or `"1"`.

The JSON Schema entry point is `_extensions/qti/schema/qti.schema.json`. It
composes one schema per interaction type, and shared fields live in
`schema/item.schema.json`.

## Adding an interaction type

Each type lives in `_extensions/qti/interactions/<type>/` as `<type>.lua`
(returns `context(qti)`, the template values), `<type>.xml` (a complete QTI
document template), and `<type>.schema.json` (its front matter shape). Register
the module in `INTERACTIONS` in `_extensions/qti/filter.lua` and add a `$ref` to
the schema in `schema/qti.schema.json`. Values are XML-escaped by the
dispatcher, so modules return plain strings.

## Validation

Validation is optional and ships with the extension. Add the two hooks to your
project's `_quarto.yml`:

```yaml
project:
  pre-render: _extensions/qti/validation/validate_front_matter.py
  post-render: _extensions/qti/validation/validate_output.py
```

- **pre-render** validates each document's `qti` front matter against the JSON
  Schema and stops the render on an error. Documents without a `qti` key are
  skipped.
- **post-render** validates every generated QTI XML file against the official
  IMS QTI 3.0 XSD using `lxml`. Other XML files are skipped.

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

This repository renders `examples/*.qmd` with the hooks above, so `quarto
render` checks the extension itself. Add one example per interaction type.
