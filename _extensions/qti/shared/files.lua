local M = {}

-- Matches the schema's identifier pattern; it has no path separators, so it is safe as a file name.
local SAFE_IDENTIFIER = "^[A-Za-z_][A-Za-z0-9_.%-]*$"

function M.item_file_name(identifier)
    assert(identifier:match(SAFE_IDENTIFIER), "Invalid QTI identifier (used as a file name): " .. identifier)
    return identifier .. ".xml"
end

function M.write(path, content)
    -- Quarto creates a project's output directory only when it moves the output there.
    pandoc.system.make_directory(pandoc.path.directory(path), true)
    local file = assert(io.open(path, "w"))
    file:write(content)
    file:close()
end

return M
