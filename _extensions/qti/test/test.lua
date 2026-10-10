local meta = require("shared.meta")

local M = {}

-- `items` lists the written item files as { identifier, href } pairs, in question order.
function M.context(qti, items)
    local identifier = meta.field(qti, "identifier", "TEST_1")
    return {
        identifier = identifier,
        title = meta.field(qti, "title", identifier),
        items = items,
    }
end

return M
