local M = {}

local ENTITIES = {
    ["&"] = "&amp;",
    ["<"] = "&lt;",
    [">"] = "&gt;",
    ['"'] = "&quot;",
    ["'"] = "&apos;",
}

local function normalize_tag(tag)
    local output, quote, pending_space = {}, nil, false
    for index = 1, #tag do
        local character = tag:sub(index, index)
        if quote then
            table.insert(output, character)
            if character == quote then
                quote = nil
            end
        elseif character == '"' or character == "'" then
            if pending_space and #output > 0 then
                table.insert(output, " ")
                pending_space = false
            end
            quote = character
            table.insert(output, character)
        elseif character:match("%s") then
            pending_space = true
        else
            if pending_space and #output > 0 then
                table.insert(output, " ")
            end
            pending_space = false
            table.insert(output, character)
        end
    end
    return table.concat(output)
end

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

function M.format(document)
    local root = { children = {} }
    local stack = { root }
    local position = 1

    while position <= #document do
        local left = document:find("<", position, true)
        if not left then
            table.insert(stack[#stack].children, document:sub(position))
            break
        end
        if left > position then
            table.insert(stack[#stack].children, document:sub(position, left - 1))
        end

        local right = assert(document:find(">", left, true), "Invalid XML: unterminated tag")
        local tag = document:sub(left, right)
        if not tag:match("^<[%?!]") then
            tag = normalize_tag(tag)
        end
        if tag:match("^</") then
            local node = table.remove(stack)
            assert(node and node ~= root, "Invalid XML: unexpected closing tag")
            node.close = tag
        elseif tag:match("^<[%?!]") then
            table.insert(stack[#stack].children, tag)
        elseif tag:match("/%s*>$") then
            table.insert(stack[#stack].children, { open = tag, children = {}, self_closing = true })
        else
            local node = { open = tag, children = {} }
            table.insert(stack[#stack].children, node)
            table.insert(stack, node)
        end
        position = right + 1
    end

    assert(#stack == 1, "Invalid XML: unclosed element")

    local function has_element(children)
        for _, child in ipairs(children) do
            if type(child) == "table" then
                return true
            end
        end
        return false
    end

    local function has_text(children)
        for _, child in ipairs(children) do
            if type(child) == "string" and child:match("%S") then
                return true
            end
        end
        return false
    end

    local function inline(node)
        if type(node) == "string" then
            return node
        end
        if node.self_closing then
            return node.open
        end
        local children = {}
        for _, child in ipairs(node.children) do
            table.insert(children, inline(child))
        end
        return node.open .. table.concat(children) .. (node.close or "")
    end

    local function render(node, depth)
        if type(node) == "string" then
            return node
        end
        local indent = string.rep(" ", depth * 4)
        if node.self_closing then
            return indent .. node.open
        end

        if has_element(node.children) and not has_text(node.children) then
            local children = {}
            for _, child in ipairs(node.children) do
                if type(child) == "table" then
                    table.insert(children, render(child, depth + 1))
                end
            end
            return indent .. node.open .. "\n" .. table.concat(children, "\n") ..
                "\n" .. indent .. (node.close or "")
        end

        return indent .. inline(node)
    end

    local output = {}
    for _, child in ipairs(root.children) do
        if type(child) == "string" then
            if child:match("^<%?xml") then
                table.insert(output, child)
            elseif child:match("%S") then
                table.insert(output, child)
            end
        else
            table.insert(output, render(child, 0))
        end
    end
    return table.concat(output, "\n") .. "\n"
end

return M
