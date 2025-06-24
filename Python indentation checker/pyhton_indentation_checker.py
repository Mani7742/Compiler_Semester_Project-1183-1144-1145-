# python indentation checker
# Includes all six phases of compilation

import ply.lex as lex
import ply.yacc as yacc
import tkinter as tk
from tkinter import scrolledtext, messagebox

# ----------- LEXICAL ANALYSIS -----------

reserved = {
    'if': 'IF',
    'else': 'ELSE',
    'print': 'PRINT',
    'for': 'FOR',
    'in': 'IN',
    'range': 'RANGE'
}

tokens = [
    'COLON', 'NAME', 'NUMBER', 'EQUALS', 'EQEQ',
    'LPAREN', 'RPAREN', 'COMMA',
    'NEWLINE', 'INDENT', 'DEDENT'
] + list(reserved.values())

t_COLON = r':'
t_EQUALS = r'='
t_EQEQ = r'=='
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COMMA = r','

t_ignore = ' '

indent_stack = [0]
token_queue = []

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_NAME(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'NAME')
    return t

def t_NEWLINE(t):
    r'\n[ \t]*'
    t.lexer.lineno += 1
    spaces = len(t.value) - 1
    last_indent = indent_stack[-1]

    new_newline = lex.LexToken()
    new_newline.type = 'NEWLINE'
    new_newline.value = '\n'
    new_newline.lineno = t.lexer.lineno
    new_newline.lexpos = t.lexpos

    if spaces > last_indent:
        indent_stack.append(spaces)
        indent = lex.LexToken()
        indent.type = 'INDENT'
        indent.value = ''
        indent.lineno = t.lexer.lineno
        indent.lexpos = t.lexpos
        token_queue.append(indent)
        return new_newline
    elif spaces < last_indent:
        while indent_stack and indent_stack[-1] > spaces:
            indent_stack.pop()
            dedent = lex.LexToken()
            dedent.type = 'DEDENT'
            dedent.value = ''
            dedent.lineno = t.lexer.lineno
            dedent.lexpos = t.lexpos
            token_queue.append(dedent)
        return new_newline
    else:
        return new_newline

def t_error(t):
    raise SyntaxError(f"Illegal character {t.value[0]!r} at line {t.lineno}")

lexer = lex.lex()

def token_generator(input_code):
    lexer.input(input_code)
    while True:
        if token_queue:
            tok = token_queue.pop(0)
        else:
            tok = lexer.token()
            if not tok:
                while len(indent_stack) > 1:
                    indent_stack.pop()
                    dedent = lex.LexToken()
                    dedent.type = 'DEDENT'
                    dedent.value = ''
                    dedent.lineno = lexer.lineno
                    dedent.lexpos = 0
                    yield dedent
                break
        yield tok

# ----------- SYNTAX, SEMANTIC, IR GENERATION -----------

start = 'program'
symbol_table = {}
intermediate_code = []
temp_count = 0

def new_temp():
    global temp_count
    temp = f"t{temp_count}"
    temp_count += 1
    return temp

def p_program(p):
    'program : statement_list'
    p[0] = p[1]

def p_statement_list(p):
    '''statement_list : statement
                      | statement_list statement'''
    pass

def p_statement(p):
    '''statement : simple_stmt NEWLINE
                 | compound_stmt
                 | NEWLINE'''
    pass

def p_simple_stmt(p):
    '''simple_stmt : assignment
                   | print_stmt'''
    pass

def p_assignment(p):
    'assignment : NAME EQUALS expr'
    symbol_table[p[1]] = 'int'
    intermediate_code.append(f"{p[1]} = {p[3]}")

def p_print_stmt(p):
    'print_stmt : PRINT LPAREN expr RPAREN'
    intermediate_code.append(f"print({p[3]})")

def p_expr_name(p):
    'expr : NAME'
    if p[1] not in symbol_table:
        raise NameError(f"Undefined variable '{p[1]}'")
    p[0] = p[1]

