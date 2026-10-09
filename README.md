# Quarto QTI 2.1 Extension

This extension renders one Quarto document as a standalone IMS QTI 2.1
`assessmentItem` XML file. It currently supports single-answer multiple-choice
questions with plain-text prompts and choices.

## Use

Define the question in the root `qti` YAML field. Include an item identifier,
title, prompt, and at least two choices. Mark exactly one choice `correct: true`.

```yaml
qti:
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

Render with:

```sh
quarto render question.qmd --to qti-docbook
```

The output is `assessment.xml`. QTI identifiers must begin with a letter or
underscore and may contain letters, digits, underscores, periods, and hyphens.
Item identifiers default to `ITEM_1`; choice identifiers default to
`CHOICE_1`, `CHOICE_2`, and so on.

The Lua filter validates the `qti` object and supplies normalized values to the
QTI XML template.
