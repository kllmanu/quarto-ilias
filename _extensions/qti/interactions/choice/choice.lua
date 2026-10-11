local item = require("shared.item")
local meta = require("shared.meta")

local M = {}

function M.context(question, index)
    local context = item.base_context(question, index)
    context.choices = {}

    for position, choice in ipairs(question.choices) do
        local identifier = meta.field(choice, "identifier", "CHOICE_" .. position)
        if meta.field(choice, "correct", "false") == "true" then
            context.correct = identifier
        end
        table.insert(context.choices, {
            identifier = identifier,
            text = meta.field(choice, "text", ""),
            points = meta.field(choice, "correct", "false") == "true" and "1" or "0",
        })
    end

    return context
end

return M
