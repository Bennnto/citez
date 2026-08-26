from lexicals import tokens, lexer
import ply.yacc as yacc
from astnode import (
    If_Node, Type_Node, Assign_Node, Int_Node, Float_Node, String_Node, Bool_Node,
    Binaryops_Node, Unaryops_Node, Program_Node, While_Node, Ident_Node, Char_Node,
    For_Node, Procedure_Node, Param_Node, Break_Node, Continue_Node, Return_Node,
    Onscreen_Node, Scan_Node, Array_Literal_Node, Index_Node, Array_Decl_Node, Call_Node,
    Argument_Node, Pass_Node, Lambda_Node, Field_Node, Struct_Decl_Node, Struct_Access_Node,

)
from dataclasses import asdict
import json

precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'XOR'),
    ('left', 'NE', 'EQ'),
    ('left', 'GT', 'LT', 'GE', 'LE'),
    ('left', 'ADD', 'SUB'),
    ('left', 'MUL', 'DIV', 'MOD'),
    ('right', 'POW'),
    ('right', 'NOT', 'UMINUS'),
)

# Program, Statement and Expression

def p_program(p):
    '''program : statements'''
    p[0] = Program_Node(statements=p[1])
    
def p_statement(p):
    '''statement : expression optional_semicolon
                 | assign_stmt optional_semicolon
                 | if_stmt
                 | while_stmt
                 | for_stmt
                 | procedure_stmt
                 | break_stmt
                 | continue_stmt
                 | return_stmt
                 | scan_stmt
                 | onscreen_stmt
                 | call_stmt
                 | pass_stmt
                 | lambda_stmt'''

    p[0] = p[1]
    
def p_statements(p):
    '''statements : statement
                  | statements statement'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_expression_atom(p):
    '''expression : literal
                  | IDENT
                  | LPAREN expression RPAREN'''
    if p.slice[1].type == 'IDENT':
        p[0] = Ident_Node(ident=p[1])
    elif p.slice[1].type == 'LPAREN':
        p[0] = p[2]
    else:
        p[0] = p[1]

def p_expression_block(p):
    '''expression : LBRACE expression RBRACE'''
    p[0] = p[2]

# Type Kind

def p_type(p):
    '''type : I8
            | I16
            | I32
            | I64
            | U8
            | U16
            | U32
            | U64
            | F32
            | F64
            | USIZE
            | ISIZE
            | STR_TYPE
            | BOOL_TYPE
            | INT_TYPE
            | CHAR_TYPE
            | VOID'''
    p[0] = Type_Node(name=p[1])

# Assign and Set Statement

def p_assign_stmt(p):
    '''assign_stmt : SET IDENT ASSIGN expression
                   | SET expression ASSIGN expression
                   | VAR type IDENT ASSIGN expression
                   | VAR type IDENT
                   | VAR LBRACKET type COMMA INT RBRACKET IDENT ASSIGN expression'''
    if len(p) == 5:
        p[0] = Assign_Node(ident=p[2], type=None, value=p[4])
    elif len(p) == 6:
        p[0] = Assign_Node(ident=p[3], type=p[2], value=p[5])
    elif len(p) == 10:
        p[0] = Array_Decl_Node(ident=p[7], type=p[3], size=p[5], value=p[9])
    else:
        p[0] = Assign_Node(ident=p[3], type=p[2], value=None)
    
        
# Literal of variable 

def p_literal(p):
    '''literal : STR
               | INT
               | FLOAT
               | TRUE
               | FALSE
               | CHAR
               | IDENT'''
    tok_type = p.slice[1].type
    if tok_type == 'INT':
        p[0] = Int_Node(value=p[1])
    elif tok_type == 'FLOAT':
        p[0] = Float_Node(value=p[1])
    elif tok_type in ('TRUE', 'FALSE'):
        p[0] = Bool_Node(value=(p[1] == 'true' or p[1] is True))
    elif tok_type == 'CHAR':
        p[0] = Char_Node(value=str(p[1]))
    else:
        p[0] = String_Node(value=str(p[1]))
                      
# Operation     

def p_expression_binary(p):
    '''expression : expression ADD expression
                  | expression SUB expression
                  | expression MUL expression
                  | expression DIV expression
                  | expression MOD expression
                  | expression POW expression
                  | expression AND expression
                  | expression OR  expression
                  | expression XOR expression
                  | expression NE expression
                  | expression EQ expression
                  | expression GT expression
                  | expression LT expression
                  | expression GE expression
                  | expression LE expression'''
    p[0] = Binaryops_Node(left=p[1], right=p[3], ops=p[2])
    
# Unary Operation

def p_expression_unary(p):
    '''expression : NOT expression
                  | SUB expression %prec UMINUS'''
    p[0] = Unaryops_Node(operand=p[2], ops=p[1])
    
# If_Else 

def p_if_stmt(p):
    '''if_stmt : IF expression LBRACE statements RBRACE
               | IF expression LBRACE statements RBRACE ELSE LBRACE statements RBRACE'''
    if len(p) == 6:
        p[0] = If_Node(cond=p[2], if_block=p[4], else_block=None)
    else:
        p[0] = If_Node(cond=p[2], if_block=p[4], else_block=p[8])
        
# While 

def p_while_stmt(p):
    '''while_stmt : WHILE expression LBRACE statements RBRACE'''
    p[0] = While_Node(cond=p[2], body=p[4])


# For

def p_for_stmt(p):
    '''for_stmt : FOR assign_stmt SEMICOLON expression SEMICOLON assign_stmt LBRACE statements RBRACE
                | FOR assign_stmt IN expression LBRACE statements RBRACE
                | FOR expression LBRACE statements RBRACE'''
    if len(p) == 10:
        p[0] = For_Node(init=p[2], cond=p[4], increment=p[6], body=p[8], is_classic=True)
    elif len(p) == 8:
        p[0] = For_Node(init=p[2], range=p[4], body=p[6], is_classic=False)
    else:
        p[0] = For_Node(cond=p[2], body=p[4], is_classic=False)

# Parameter

def p_param(p):
    '''param : IDENT COLON type'''
    p[0] = Param_Node(name=p[1], type_name=p[3])

def p_param_list(p):
    '''params_list : param
                   | params_list COMMA param
                   | empty'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    elif len(p) == 2 and p[1]:
        p[0] = [p[1]]
    else:
        p[0] = []