def p_expr_number(p):
    'expr : NUMBER'
    p[0] = str(p[1])

def p_expr_eqeq(p):
    'expr : expr EQEQ expr'
    temp = new_temp()
    intermediate_code.append(f"{temp} = {p[1]} == {p[3]}")
    p[0] = temp

def p_compound_stmt(p):
    '''compound_stmt : IF expr COLON NEWLINE INDENT statement_list DEDENT
                     | ELSE COLON NEWLINE INDENT statement_list DEDENT
                     | FOR NAME IN RANGE LPAREN NUMBER RPAREN COLON NEWLINE INDENT statement_list DEDENT'''
    if p[1] == 'if':
        intermediate_code.append(f"if {p[2]}:")
    elif p[1] == 'else':
        intermediate_code.append("else:")
    elif p[1] == 'for':
        var = p[2]
        rng = p[6]
        symbol_table[var] = 'int'
        intermediate_code.append(f"for {var} in range({rng}):")

def p_error(p):
    if p:
        raise SyntaxError(f"Syntax error at '{p.value}' line {p.lineno}")
    else:
        raise SyntaxError("Syntax error at EOF")

parser = yacc.yacc()

# ----------- OPTIMIZATION -----------

def optimize(code_list):
    optimized = []
    for line in code_list:
        if '==' in line and all(part.strip().isdigit() for part in line.split('==')):
            lhs, rhs = line.split('=')
            val = eval(rhs.strip())
            optimized.append(f"{lhs.strip()} = {val}")
        else:
            optimized.append(line)
    return optimized

# ----------- CODE GENERATION -----------

def generate_code(code_lines):
    return "\n".join(code_lines)

#----------- Assembly code generation -------
def generate_assembly(code_lines):
    asm_code = []
    for line in code_lines:
        line = line.strip()
        # Assignment: 
        if '=' in line and not line.startswith('if') and not line.startswith('for') and not line.startswith('else'):
            var, val = line.split('=', 1)
            var = var.strip()
            val = val.strip()
            
            asm_code.append(f"MOV {var}, {val}")
        # print statement: 
        elif line.startswith('print(') and line.endswith(')'):
            inside = line[6:-1].strip()
            asm_code.append(f"PRINT {inside}")
        # if statement
        elif line.startswith('if'):
            condition = line[3:-1].strip()  # remove 'if ' and ':'
            asm_code.append(f"; IF {condition}")
        # else statement
        elif line.startswith('else'):
            asm_code.append("; ELSE")
        # for loop
        elif line.startswith('for'):
            asm_code.append(f"; {line}")
        else:
            asm_code.append(f"; {line}  ; (unknown)")
    return "\n".join(asm_code)
# ----------- GUI -----------

def check_indentation():
    global indent_stack, token_queue, intermediate_code, symbol_table, temp_count
    indent_stack = [0]
    token_queue = []
    intermediate_code = []
    symbol_table = {}
    temp_count = 0

    code = text_area.get("1.0", tk.END)
    try:
        token_gen = token_generator(code)
        parser.parse(lexer=lexer, tokenfunc=lambda: next(token_gen, None))
        optimized = optimize(intermediate_code)
        final_code = generate_code(optimized)
        messagebox.showinfo("Result", "Compiled successfully!\n\nGenerated Code:\n" + final_code)
    except (IndentationError, SyntaxError, NameError) as e:
        messagebox.showerror("Compiler Error", str(e))
    except Exception as e:
        messagebox.showerror("Unknown Error", str(e))

root = tk.Tk()
root.title("Mini Python Compiler")

text_area = scrolledtext.ScrolledText(root, width=80, height=20, font=("Courier", 12))
text_area.pack(padx=10, pady=10)

check_button = tk.Button(root, text="Compile", command=check_indentation)
check_button.pack(pady=5)

root.mainloop()
