local meta = require("shared.meta")

local M = {}

-- Template values shared by every interaction type.
function M.base_context(question, index)
    local identifier = meta.field(question, "identifier", "")
    local title = meta.field(question, "title", "")
    local prompt = meta.field(question, "prompt", "")
    if identifier == "" then
        local label = title ~= "" and title or prompt
        local slug = label:gsub("[^A-Za-z0-9_.%-]+", "_")
        slug = slug:gsub("^_+", ""):gsub("_+$", ""):sub(1, 48)
        if slug == "" then
            slug = "QUESTION"
        end
        if not slug:match("^[A-Za-z_]") then
            slug = "Q_" .. slug
        end
        identifier = "ITEM_" .. slug .. "_" .. index
    end
    return {
        identifier = identifier,
        title = title ~= "" and title or identifier,
        prompt = prompt,
    }
end

return M
