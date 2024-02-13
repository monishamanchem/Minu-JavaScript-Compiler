import ply.lex as lex
import json
from pyjsparser import parse

tokens = (
    'KEYWORD',
    'IDENTIFIER',
    'STRING_LITERAL',
    'NUMBER',
    'BOOLEAN_LITERAL',
    'NULL',
    'UNDEFINED',
    'SPECIAL_LITERAL',
    'LPAREN',
    'RPAREN',
    'LBRACE',
    'RBRACE',
    'SEMICOLON',
    'COMMA',
    'DOT',
    'ASSIGN',
    'EQUAL',
    'NOT_EQUAL',
    'PLUS',
    'MINUS',
    'MULTIPLY',
    'DIVIDE',
    'MODULO',
    'FUNCTION',
    'RETURN',
    'CONSTANT',
    'DELIMITER',
    'OPERATOR',
)

t_ignore = ' \t'
t_KEYWORD = r'(var|let|const|if|while|for|function|return)(?=\W|$)'
t_IDENTIFIER = r'(console.log)|(\w+(?=\W|$))'
t_STRING_LITERAL = r'(\'[^\']*\'|\"[^\"]*\")'
t_SPECIAL_LITERAL = r'(null|undefined)(?=\W|$)'
t_NUMBER = r'\d+'
t_BOOLEAN_LITERAL = r'(?:true|false)'
t_NULL = r'null'
t_UNDEFINED = r'undefined'

