local M = {}

local ENTITIES = {
    ["&"] = "&amp;",
    ["<"] = "&lt;",
    [">"] = "&gt;",
    ['"'] = "&quot;",
    ["'"] = "&apos;",
}

function M.escape(text)
    return (tostring(text):gsub("[&<>\"']", ENTITIES))
end

-- Escapes every string in a nested table of template values.
function M.escape_values(value)
    if type(value) == "string" then
        return M.escape(value)
    end
    if type(value) ~= "table" then
        return value
    end
    local escaped = {}
    for key, inner in pairs(value) do
        escaped[key] = M.escape_values(inner)
    end
    return escaped
end

return M
