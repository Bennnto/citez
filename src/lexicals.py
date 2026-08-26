import ply.lex as lex

tokens = (
    # Type and Literal
    'STR_TYPE',
    'STR',
    'INT_TYPE',
    'INT',
    'BOOL',
    'BOOL_TYPE',
    'FLOAT',
    'FLOAT_TYPE',
    'I8', 'I16', 'I32', 'I64', 'ISIZE',
    'U8', 'U16', 'U32', 'U64', 'USIZE',
    'F32', 'F64', 
    'CHAR',
    'CHAR_TYPE',
    'IDENT',
    'VOID',
    
    # Delimiters
    'COLON', 'SEMICOLON', 'DOUBLE_COLON', 'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'COMMA',
    'LBRACKET', 'RBRACKET', 'ARROW', 'DOT',
    
    # Operators
    'ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'POW', 'AND', 'OR', 'XOR', 'NOT',
    'NE', 'EQ', 'LE', 'GE', 'LT', 'GT', 'UMINUS',
    
    # Keywords
    'ASSIGN', 'SET', 'VAR', 'TRUE', 'FALSE', 'NEWLINE', 'IF', 'ELSE', 'WHILE', 'CONTINUE', 
    'BREAK', 'PROCEDURE', 'FOR', 'IN', 'RETURN', 'ONSCREEN', 'SCAN', 'ARRAY', 'PASS', 
    'STRUCT'
)

reserved = {
    'set': 'SET',
    'var': 'VAR',
    'if': 'IF',
    'else': 'ELSE',
    'while': 'WHILE',
    'continue': 'CONTINUE',
    'break': 'BREAK',
    'str': 'STR_TYPE',
    'int': 'INT_TYPE',
    'bool': 'BOOL_TYPE',
    'float': 'FLOAT_TYPE',
    'char': 'CHAR_TYPE',
    'void': 'VOID',
    'i8': 'I8',
    'i16': 'I16',
    'i32': 'I32',
    'i64': 'I64',
    'u8': 'U8',
    'u16': 'U16',
    'u32': 'U32',
    'u64': 'U64',
    'isize': 'ISIZE',
    'usize': 'USIZE',
    'f32': 'F32',
    'f64': 'F64',
    'true': 'TRUE',
    'false': 'FALSE',
    'proc': 'PROCEDURE',
    'for': 'FOR',
    'in' : 'IN',
    'onscreen' : 'ONSCREEN',
    'scan' : 'SCAN',
    'array' : 'ARRAY',
    'return' : 'RETURN',
    'pass': 'PASS',
    'struct' : 'STRUCT'
}


t_ignore = ' \t'

t_DOUBLE_COLON = r'::'
t_COLON = r':'
t_SEMICOLON = r';'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_COMMA = r','

t_POW = r'\*\*'
t_ADD = r'\+'
t_SUB = r'-'
t_MUL = r'\*'
t_DIV = r'\/'
t_MOD = r'%'
t_AND = r'\&\&'
t_OR = r'\|\|'
t_XOR = r'\^'
t_NOT = r'!'
t_NE = r'!='
t_EQ = r'=='
t_LE = r'<='
t_GE = r'>='
t_LT = r'<'
t_ASSIGN = r'='
t_GT = r'>'
t_DOT = r'\.'
t_ARROW = r'->'

def t_IDENT(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'IDENT')
    return t

def t_CHAR(t):
    r"'\\?.'"
    return t

def t_STR(t):
    r'"[^"]*"'
    t.value = t.value[1:-1]
    return t

def t_FLOAT(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_INT(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f'Invalid Token at {t.lineno} position {t.lexpos}')
    t.lexer.skip(1)

lexer = lex.lex()

if __name__ == "__main__":
    data = "var char x = 'c';"
    lexer.input(data)
    while True:
        tok = lex.token()
        if not tok:
            break
        print(tok)