from dataclasses import dataclass 
from typing import Optional

class HIRNode: pass
class HIRStmt(HIRNode): pass
class HIRExpr(HIRNode): pass

@dataclass
class HIRProgram(HIRNode):
    statements : list[HIRStmt]
    
@dataclass 
class HIRAssign(HIRStmt):
    ident: str
    type: Optional[str]
    value: Optional[HIRExpr]
    
@dataclass 
class HIRInt(HIRExpr):
    value : int 
    type_name : str

@dataclass
class HIRFloat(HIRExpr):
    value : float
    type_name : str
    
@dataclass
class HIRString(HIRExpr):
    value : str
    type_name : str
    
@dataclass 
class HIRBool(HIRExpr):
    value : bool
    type_name : str
    
@dataclass
class HIRBinary(HIRExpr):
    left : HIRExpr
    right : HIRExpr
    ops : str
    
@dataclass
class HIRName(HIRExpr):
    name : str
    type_name : str
    
@dataclass
class HIRChar(HIRExpr):
    value : str
    type_name : str

@dataclass
class HIRIf(HIRStmt):
    cond : HIRExpr
    if_block : list[HIRStmt]
    else_block : Optional[list[HIRStmt]] = None
    
@dataclass
class HIRWhile(HIRStmt):
    cond : HIRExpr
    body : list[HIRStmt]

@dataclass
class HIRFor(HIRStmt):
    body : list[HIRStmt]
    is_classic : bool 
    init : Optional[HIRStmt] = None
    cond : Optional[HIRExpr] = None
    increment : Optional[HIRExpr] = None
    range : Optional[HIRExpr] = None

@dataclass
class HIRProcedure(HIRStmt):
    ident : str
    return_type : str
    body : list[HIRStmt]
    param : Optional[list[HIRExpr]] = None
    
@dataclass 
class HIRBreak(HIRStmt):
    pass

@dataclass
class HIRContinue(HIRStmt):
    pass

@dataclass
class HIRReturn(HIRStmt):
    value : Optional[HIRExpr] = None


@dataclass
class HIROnscreen(HIRStmt):
    expr : HIRExpr

@dataclass
class HIRScan(HIRStmt):
    expr : HIRExpr

@dataclass
class HIRArrayliteral(HIRStmt):
    elements : list[HIRExpr]

@dataclass
class HIRIndex(HIRExpr):
    target : HIRExpr
    index : HIRExpr

@dataclass
class HIRArraydecl(HIRStmt):
    ident : str
    type : str
    size : int 
    value : Optional[HIRArrayliteral] = None

@dataclass
class HIRArgument(HIRExpr):
    name : str
    value : Optional[HIRExpr] = None
    
@dataclass
class HIRCall(HIRStmt):
    func : str
    arguments : list[HIRArgument]

@dataclass
class HIRPass(HIRStmt):
    pass

@dataclass
class HIRLambda(HIRStmt):
    args : list[HIRExpr]
    return_type : str
    body : list[HIRStmt]

@dataclass
class HIRField(HIRNode):
    name : str
    type_name : str

@dataclass
class HIRStructdecl(HIRStmt):
    name : str
    fields : list[HIRField]

@dataclass
class HIRStructaccess(HIRExpr):
    target : HIRExpr
    field : str

@dataclass
class HIRAddress(HIRExpr):
    target: HIRExpr

@dataclass
class HIRPointertype(HIRExpr):
    base_type : str

@dataclass 
class HIRDeref(HIRExpr):
    target : HIRExpr 




    