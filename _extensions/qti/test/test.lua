local meta = require("shared.meta")

local M = {}

local function generated_identifier(value)
    local identifier = value:gsub("[^A-Za-z0-9_.%-]+", "_")
    identifier = identifier:gsub("^_+", ""):gsub("_+$", "")
    if identifier == "" then
        identifier = "TEST"
    end
    if not identifier:match("^[A-Za-z_]") then
        identifier = "TEST_" .. identifier
    end
    return identifier
end

-- `items` lists the written item files as { identifier, href } pairs, in question order.
function M.context(qti, items, output_name)
    local title = meta.field(qti, "title", "")
    local identifier = meta.field(qti, "identifier", "")
    if identifier == "" then
        identifier = generated_identifier(title ~= "" and title or output_name)
    end
    return {
        identifier = identifier,
        title = title ~= "" and title or identifier,
        items = items,
    }
end

return M
