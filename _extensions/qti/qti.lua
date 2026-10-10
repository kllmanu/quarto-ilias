local function field(map, name, default)
    local value = map[name]
    if value == nil then
        return default
    end
    return pandoc.utils.stringify(value)
end

local function xml_escape(value)
    return tostring(value)
        :gsub("&", "&amp;")
        :gsub("<", "&lt;")
        :gsub(">", "&gt;")
        :gsub('"', "&quot;")
        :gsub("'", "&apos;")
end

function Pandoc(doc)
    local qti = doc.meta.qti
    local interaction_type = field(qti, "type", "choice")
    local identifier = field(qti, "identifier", "ITEM_1")
    local choices = qti.choices
    local correct_id = nil
    local template_choices = {}

    if interaction_type == "choice" then
        for index, choice in ipairs(choices) do
            local choice_id = field(choice, "identifier", "CHOICE_" .. index)
            if field(choice, "correct", "false") == "true" then
                correct_id = choice_id
            end

            table.insert(template_choices, string.format(
                '<simpleChoice identifier="%s">%s</simpleChoice>',
                xml_escape(choice_id),
                xml_escape(field(choice, "text", ""))
            ))
        end
    else
        correct_id = field(qti, "correct", "")
    end

    local template_name = interaction_type == "choice" and "qti-choice.xml" or "qti-text-entry.xml"
    local template_path = pandoc.path.join({
        pandoc.path.directory(PANDOC_SCRIPT_FILE),
        template_name
    })
    local file = io.open(template_path, "r")
    if not file then
        error("Could not open QTI template: " .. template_path)
    end
    local template_source = file:read("*a")
    file:close()

    local context = {
        qti = {
            identifier = xml_escape(identifier),
            title = xml_escape(field(qti, "title", identifier)),
            correct = xml_escape(correct_id or ""),
            prompt = xml_escape(field(qti, "prompt", "")),
            choices_xml = table.concat(template_choices)
        }
    }
    local template = pandoc.template.compile(template_source, template_path)
    local xml = pandoc.layout.render(pandoc.template.apply(template, context))
    return pandoc.Pandoc({ pandoc.RawBlock("docbook", xml) }, doc.meta)
end
