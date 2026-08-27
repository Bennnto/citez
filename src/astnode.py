from dataclasses import dataclass, field
from typing import Optional, List

class Node():
    pass

class Expr_Node(Node):
    pass

class Stmt_Node(Node):
    pass

@dataclass
class Break_Node(Stmt_Node):
    pass

@dataclass
class Continue_Node(Stmt_Node):
    pass

@dataclass
class Program_Node(Node):
    statements : List[Stmt_Node]

@dataclass
class Type_Node(Node):
    name : str
    
@dataclass
class Assign_Node(Node):
    ident : str
    type : Optional[Type_Node] = None
    value : Optional[Expr_Node] = None
    
@dataclass
class String_Node(Node):
    value : str

@dataclass
class Bool_Node(Node):
    value : bool
    
@dataclass
class Int_Node(Node):
    value : int
    
@dataclass 
class Float_Node(Node):
    value : float
    
@dataclass
class Ident_Node(Node):
    ident : str
    
@dataclass
class Binaryops_Node(Node):
    left : Expr_Node
    right : Expr_Node
    ops : str
    
@dataclass
class Char_Node(Node):
    value : str
    
@dataclass
class If_Node(Node):
    cond : Expr_Node
    if_block : List[Stmt_Node]
    else_block : Optional[List[Stmt_Node]] = None
    
@dataclass
class Unaryops_Node(Node):
    operand: Expr_Node
    ops : str
    
@dataclass
class While_Node(Node):
    cond : Expr_Node
    body : List[Stmt_Node]

@dataclass
class Param_Node(Node):
    name : str
    type_name : Optional[Type_Node]
    
@dataclass
class Procedure_Node(Node):
    ident : str
    return_type : Optional[Type_Node]
    param : Optional[List[Param_Node]]
    body : List[Stmt_Node]

@dataclass
class For_Node(Node):
    init : Optional[Expr_Node] = None
    cond : Optional[Expr_Node] = None
    range : Optional[Expr_Node] = None
    increment : Optional[Expr_Node] = None
    body : List[Stmt_Node] = field(default_factory=list)
    is_classic : bool = False

@dataclass
class Return_Node(Node):
    value : Optional[Expr_Node] = None

@dataclass 
class Onscreen_Node(Node):
    expr: Expr_Node

@dataclass
class Scan_Node(Node):
    expr: Expr_Node

@dataclass 
class Array_Literal_Node(Expr_Node):
    elements : List[Expr_Node]

@dataclass 
class Index_Node(Expr_Node):
    target : Expr_Node
    index : Expr_Node

@dataclass
class Array_Decl_Node(Stmt_Node):
    ident : str
    type : Type_Node
    size : int
    value : Optional[Array_Literal_Node] = None

@dataclass
class Argument_Node(Expr_Node):
    name : str
    value : Optional[Expr_Node] = None

@dataclass
class Call_Node(Stmt_Node):
    func : str
    arguments : List[Argument_Node]

@dataclass
class Pass_Node(Stmt_Node):
    pass

@dataclass
class Lambda_Node(Stmt_Node):
    param : List[Param_Node]
    return_type : Optional[Type_Node] = None
    body : Stmt_Node = None

@dataclass
class Field_Node(Node):
    name : str
    type_name : Type_Node

@dataclass
class Struct_Decl_Node(Stmt_Node):
    name : str
    fields : List[Field_Node]

@dataclass
class Struct_Access_Node(Expr_Node):
    target : Expr_Node
    field : str
    is_arrow : bool = False

@dataclass 
class Pointer_Type_Node(Node):
    base_type : Type_Node

@dataclass
class Address_Node(Expr_Node):
    target : Expr_Node

@dataclass 
class Deref_Node(Expr_Node):
    target : Expr_Node

@dataclass
class Trap_Node(Stmt_Node):
    trap_block : List[Stmt_Node]
    catch_var : Optional[str] = None
    catch_block : Optional[List[Stmt_Node]] = None
    always_block : Optional[List[Stmt_Node]] = None

@dataclass
class Raise_Node(Stmt_Node):
    expr : Optional[Expr_Node] = None


@dataclass
class Borrow_Type_Node(Stmt_Node):
    base_type : Type_Node
    is_rw : bool = False

@dataclass
class Drop_Node(Stmt_Node):
    target : str
    
@dataclass 
class Borrow_Node(Stmt_Node):
    target : Expr_Node
    is_rw : bool = False

@dataclass
class Alloc_Node(Expr_Node):
    type : Type_Node
    count : Expr_Node

@dataclass
class Free_Node(Stmt_Node):
    target : Expr_Node

@dataclass
class Field_Init_Node(Node):
    field : str
    value : Expr_Node

@dataclass
class Struct_Literal_Node(Expr_Node):
    struct_name : str
    fields : List[Field_Init_Node]