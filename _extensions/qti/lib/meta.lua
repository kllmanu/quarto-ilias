local M = {}

function M.field(map, name, default)
    local value = map[name]
    if value == nil then
        return default
    end
    return pandoc.utils.stringify(value)
end

return M
