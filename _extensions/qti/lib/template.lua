local M = {}

function M.render(path, context)
    local file = assert(io.open(path, "r"))
    local source = file:read("a")
    file:close()

    local template = pandoc.template.compile(source, path)
    return pandoc.layout.render(pandoc.template.apply(template, context))
end

return M
