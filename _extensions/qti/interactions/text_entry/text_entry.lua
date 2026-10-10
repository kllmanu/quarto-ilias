local item = require("shared.item")
local meta = require("shared.meta")

local M = {}

function M.context(question, index)
    local context = item.base_context(question, index)
    context.correct = meta.field(question, "correct", "")
    return context
end

return M