def t_CONSTANT(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_DELIMITER(t):
    r'[{}();,\[\]\.]'
    return t

def t_OPERATOR(t):
    r'[+-=<>*!|/]'
    return t

def t_ignore_COMMENT(t):
    r'//.*|/\*(.|\n)*?\*/'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    t.lexer.lexpos = t.lexpos + len(t.value)

def t_error(t):
    print(f"Illegal character '{t.value[0]}' at line {t.lineno}, position {t.lexpos}")
    t.lexer.skip(1)

lexer = lex.lex()
input_code = """
var x;
let y;
const z = 5;

// Decision Making Statement (if-else)
let age = 18;

if (age >= 18) {
  console.log("You are an adult.");
} else {
  console.log("You are a minor.");
}

// Arithmetic Operations
let a = 10;
let b = 5;

let sum = a + b;
let difference = a - b;
let product = a * b;
let quotient = a / b;

console.log('Sum: ',sum);
console.log('Difference: ',difference);
console.log('Product:',product);
console.log('Quotient:', quotient);

// For loop
for (let i = 0; i < 5; i++) {
  console.log('Count (for loop):', i);
}

// While loop
let count = 0;
while (count < 5) {
  console.log('Count (while loop): ' + count);
  count = count + 1;
}

"""
# Give the lexer the input code
lexer.input(input_code)

# Tokenize and print the lexer output
print("------------------------------------------------ Lexical Analysis ------------------------------------------------")
while True:
    tok = lexer.token()
    if not tok:
        break
    print(tok)


ast = parse(input_code)


ast_json_syntax = json.dumps(ast, indent=2)
print("\n\n------------------------------------------------ Syntax Analysis ------------------------------------------------")
print(ast_json_syntax)
class SymbolTable:
    def __init__(self):
        self.symbols = {}
        self.scopes = [{}]

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def add_symbol(self, name, value, type, lineno):
        self.scopes[-1][name] = {'value': value, 'type': type, 'lineno': lineno}

    def get_symbol(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def update_symbol(self, name, value):
        for scope in reversed(self.scopes):
            if name in scope:
                scope[name]['value'] = value
                return True
        return False


symbol_table = SymbolTable()
current_scope = 'global'

def handle_variable_declaration(node):
    global current_scope
    declaration_type = node['kind']

    for decl in node['declarations']:
        var_name = decl['id']['name']
        lineno = decl['id'].get('loc', {}).get('start', {}).get('line', -1)

        if 'init' in decl and decl['init']:
            if decl['init']['type'] == 'Literal':
                var_value = decl['init']['value']
            elif decl['init']['type'] == 'Identifier':
                var_value = symbol_table.get_symbol(decl['init']['name'])['value']
            elif decl['init']['type'] == 'BinaryExpression':
                var_value = evaluate_binary_expression(decl['init'])
            else:
                var_value = None
        else:
            var_value = None

        symbol_table.add_symbol(var_name, var_value, declaration_type, lineno)

def evaluate_binary_expression(node):
    operator = node['operator']
    left_operand = node['left']
    right_operand = node['right']

    if operator == '+':
        return evaluate_expression(left_operand) + evaluate_expression(right_operand)
    elif operator == '-':
        return evaluate_expression(left_operand) - evaluate_expression(right_operand)
    elif operator == '*':
        return evaluate_expression(left_operand) * evaluate_expression(right_operand)
    elif operator == '/':
        return evaluate_expression(left_operand) / evaluate_expression(right_operand)

def evaluate_expression(node):
    if node['type'] == 'Literal':
        return node['value']
    elif node['type'] == 'Identifier':
        return symbol_table.get_symbol(node['name'])['value']
    elif node['type'] == 'BinaryExpression':
        return evaluate_binary_expression(node)


def semantic_analysis(ast):
    global current_scope

    for node in ast['body']:
        if node['type'] == 'VariableDeclaration':
            handle_variable_declaration(node)
        elif node['type'] == 'FunctionDeclaration':
            symbol_table.add_symbol(node['id']['name'], None, 'function', node.get('loc', {}).get('start', {}).get('line', -1))
            symbol_table.push_scope()
            for param in node['params']:
                symbol_table.add_symbol(param['name'], None, 'param', param.get('loc', {}).get('start', {}).get('line', -1))
            semantic_analysis(node['body'])
            symbol_table.pop_scope()

semantic_analysis(ast)


print("\n\n------------------------------------------------ Symbol Table ------------------------------------------------")
for scope_index, scope in enumerate(symbol_table.scopes):
    print(f"Scope {scope_index + 1}:")
    for symbol_name, symbol_info in scope.items():
        if 'value' in symbol_info:
            print(f"  {symbol_name}: {symbol_info['value']} (Type: {symbol_info['type']}, Line No: {symbol_info['lineno']})")
        else:
            print(f"  {symbol_name}: (Type: {symbol_info['type']}, Line No: {symbol_info['lineno']})")


ast_json_semantic = json.dumps(ast, indent=2)
print("\n\n------------------------------------------------ Semantic Analysis ------------------------------------------------")
print(ast_json_semantic)

def generate_intermediate_code(input_code):
    lines = input_code.split('\n')
    intermediate_code = ""
    label_count = 1

    for line in lines:
        # Remove comments
        if '//' in line:
            line = line.split('//')[0].strip()

        # Skip empty lines
        if line.strip() == '':
            continue

        # Handle variable declaration
        if 'var' in line or 'let' in line or 'const' in line:
            intermediate_code += line + '\n'

        # Handle assignment statements
        elif '=' in line and 'if' not in line and 'for' not in line and 'while' not in line:
            parts = line.split('=')
            if len(parts) >= 2:
                var_name = parts[0].strip()
                var_value = parts[1].strip()
                intermediate_code += f'{var_name};\n{var_name} = {var_value};\n'
            else:
                print(f"Error in line: {line}")

        # Handle conditional statements
        elif 'if' in line:
            condition = line.split('(')[1].split(')')[0].strip()
            intermediate_code += f'IF {condition} GOTO label{label_count}\n'
            label_count += 1

        elif 'else' in line:
            intermediate_code += f'ELSE GOTO label{label_count}\n'
            intermediate_code += f'label{label_count - 1}:\n'
            label_count += 1

        elif '}' in line and 'end_if' not in line:
            intermediate_code += f'GOTO end_if\n'
            intermediate_code += f'label{label_count - 1}:\n'
            label_count += 1


        elif 'for' in line:

            parts_let = line.split('let')

            parts_eq = line.split('=')

            parts_lt = line.split('<')

            if len(parts_let) >= 2 and len(parts_eq) >= 2 and len(parts_lt) >= 2:

                loop_var = parts_let[1].split('=')[0].strip()

                loop_limit = parts_lt[1].split(';')[0].strip()

                intermediate_code += f'{loop_var};\nlabel_for_start:\nIF {loop_var} < {loop_limit} GOTO label_for_body\nELSE GOTO label_for_end\nlabel_for_body:\nPRINT "Count (for loop): " + {loop_var};\n{loop_var} = {loop_var} + 1;\nGOTO label_for_start\nlabel_for_end:\n'

            else:

                print(f"Error in line: {line}")

        elif 'while' in line:
            intermediate_code += f'let count;\ncount = 0;\nlabel_while_start:\nIF count < 5 GOTO label_while_body\nELSE GOTO label_while_end\nlabel_while_body:\nPRINT "Count (while loop): " + count;\ncount = count + 1;\nGOTO label_while_start\nlabel_while_end:\n'

    return intermediate_code.strip()


resulting_intermediate_code = generate_intermediate_code(input_code)
print("\n\n------------------------------------------------ Intermediate Code ------------------------------------------------")
print(resulting_intermediate_code)

def generate_assembly_code(resulting_intermediate_code):
    assembly_code_data = """.data
x:  .word 0
y:  .word 0
z:  .word 5

adult_msg: .asciiz "You are an adult.\n"
minor_msg: .asciiz "You are a minor.\n"
"""

    assembly_code_text = """.text
.globl _start

_start:
"""

    label_count = 1

    lines = resulting_intermediate_code.split('\n')
    for line in lines:
        if 'var' in line or 'let' in line or 'const' in line:
            var_name = line.split()[1][:-1]
            assembly_code_data += f"{var_name}: .word 0\n"

        elif '=' in line and 'IF' not in line and 'PRINT' not in line:
            var_name, value = line.split('=')
            var_name = var_name.strip()
            value = value.strip()
            assembly_code_text += f"    li $t{label_count}, {value}\n"
            assembly_code_text += f"    sw $t{label_count}, {var_name}\n"
            label_count += 1

        elif 'IF' in line:
            condition = line.split('IF ')[1].split(' GOTO')[0].strip()
            label = line.split('GOTO ')[1].strip()
            assembly_code_text += f"    bge $t{label_count - 1}, {condition}, {label}\n"

        elif 'PRINT' in line:
            message = line.split('"')[1]
            assembly_code_text += f"    li $v0, 4\n"
            assembly_code_text += f"    la $a0, {message}_msg\n"
            assembly_code_text += f"    syscall\n"

        elif 'GOTO' in line:
            label = line.split('GOTO ')[1].strip()
            assembly_code_text += f"    j {label}\n"
            assembly_code_text += f"{label}:\n"

    assembly_code_text += """
end_program:
    li $v0, 10
    syscall
"""

    return assembly_code_data + assembly_code_text

print("\n\n------------------------------------------------ Assembly code ------------------------------------------------")
resulting_assembly_code = generate_assembly_code(resulting_intermediate_code)
print(resulting_assembly_code)
