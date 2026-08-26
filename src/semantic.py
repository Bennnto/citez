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
        self.visit(program)

    # Core Dispatcher & Aliases
    def visit(self, node):
        if node is None:
            return None
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    # Aliases for backward compatibility with external code
    def check(self, node):
        return self.visit(node)
        
    def infer(self, node):
        return self.visit(node)

    def generic_visit(self, node):
        raise NotImplementedError(f"No visit method implemented for {type(node).__name__}")

    # Scope & Type Helper Utilities
    def visit_block(self, stmts, scope_kind="block"):
        self.push_scope(kind=scope_kind)
        try:
            if isinstance(stmts, list):
                for s in stmts:
                    self.visit(s)
            elif stmts is not None:
                self.visit(stmts)
        finally:
            self.pop_scope()

    def assert_type(self, node, expected_type, context="Expression"):
        actual_type = self.visit(node)
        if not self.is_assignable(expected_type, actual_type):
            raise SemanticError(f"{context} expected type '{expected_type}', got '{actual_type}'")
        return actual_type

    def resolve_type(self, node: Type_Node):
        if not node:
            return Type_Name_Map["void"]
        type_name = node.name.lower() if hasattr(node, "name") else str(node).lower()
        
        if type_name in Type_Name_Map:
            return Type_Name_Map[type_name]

        # Check if it's a user declared struct in current scope 
        symbol = self.current_scope.resolve(node.name if hasattr(node, "name") else str(node))
        if symbol and (getattr(symbol, 'type_kind', None) == "struct" or getattr(symbol, 'kind', None) == "struct"):
            return symbol.name
        
        raise SemanticError(f"Unknown type '{node.name if hasattr(node, 'name') else node}'")

    def is_assignable(self, expected, actual):
        if expected == actual:
            return True 
        if expected in INT_TYPES and actual == Type_Name_Map["int"]:
            return True
        if expected in FLOAT_TYPES and actual in {Type_Name_Map["int"], Type_Name_Map["float"]}:
            return True
        return False

    # AST Node Visitors
    def visit_Program_Node(self, node: Program_Node):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_Assign_Node(self, node: Assign_Node):
        inferred_type = self.visit(node.value) if node.value is not None else None

        if node.type is None:
            if not isinstance(node.ident, str):
                target_type = self.visit(node.ident)
                if inferred_type is not None and not self.is_assignable(target_type, inferred_type):
                    raise SemanticError(f"Cannot assign '{inferred_type}' to element of type '{target_type}'")
                final_type = target_type
                symbol = getattr(node.ident, "symbol", None)
            else:
                symbol = self.current_scope.resolve(node.ident)
                if inferred_type is not None and not self.is_assignable(symbol.type_kind, inferred_type):
                    raise SemanticError(f"Type mismatch for '{symbol.name}': cannot assign '{inferred_type}' to '{symbol.type_kind}'")
                final_type = symbol.type_kind
        else:
            declared_type = self.resolve_type(node.type)
            if inferred_type is not None and not self.is_assignable(declared_type, inferred_type):
                raise SemanticError(f"Type mismatch for '{node.ident}': declared '{declared_type}', got '{inferred_type}'")
            final_type = declared_type
            symbol = self.current_scope.declare(node.ident, final_type)

        node.symbol = symbol
        node.inferred_type = final_type
        return final_type 

    def visit_Bool_Node(self, node: Bool_Node):
        node.inferred_type = Type_Name_Map["bool"]
        return node.inferred_type
    
    def visit_String_Node(self, node: String_Node):
        node.inferred_type = Type_Name_Map["str"]
        return node.inferred_type
        
    def visit_Int_Node(self, node: Int_Node):
        node.inferred_type = Type_Name_Map["int"]
        return node.inferred_type
    
    def visit_Float_Node(self, node: Float_Node):
        node.inferred_type = Type_Name_Map["float"]
        return node.inferred_type

    def visit_Char_Node(self, node: Char_Node):
        node.inferred_type = Type_Name_Map["char"]
        return node.inferred_type

    def visit_Ident_Node(self, node: Ident_Node):
        symbol = self.current_scope.resolve(node.ident)
        node.symbol = symbol
        node.inferred_type = symbol.type_kind
        return node.inferred_type

    def visit_Array_Literal_Node(self, node: Array_Literal_Node):
        if not node.elements:
            node.inferred_type = Type_Name_Map["void"]
            return node.inferred_type 

        first_type = self.visit(node.elements[0])
        for elem in node.elements[1:]:
            elem_type = self.visit(elem)
            if not self.is_assignable(first_type, elem_type):
                raise SemanticError(f"Array Literal has inconsistent element types '{first_type}' and '{elem_type}'")
        node.inferred_type = first_type
        return node.inferred_type      

    def visit_Index_Node(self, node: Index_Node):
        target_type = self.current_scope.resolve(node.target).type_kind if isinstance(node.target, str) else self.visit(node.target)
        index_type = self.visit(node.index)

        if index_type not in INT_TYPES:
            raise SemanticError(f"Array index must be integer, got '{index_type}'")

        node.inferred_type = target_type
        return node.inferred_type 

    def visit_Call_Node(self, node: Call_Node):
        proc_symbol = self.current_scope.resolve(node.func)
        if node.arguments:
            for arg in node.arguments:
                self.visit(arg)
        node.inferred_type = proc_symbol.type_kind
        return node.inferred_type

    def visit_Argument_Node(self, node: Argument_Node):
        if node.value is not None:
            return self.visit(node.value)
        return self.visit(node.name) if isinstance(node.name, (Ident_Node, Int_Node, Float_Node, String_Node, Bool_Node)) else None

    def visit_Binaryops_Node(self, node: Binaryops_Node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.ops

        bool_type = Type_Name_Map["bool"]
        str_type = Type_Name_Map["str"]

        if op == "+" and left == str_type and right == str_type:
            node.inferred_type = str_type
            return node.inferred_type

        if op in {"+", "-", "*", "/"}:
            if left in NUMERIC_TYPES and right in NUMERIC_TYPES:
                node.inferred_type = Type_Name_Map["float"] if (left in FLOAT_TYPES or right in FLOAT_TYPES) else Type_Name_Map["int"]
                return node.inferred_type
            raise SemanticError(f"Operator '{op}' requires numeric operands, got {left} and {right}")

        if op == "%":
            if left in INT_TYPES and right in INT_TYPES:
                node.inferred_type = Type_Name_Map["int"]
                return node.inferred_type
            raise SemanticError(f"Operator '%' requires integer operands, got {left} and {right}")

        if op in {"==", "!="}:
            if left == right:
                node.inferred_type = bool_type
                return node.inferred_type
            raise SemanticError(f"Operator '{op}' requires matching operand types, got {left} and {right}")

        if op in {"<", "<=", ">", ">="}:
            if left in NUMERIC_TYPES and right in NUMERIC_TYPES:
                node.inferred_type = bool_type
                return node.inferred_type
            raise SemanticError(f"Operator '{op}' requires numeric operands, got {left} and {right}")

        if op in {"&&", "||"}:
            if left == bool_type and right == bool_type:
                node.inferred_type = bool_type
                return node.inferred_type
            raise SemanticError(f"Operator '{op}' requires bool operands, got {left} and {right}")

        raise SemanticError(f"Unknown binary operator '{op}'")
    
    def visit_Unaryops_Node(self, node: Unaryops_Node):
        operand_type = self.visit(node.operand)
        op = node.ops
        
        if op == "!" and operand_type == Type_Name_Map["bool"]:
            node.inferred_type = Type_Name_Map["bool"]
            return node.inferred_type
        elif op == "-" and operand_type in {Type_Name_Map["int"], Type_Name_Map["float"]}:
            node.inferred_type = operand_type
            return node.inferred_type
    
        raise SemanticError(f"Unknown unary operator '{op}' or incompatible operand type '{operand_type}'")
    
    def visit_If_Node(self, node: If_Node):
        self.assert_type(node.cond, Type_Name_Map["bool"], "Condition in if statement")
        if node.if_block:
            self.visit_block(node.if_block)
        if node.else_block:
            self.visit_block(node.else_block)

    def visit_While_Node(self, node: While_Node):
        self.assert_type(node.cond, Type_Name_Map["bool"], "Condition in while statement")
        if node.body:
            self.visit_block(node.body)

    def visit_For_Node(self, node: For_Node):
        self.push_scope()
        try:
            if node.is_classic:
                if node.init is not None:
                    self.visit(node.init)
                if node.cond is not None:
                    self.visit(node.cond)
                if node.increment is not None:
                    self.visit(node.increment)
            else: 
                if node.cond is not None:
                    self.assert_type(node.cond, Type_Name_Map["bool"], "Condition in for statement")
                elif node.range is not None:
                    if node.init is not None:
                        self.visit(node.init)
                    self.visit(node.range)
            if node.body:
                for stmt in node.body:
                    self.visit(stmt)
        finally:
            self.pop_scope()

    def visit_Procedure_Node(self, node: Procedure_Node):
        return_type = self.resolve_type(node.return_type) if node.return_type else Type_Name_Map["void"]
        proc_symbol = self.current_scope.declare(node.ident, return_type)
        node.symbol = proc_symbol

        self.push_scope(kind="function")
        old_fn_type = getattr(self, "current_fn_type", None)
        self.current_fn_type = return_type
        try:
            if node.param:
                for param in node.param:
                    param_type = self.resolve_type(param.type_name) if param.type_name else Type_Name_Map['void']
                    param_symbol = self.current_scope.declare(param.name, param_type)
                    param.symbol = param_symbol                    
            if node.body:
                for stmt in node.body:
                    self.visit(stmt)
        finally:
            self.current_fn_type = old_fn_type
            self.pop_scope()

    def visit_Return_Node(self, node: Return_Node):
        ret_type = self.visit(node.value) if node.value is not None else Type_Name_Map["void"]
        expected_type = getattr(self, "current_fn_type", Type_Name_Map["void"])
        if ret_type != expected_type:
            raise SemanticError(f"Return type mismatch: expected '{expected_type}' got '{ret_type}'") 
               
    def visit_Onscreen_Node(self, node: Onscreen_Node):
        node.inferred_type = self.visit(node.expr)
        return node.inferred_type

    def visit_Scan_Node(self, node: Scan_Node):
        node.inferred_type = self.visit(node.expr)
        return node.inferred_type

    def visit_Array_Decl_Node(self, node: Array_Decl_Node):
        array_type = self.resolve_type(node.type) 
        array_symbol = self.current_scope.declare(node.ident, array_type)
        node.symbol = array_symbol

        if node.value is not None:
            if node.size != len(node.value.elements):
                raise SemanticError("Array size must match the number of elements")
            for elem in node.value.elements:
                elem_type = self.visit(elem)
                if not self.is_assignable(array_type, elem_type):
                    raise SemanticError("Array element type must match array type")

    def visit_Lambda_Node(self, node: Lambda_Node):
        return_type = self.resolve_type(node.return_type) if node.return_type else Type_Name_Map["void"]
        self.push_scope(kind="function")
        old_fn_type = getattr(self, "current_fn_type", None)
        self.current_fn_type = return_type
        try:
            if node.param:
                for p in node.param:
                    param_type = self.visit(p.value) if getattr(p, "value", None) else Type_Name_Map["int"]
                    self.current_scope.declare(p.name, param_type)
            if node.body:
                self.visit_block(node.body)
        finally:
            self.current_fn_type = old_fn_type
            self.pop_scope()

    def visit_Struct_Decl_Node(self, node: Struct_Decl_Node):
        s_name = getattr(node, "name", getattr(node, "ident", "struct"))
        struct_symbol = self.current_scope.declare(s_name, "struct")
        field_map = {}
        if node.fields:
            for field in node.fields:
                if field.name in field_map:
                    raise SemanticError(f"Duplicate field '{field.name}' in struct '{s_name}'")
                field_type = self.resolve_type(field.type_name)
                field_map[field.name] = field_type
        struct_symbol.fields = field_map
        node.symbol = struct_symbol

    def visit_Struct_Access_Node(self, node: Struct_Access_Node):
        target_type = self.visit(node.target)
        struct_symbol = self.current_scope.resolve(target_type)
        if not hasattr(struct_symbol, "fields"):
            raise SemanticError(f"Type '{target_type}' is not a struct")
        if node.field not in struct_symbol.fields:
            raise SemanticError(f"Struct '{target_type}' has no field '{node.field}'")
        node.inferred_type = struct_symbol.fields[node.field]
        return node.inferred_type