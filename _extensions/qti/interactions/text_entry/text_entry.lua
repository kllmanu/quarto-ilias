local item = require("shared.item")
local meta = require("shared.meta")

local M = {}

function M.context(qti)
    local context = item.base_context(qti)
    context.correct = meta.field(qti, "correct", "")
    return context
end

return M
