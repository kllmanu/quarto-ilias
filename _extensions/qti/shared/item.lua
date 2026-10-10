local meta = require("shared.meta")

local M = {}

-- Template values shared by every interaction type.
function M.base_context(question, index)
    local identifier = meta.field(question, "identifier", "ITEM_" .. index)
    return {
        identifier = identifier,
        title = meta.field(question, "title", identifier),
        prompt = meta.field(question, "prompt", ""),
    }
end

return M
