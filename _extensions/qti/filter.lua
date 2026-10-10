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
    local folder = "interactions/" .. interaction_type
    local output = template.render(template_file(folder, interaction_type), xml.escape_values(context))
    return context.identifier, output
end

function Pandoc(doc)
    local qti = doc.meta.qti
    local output_file = quarto.doc.output_file
    local output_dir = pandoc.path.directory(output_file)
    local test_file_name = pandoc.path.filename(output_file)

    local items, pending, seen = {}, {}, {}
    for index, question in ipairs(qti.questions) do
        local identifier, output = build_item(question, index)
        local href = files.item_file_name(identifier)

        assert(not seen[identifier], "Duplicate question identifier: " .. identifier)
        assert(href ~= test_file_name, "Question identifier '" .. identifier .. "' would overwrite the test file " .. href)
        seen[identifier] = true

        table.insert(pending, { path = output_dir .. "/" .. href, content = output })
        table.insert(items, { identifier = identifier, href = href })
    end

    -- Write only after every question passed its guards, so a failure leaves no partial output.
    for _, file in ipairs(pending) do
        files.write(file.path, file.content)
    end

    local context = xml.escape_values(assessment_test.context(qti, items))
    local output = template.render(template_file("test", "test"), context)
    return pandoc.Pandoc({ pandoc.RawBlock("docbook", output) }, doc.meta)
end
