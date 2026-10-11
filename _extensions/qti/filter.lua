local root = pandoc.path.directory(PANDOC_SCRIPT_FILE)
package.path = root .. "/?.lua;" .. package.path

local files = require("shared.files")
local meta = require("shared.meta")
local template = require("shared.template")
local xml = require("shared.xml")
local assessment_test = require("test.test")

-- Guards use assert: under Quarto, error() only logs and the filter keeps running.

-- Each type lives in interactions/<type>/ as <type>.lua and <type>.xml.
local INTERACTIONS = {
    choice = require("interactions.choice.choice"),
    text_entry = require("interactions.text_entry.text_entry"),
}

local function template_file(folder, name)
    return string.format("%s/%s/%s.xml", root, folder, name)
end

-- Returns the question's identifier and its complete QTI item document.
local function build_item(question, index)
    local interaction_type = meta.field(question, "type", "")
    local interaction = INTERACTIONS[interaction_type]
    assert(interaction, "Unknown question type: " .. interaction_type)

    local context = interaction.context(question, index)
    local identifier = context.identifier
    context.external_id = identifier
    context.identifier = "il_0_qst_" .. index
    local folder = "interactions/" .. interaction_type
    local output = xml.format(template.render(template_file(folder, interaction_type), xml.escape_values(context)))
    return identifier, output
end

function Pandoc(doc)
    local qti = doc.meta.qti
    local output_file = quarto.doc.output_file
    local exam_folder = files.exam_folder_name(pandoc.path.filename(output_file))

    local items, seen = {}, {}
    for index, question in ipairs(qti.questions) do
        local identifier, output = build_item(question, index)

        assert(not seen[identifier], "Duplicate question identifier: " .. identifier)
        seen[identifier] = true

        table.insert(items, { identifier = identifier, content = output })
    end

    local context = xml.escape_values(assessment_test.context(qti, {}, exam_folder))
    context.items = items
    local output = xml.format(template.render(template_file("test", "test"), context))
    return pandoc.Pandoc({ pandoc.RawBlock("docbook", output) }, doc.meta)
end
