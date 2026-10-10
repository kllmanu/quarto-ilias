# Quarto QTI 2.1 Extension

This extension renders a Quarto document as a standalone IMS QTI 2.1
`assessmentItem` XML file. The root `qti.type` selects the interaction template.

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

The output is `assessment.xml`. QTI identifiers must begin with a letter or
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
