# [SublimeLinter @python:2]

from __future__ import print_function

def generate_code(actions, test_number, template_filename, output_filename):
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
    contents = contents.replace('{{ test_number }}', str(test_number))
    with open(output_filename, 'w') as output:
        output.write(contents)
