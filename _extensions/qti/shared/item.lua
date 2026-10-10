local meta = require("shared.meta")

local M = {}

-- Template values shared by every interaction type.
function M.base_context(qti)
    local identifier = meta.field(qti, "identifier", "ITEM_1")
    return {
        identifier = identifier,
        title = meta.field(qti, "title", identifier),
        prompt = meta.field(qti, "prompt", ""),
    }
end

return M
