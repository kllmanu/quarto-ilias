local function field(map, name, default)
    local value = map[name]
    if value == nil then
        return default
    end
    return pandoc.utils.stringify(value)
end

function Pandoc(doc)
    local qti = doc.meta.qti
    local identifier = field(qti, "identifier", "ITEM_1")
    local choices = qti.choices
    local correct_id = nil
    local template_choices = {}

    for index, choice in ipairs(choices) do
        local choice_id = field(choice, "identifier", "CHOICE_" .. index)
        if field(choice, "correct", "false") == "true" then
            correct_id = choice_id
        end

        table.insert(template_choices, {
            identifier = choice_id,
            text = field(choice, "text", "")
        })
    end

    local prompt = field(qti, "prompt", "")
    doc.meta.qti = {
        identifier = identifier,
        title = field(qti, "title", identifier),
        correct = correct_id,
        prompt = prompt,
        choices = template_choices
    }
    doc.blocks = {}
    return doc
end