# Block
 
def p_block(p):
    '''block : LBRACE statements RBRACE
             | empty'''
    if len(p) == 4 :
        p[0] = p[2]
    else :
        p[0] = []

# Procedure

def p_procedure_stmt(p):
    '''procedure_stmt : PROCEDURE IDENT LPAREN params_list RPAREN COLON type block
                      | PROCEDURE IDENT LPAREN params_list RPAREN block'''
    if len(p) == 9 :
        p[0] = Procedure_Node(ident=p[2], param=p[4], return_type=p[7], body=p[8])
    else :
        p[0] = Procedure_Node(ident=p[2], param=p[4], return_type=None, body=p[6])

# Break and Continue and Return

def p_break_stmt(p):
    '''break_stmt : BREAK optional_semicolon'''
    p[0] = Break_Node()


def p_continue_stmt(p):
    '''continue_stmt : CONTINUE optional_semicolon'''
    p[0] = Continue_Node()

def p_return_stmt(p):
    '''return_stmt : RETURN expression optional_semicolon
                   | RETURN optional_semicolon'''
    if len(p) == 4 :
        p[0] = Return_Node(value=p[2])
    else :
        p[0] = Return_Node(value=None)
    

# Onscreen and Scan

def p_onscreen_stmt(p):
    '''onscreen_stmt : ONSCREEN LPAREN expression RPAREN optional_semicolon'''
    p[0] = Onscreen_Node(expr=p[3])

def p_scan_stmt(p):
    '''scan_stmt : SCAN LPAREN expression RPAREN optional_semicolon'''
    p[0] = Scan_Node(expr=p[3])


# Array and elements
def p_element(p):
    '''element : expression'''
    p[0] = p[1]

def p_element_list(p):
    '''element_list : element 
                    | element_list COMMA element
                    | empty'''

    if len(p) == 2 and p[1] is not []:
        p[0] = [p[1]]
    elif len(p) == 4 :
        p[0] = p[1] + [p[3]]
    else :
        p[0] = []

def p_array_ltieral(p):
    '''expression : LBRACKET element_list RBRACKET optional_semicolon'''
    p[0] = Array_Literal_Node(elements=p[2])

def p_array_index(p):
    '''expression : IDENT LBRACKET expression RBRACKET'''
    p[0] = Index_Node(target=p[1], index=p[3])

# Call and Argument 
 
def p_argument(p):
    '''argument : IDENT 
                | IDENT ASSIGN expression'''
    if len(p) == 2 :
        p[0] = Argument_Node(name=p[1],value=None)
    else :
        p[0] = Argument_Node(name=p[1],value=p[3])

def p_argument_list(p):
    '''argument_list : argument
                     | argument_list COMMA argument
                     | empty'''

    if len(p) == 2 and p[1] is not []:
        p[0] = [p[1]]
    elif len(p) == 4 :
        p[0] = p[1] + [p[3]]
    else :
        p[0] = []

def p_call_stmt(p):
    '''call_stmt : IDENT LPAREN argument_list RPAREN optional_semicolon'''
    p[0] = Call_Node(func=p[1], arguments=p[3])

# Pass
def p_pass_stmt(p):
    '''pass_stmt : PASS optional_semicolon'''
    p[0] = Pass_Node()

# Lambda 
def p_lambda_stmt(p):
    '''lambda_stmt : type LPAREN argument_list RPAREN ARROW statement'''
    p[0] = Lambda_Node(param=p[3], return_type=p[1], body=p[6])

# Struct and Field

def p_field(p):
    '''field : IDENT COLON type'''
    p[0] = Field_Node(name=p[1], type_name=p[3])

def p_field_list(p):
    '''field_list : field
                  | field_list COMMA field
                  | empty'''
    if len(p) == 2 and p[1] is not [] :
        p[0] = [p[1]]
    elif len(p) == 4 :
        p[0] = p[1] + [p[3]]
    else: 
        p[0] = []

def p_struct_decl_stmt(p):
    '''struct_decl_stmt : STRUCT IDENT LBRACE field_list RBRACE'''
    p[0] = Struct_Decl_Node(name=p[2], fields=p[4])

def p_expression_struct_access(p):
    '''expression : expression DOT IDENT'''
    p[0] = Struct_Access_Node(target=p[1], field=p[3])




# Helper
def p_optional_semicolon(p):
    '''optional_semicolon : SEMICOLON
                          | empty'''
    pass

def p_empty(p):
    '''empty : '''
    p[0] = []

def p_error(p):
    if p:
        print(f"Syntax error at token {p.type}, value {p.value}, line {p.lineno}")
    else:
        print("Syntax error at EOF")

parser = yacc.yacc()

if __name__ == "__main__":
    lexer = lexer 
    data = """
    var [i32, 5] numarray = [1, 2, 3, 4, 5]
    """
    result = parser.parse(data, lexer=lexer)
    print(json.dumps(asdict(result), indent=2))