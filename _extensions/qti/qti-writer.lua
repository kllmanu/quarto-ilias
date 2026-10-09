local function scalar(value)
    return pandoc.utils.stringify(value)
end

function Writer(doc, opts)
    local template = opts and opts.template
    if not template then
        local template_path = pandoc.path.join({
            pandoc.path.directory(PANDOC_SCRIPT_FILE),
            "qti.xml"
        })
        local file = io.open(template_path, "r")
        if not file then
            error("Could not open QTI template: " .. template_path)
        end
        local contents = file:read("*a")
        file:close()
        template = pandoc.template.compile(contents, template_path)
    end

    local item = doc.meta.qti
    local choices = {}
    for _, choice in ipairs(item.choices) do
        table.insert(choices, {
            identifier = scalar(choice.identifier),
            text = scalar(choice.text)
        })
    end

    local context = {
        qti = {
            identifier = scalar(item.identifier),
            title = scalar(item.title),
            correct = scalar(item.correct),
            prompt = scalar(item.prompt),
            choices = choices
        }
    }
    return pandoc.layout.render(pandoc.template.apply(template, context))
end
