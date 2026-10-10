local item = require("lib.item")
local meta = require("lib.meta")

local M = {}

function M.context(qti)
    local context = item.base_context(qti)
    context.correct = meta.field(qti, "correct", "")
    return context
end

return M
