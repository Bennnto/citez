from astnode import ( 
    Type_Node, Assign_Node,
    String_Node, Bool_Node,
    Int_Node, Float_Node,
    Ident_Node, Program_Node,
    Binaryops_Node, Char_Node,
    Unaryops_Node, If_Node,
    While_Node, For_Node,
    Param_Node, Procedure_Node,
    Return_Node, Onscreen_Node, 
    Scan_Node, Array_Literal_Node,
    Index_Node, Array_Decl_Node,
    Call_Node, Argument_Node,
    Lambda_Node, Struct_Decl_Node,
    Field_Node, Struct_Access_Node
)
from symbol import Scope, TYPE_NAME_MAP as Type_Name_Map, Symbol

INT_TYPES = {
    Type_Name_Map["int"], Type_Name_Map["i8"], Type_Name_Map["i16"],
    Type_Name_Map["i32"], Type_Name_Map["i64"], Type_Name_Map["isize"],
    Type_Name_Map["u8"], Type_Name_Map["u16"], Type_Name_Map["u32"],
    Type_Name_Map["u64"], Type_Name_Map["usize"],
}

FLOAT_TYPES = {
    Type_Name_Map["float"], Type_Name_Map["f32"], Type_Name_Map["f64"],
}

NUMERIC_TYPES = INT_TYPES | FLOAT_TYPES


class SemanticError(Exception):
    pass

