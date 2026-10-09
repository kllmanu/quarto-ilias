local function field(map, name, default)
    local value = map[name]
    if value == nil then
        return default
    end
    return pandoc.utils.stringify(value)
end

local function valid_identifier(identifier)
    return identifier:match("^[A-Za-z_][A-Za-z0-9_.%-]*$") ~= nil
end

function Pandoc(doc)
    local qti = doc.meta.qti
    if qti == nil or type(qti) ~= "table" then
        error("QTI output requires a qti object in YAML front matter")
    end

    local identifier = field(qti, "identifier", "ITEM_1")
    if not valid_identifier(identifier) then
        error("Invalid QTI item identifier: " .. identifier)
    end

    local choices = qti.choices
    if choices == nil or type(choices) ~= "table" or #choices < 2 then
        error("qti.choices must contain at least two choices")
    end

    local correct_count = 0
    local correct_id = nil
    local template_choices = {}
    local used_ids = {}

    for index, choice in ipairs(choices) do
        if type(choice) ~= "table" then
            error("Each qti.choices entry must be an object")
        end

        local choice_id = field(choice, "identifier", "CHOICE_" .. index)
        if not valid_identifier(choice_id) then
            error("Invalid QTI choice identifier: " .. choice_id)
        end
        if used_ids[choice_id] then
            error("Duplicate QTI choice identifier: " .. choice_id)
        end
        used_ids[choice_id] = true

        if field(choice, "correct", "false") == "true" then
            correct_count = correct_count + 1
            correct_id = choice_id
        end

        local choice_text = field(choice, "text", "")
        if choice_text == "" then
            error("Each qti.choices entry must have non-empty text")
        end
        table.insert(template_choices, {
            identifier = choice_id,
            text = choice_text
        })
    end

    if correct_count ~= 1 then
        error("Exactly one qti.choices entry must have correct: true")
    end

    local prompt = field(qti, "prompt", "")
    if prompt == "" then
        error("qti.prompt must not be empty")
    end

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
