local function attr(div, name, default)
    local value = div.attributes[name]
    if value == nil or value == "" then
        return default
    end
    return value
end

local function text(blocks)
    return pandoc.utils.stringify(blocks)
end

function Pandoc(doc)
    local items = {}
    for _, block in ipairs(doc.blocks) do
        if block.t == "Div" and block.classes:includes("qti-item") then
            table.insert(items, block)
        end
    end

    if #items ~= 1 then
        error("QTI output requires exactly one .qti-item block per document")
    end

    local item = items[1]
    local choices = {}
    local prompt = {}

    for _, block in ipairs(item.content) do
        if block.t == "Div" and block.classes:includes("qti-choice") then
            table.insert(choices, block)
        else
            table.insert(prompt, block)
        end
    end

    if #choices < 2 then
        error("A .qti-item must contain at least two .qti-choice blocks")
    end

    local correct_count = 0
    local correct_id = nil
    local template_choices = {}
    local used_ids = {}

    for index, choice in ipairs(choices) do
        local choice_id = attr(choice, "identifier", "CHOICE_" .. index)
        if not choice_id:match("^[A-Za-z_][A-Za-z0-9_.%-]*$") then
            error("Invalid QTI choice identifier: " .. choice_id)
        end
        if used_ids[choice_id] then
            error("Duplicate QTI choice identifier: " .. choice_id)
        end
        used_ids[choice_id] = true

        if attr(choice, "correct", "false") == "true" then
            correct_count = correct_count + 1
            correct_id = choice_id
        end

        table.insert(template_choices, {
            identifier = choice_id,
            text = text(choice.content)
        })
    end

    if correct_count ~= 1 then
        error("A .qti-item must have exactly one .qti-choice with correct=\"true\"")
    end

    local identifier = attr(item, "identifier", "ITEM_1")
    if not identifier:match("^[A-Za-z_][A-Za-z0-9_.%-]*$") then
        error("Invalid QTI item identifier: " .. identifier)
    end
    doc.meta.qti = {
        identifier = identifier,
        title = attr(item, "title", identifier),
        correct = correct_id,
        prompt = text(prompt),
        choices = template_choices
    }
    doc.blocks = {}
    return doc
end
