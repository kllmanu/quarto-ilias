local root = pandoc.path.directory(PANDOC_SCRIPT_FILE)
package.path = root .. "/?.lua;" .. package.path

local template = require("shared.template")
local xml = require("shared.xml")

-- Each type lives in interactions/<type>/ as <type>.lua and <type>.xml.
local INTERACTIONS = {
    choice = require("interactions.choice.choice"),
    text_entry = require("interactions.text_entry.text_entry"),
}

local function template_path(interaction_type)
    return string.format("%s/interactions/%s/%s.xml", root, interaction_type, interaction_type)
end

function Pandoc(doc)
    local qti = doc.meta.qti
    local interaction_type = pandoc.utils.stringify(qti.type or "choice")

    local interaction = INTERACTIONS[interaction_type]
    if not interaction then
        error("Unknown qti.type: " .. interaction_type)
    end

    local context = xml.escape_values(interaction.context(qti))
    local output = template.render(template_path(interaction_type), context)
    return pandoc.Pandoc({ pandoc.RawBlock("docbook", output) }, doc.meta)
end