class Analyzer:
    def __init__(self):
        self.global_scope = Scope(kind="global")
        self.current_scope = self.global_scope
    
    def push_scope(self, kind="block"):
        self.current_scope = Scope(parent=self.current_scope, kind=kind)
        return self.current_scope
    
    def pop_scope(self):
        if self.current_scope.parent is None:
            raise SemanticError("Error: Cannot pop global scope")
        self.current_scope = self.current_scope.parent
        
    def analyze(self, program: Program_Node):
        for stmt in program.statements:
            self.check(stmt)

    def check(self, node):
        method_name = f"check_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_check)
        return method(node)
    
    def infer(self, node):
        method_name = f"infer_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_infer)
        return method(node)
    
    def generic_check(self, node):
        try:
            return self.infer(node)
        except NotImplementedError:
            raise NotImplementedError(f"Error :No check method for {type(node).__name__}")
    
    def generic_infer(self, node):
        raise NotImplementedError(f"Error :No infer method for {type(node).__name__}")
    
    def check_Assign_Node(self, node: Assign_Node):
        if node.value is not None:
            inferred_type = self.infer(node.value)
        else:
            inferred_type = None

        if node.type is None:
            if not isinstance(node.ident, str):
                target_type = self.infer(node.ident)
                if inferred_type is not None and not self.is_assignable(target_type, inferred_type):
                    raise SemanticError(f"Error :Cannot assign '{inferred_type}' to element of type '{target_type}'")
                final_type = target_type
                symbol = getattr(node.ident, "symbol", None)
            else:
                symbol = self.current_scope.resolve(node.ident)
                if inferred_type is not None and not self.is_assignable(symbol.type_kind, inferred_type):
                    raise SemanticError(f"Error :Type mismatch for '{symbol.name}': cannot assign '{inferred_type}' to '{symbol.type_kind}'")
                final_type = symbol.type_kind
        else:
            declared_type = self.resolve_type(node.type)
            if inferred_type is not None and not self.is_assignable(declared_type, inferred_type):
                raise SemanticError(f"Error :Type mismatch for '{node.ident}': declared '{declared_type}', got '{inferred_type}'")
            final_type = declared_type
            symbol = self.current_scope.declare(node.ident, final_type)

        node.symbol = symbol
        node.inferred_type = final_type
        return final_type 

    def infer_Bool_Node(self, node: Bool_Node):
        node.inferred_type = Type_Name_Map["bool"]
        return node.inferred_type
    
    def infer_String_Node(self, node: String_Node):
        node.inferred_type = Type_Name_Map["str"]
        return node.inferred_type
        
    def infer_Int_Node(self, node: Int_Node):
        node.inferred_type = Type_Name_Map["int"]
        return node.inferred_type
    
    def infer_Float_Node(self, node: Float_Node):
        node.inferred_type = Type_Name_Map["float"]
        return node.inferred_type

    def infer_Char_Node(self, node: Char_Node):
        node.inferred_type = Type_Name_Map["char"]
        return node.inferred_type

    def infer_Ident_Node(self, node: Ident_Node):
        symbol = self.current_scope.resolve(node.ident)
        node.symbol = symbol
        node.inferred_type = symbol.type_kind
        return node.inferred_type

    def infer_Array_Literal_Node(self, node: Array_Literal_Node):
        if not node.elements:
            node.inferred_type = Type_Name_Map["void"]
            return node.inferred_type 

        first_type = self.infer(node.elements[0])
        for elem in node.elements[1:]:
            elem_type = self.infer(elem)
            if not self.is_assignable(first_type, elem_type):
                raise SemanticError(
                    f"Array Literal has inconsistent element types '{first_type}' and '{elem_type}'"
                )
        node.inferred_type = first_type
        return node.inferred_type      

    def infer_Index_Node(self, node: Index_Node):
        if isinstance(node.target, str):
            symbol = self.current_scope.resolve(node.target)
            target_type = symbol.type_kind
        else:
            target_type = self.infer(node.target)

        index_type = self.infer(node.index)

        if index_type not in INT_TYPES:
            raise SemanticError(f"Array index must be integer, got '{index_type}'")

        node.inferred_type = target_type
        return node.inferred_type 

    def infer_call_Node(self, node: Call_Node):
        proc_symbol = self.current_scope.resolve(node.func)
        if node.arguments:
            for arg in node.arguments:
                self.infer(arg)
            
        node.inferred_type = proc_symbol.type_kind
        return node.inferred_type
    
    def resolve_type(self, node: Type_Node):
        type_name = node.name.lower()
        
        if type_name in Type_Name_Map:
            return Type_Name_Map[type_name]

        # Check if it's a user declared struct in current scope 
        symbol = self.current_scope.resolve(node.name)
        if symbol and getattr(symbol, 'kind', None) == "struct":
            return symbol.name
        
        raise SemanticError(f"Unknown type {node.name}")
    
    def infer_Binaryops_Node(self, node: Binaryops_Node):
        left = self.infer(node.left)
        right = self.infer(node.right)
        op = node.ops

        bool_type = Type_Name_Map["bool"]
        str_type = Type_Name_Map["str"]

        if op == "+" and left == str_type and right == str_type:
            node.inferred_type = str_type
            return node.inferred_type

        if op in {"+", "-", "*", "/"}:
            if left in NUMERIC_TYPES and right in NUMERIC_TYPES:
                if left in FLOAT_TYPES or right in FLOAT_TYPES:
                    node.inferred_type = Type_Name_Map["float"]
                    return node.inferred_type

                node.inferred_type = Type_Name_Map["int"]
                return node.inferred_type

            raise SemanticError(
                f"Operator '{op}' requires numeric operands, got {left} and {right}"
            )

        if op == "%":
            if left in INT_TYPES and right in INT_TYPES:
                node.inferred_type = Type_Name_Map["int"]
                return node.inferred_type

            raise SemanticError(
                f"Operator '%' requires integer operands, got {left} and {right}"
            )

        if op in {"==", "!="}:
            if left == right:
                node.inferred_type = bool_type
                return node.inferred_type

            raise SemanticError(
                f"Operator '{op}' requires matching operand types, got {left} and {right}"
            )

        if op in {"<", "<=", ">", ">="}:
            if left in NUMERIC_TYPES and right in NUMERIC_TYPES:
                node.inferred_type = bool_type
                return node.inferred_type

            raise SemanticError(
                f"Operator '{op}' requires numeric operands, got {left} and {right}"
            )

        if op in {"&&", "||"}:
            if left == bool_type and right == bool_type:
                node.inferred_type = bool_type
                return node.inferred_type

            raise SemanticError(
                f"Operator '{op}' requires bool operands, got {left} and {right}"
            )

        raise SemanticError(f"Unknown binary operator '{op}'")
    
    def infer_Unaryops_Node(self, node: Unaryops_Node):
        operand_type = self.infer(node.operand)
        op = node.ops
        
        if op == "!" and operand_type == Type_Name_Map["bool"]:
            node.inferred_type = Type_Name_Map["bool"]
            return node.inferred_type
    
        elif op == "-" and operand_type in {Type_Name_Map["int"], Type_Name_Map["float"]}:
            node.inferred_type = operand_type
            return node.inferred_type
    
        raise SemanticError(f"Unknown unary operator '{op}' or incompatible operand type '{operand_type}'")
    
    def check_If_Node(self, node: If_Node):
        cond_type = self.infer(node.cond)
        if cond_type != Type_Name_Map["bool"]:
            raise SemanticError(f"Condition in if statement must be of type 'bool', got '{cond_type}'")
        
        if node.if_block:
            self.push_scope()
            try:
                for stmt in node.if_block:
                    self.check(stmt)
            finally:
                self.pop_scope()

        if node.else_block:
            self.push_scope()
            try:
                for stmt in node.else_block:
                    self.check(stmt)
            finally:
                self.pop_scope()

    def check_While_Node(self, node: While_Node):
        cond_type = self.infer(node.cond)
        if cond_type != Type_Name_Map["bool"]:
            raise SemanticError(f"Condition in while statement must be of type 'bool', got '{cond_type}'")
        
        if node.body:
            self.push_scope()
            try:
                for stmt in node.body:
                    self.check(stmt)
            finally:
                self.pop_scope()

    def check_For_Node(self, node: For_Node):
        self.push_scope()
        try:
            if node.is_classic:
                if node.init is not None :
                    self.check(node.init)
                if node.cond is not None :
                    cond_type = self.infer(node.cond)
                if node.increment is not None :
                    self.check(node.increment)
            else : 
                if node.cond is not None :
                    cond_type = self.infer(node.cond)
                    if cond_type != Type_Name_Map["bool"]:
                        raise SemanticError(f"Condition in for statement must be of type 'bool' got '{cond_type}'")      
                elif node.range is not None :
                    if node.init is not None:
                        self.check(node.init)
                    range_type = self.infer(node.range)
            for stmt in node.body:
                self.check(stmt)
        finally :
            self.pop_scope()

    def check_Procedure_Node(self, node: Procedure_Node):
        # Resolve return type and declare function in outer scope
        if node.return_type is not None:
            return_type = self.resolve_type(node.return_type)
        else :
            return_type = Type_Name_Map["void"]

        proc_symbol = self.current_scope.declare(node.ident, return_type)
        node.symbol = proc_symbol

        # Push scope and declare paramerter in function scope 
        self.push_scope(kind="function")
        old_fn_type = getattr(self, "current_fn_type", None)
        self.current_fn_type = return_type
        try : 
            if node.param:
                for param in node.param:
                    param_type = self.resolve_type(param.type_name) if param.type_name else Type_Name_Map['void']
                    param_symbol = self.current_scope.declare(param.name, param_type)
                    param.symbol = param_symbol                    
            # Check body statements
            for stmt in node.body :
                self.check(stmt)
        finally :
            self.current_fn_type = old_fn_type
            self.pop_scope()
                   

    def check_Return_Node(self, node: Return_Node):
        if node.value is not None :
            ret_type = self.infer(node.value)
        else:
            ret_type = Type_Name_Map["void"]
        expected_type = getattr(self, "current_fn_type", Type_Name_Map["void"])
        if ret_type != expected_type:
            raise SemanticError(f"Return type mismatch: expected '{expected_type}' got '{ret_type}") 
               
    def check_Onscreen_Node(self, node:Onscreen_Node):
        node.inferred_type = self.infer(node.expr)
        return node.inferred_type

    def check_Scan_Node(self, node:Scan_Node):
        node.inferred_type = self.infer(node.expr)
        return node.inferred_type


    def check_Array_Decl_Node(self, node: Array_Decl_Node):
        array_type = self.resolve_type(node.type) 
        size = node.size
        name = node.ident

        array_symbol = self.current_scope.declare(name, array_type)
        node.symbol = array_symbol

        if node.value is not None:
            if size != len(node.value.elements):
                raise SemanticError("Array size must match the number of elements")
            
            for elem in node.value.elements:
                elem_type = self.infer(elem)
                if not self.is_assignable(array_type, elem_type):
                    raise SemanticError("Array element type must match array type")

    def check_Call_Node(self, node: Call_Node):
        return self.infer_Call_Node(node)

    def check_Lambda_Node(self, node: Lambda_Node):
        return_type = self.resolve_type(node.return_type) if node.return_type else Type_Name_Map["void"]
        self.push_scope(kind="function")
        old_fn_type = getattr(self, "current_fn_type", None)
        self.current_fn_type = return_type
        try:
            if node.param:
                for p in node.param:
                    param_type = self.infer(p.value) if getattr(p, "value", None) else Type_Name_Map["int"]
                    self.current_scope.declare(p.name, param_type)
            if node.body:
                if isinstance(node.body, list):
                    for stmt in node.body :
                        self.check(stmt)
                else :
                    self.check(node.body)
        finally:
            self.current_fn_type = old_fn_type
            self.pop_scope()

            


    

    def is_assignable(self, expected, actual):
        if expected == actual:
            return True 

        if expected in INT_TYPES and actual == Type_Name_Map["int"]:
            return True

        if expected in FLOAT_TYPES and actual in {Type_Name_Map["int"], Type_Name_Map["float"]}:
            return True

        return False