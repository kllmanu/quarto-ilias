local item = require("shared.item")
local meta = require("shared.meta")

local M = {}

function M.context(qti)
    local context = item.base_context(qti)
    context.choices = {}

    for index, choice in ipairs(qti.choices) do
        local identifier = meta.field(choice, "identifier", "CHOICE_" .. index)
        if meta.field(choice, "correct", "false") == "true" then
            context.correct = identifier
        end
        table.insert(context.choices, {
            identifier = identifier,
            text = meta.field(choice, "text", ""),
        })
    end

    return context
end

return M
