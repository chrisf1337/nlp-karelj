def generate_code(actions, template_filename):
    with open(template_filename, 'r') as template:
        contents = template.read()
    code = ''
    default_indent = 8
    for action in actions:
        lines = action.emit()
        for line in lines:
            code += ' ' * default_indent + ' ' * line.indent + line.line + '\n'
    code = code.lstrip()

    template_vars = {
        'code': code
    }
    contents = contents.replace('{{ code }}\n', template_vars['code'])
    print(contents)
