# Quarto QTI 2.1 Extension

This extension renders one Quarto document as a standalone IMS QTI 2.1
`assessmentItem` XML file. It currently supports single-answer multiple-choice
questions with plain-text prompts and choices.

## Use

Create a question using one `.qti-item` fenced div, containing its prompt and at
least two `.qti-choice` fenced divs. Mark exactly one choice `correct="true"`.

```markdown
::: {.qti-item identifier="FRACTIONS_1" title="Adding fractions"}
What is $1/2 + 1/4$?

::: {.qti-choice identifier="A"}
1/4
:::

::: {.qti-choice identifier="B" correct="true"}
3/4
:::

::: {.qti-choice identifier="C"}
1
:::
:::
```

Render with:

```sh
quarto render question.qmd --to qti-html
```

The output is `assessment.xml`. QTI identifiers must begin with a letter or
underscore and may contain letters, digits, underscores, periods, and hyphens.
Choice identifiers default to `CHOICE_1`, `CHOICE_2`, and so on.

The XML document structure is defined in `_extensions/qti/qti.xml`; the Lua
filter validates the item and supplies escaped values to that template.
