from json import encoder
from dataclasses import dataclass
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
    Field_Node, Struct_Access_Node,
    Pointer_Type_Node, Address_Node,
    Deref_Node, Trap_Node,
    Raise_Node, Borrow_Node,
    Drop_Node, Alloc_Node,
    Free_Node, Field_Init_Node,
    Struct_Literal_Node, Extension_Node,
    Spec_Decl_Node
)
from symbol import Scope, TYPE_NAME_MAP as Type_Name_Map, Symbol, SymbolState

@dataclass(frozen=True)
class PointerType:
    base_type: any

    def __str__(self):
        return f"*{self.base_type}"

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

    def is_lvalue(self, node) -> bool:
        return isinstance(node, (Ident_Node, Index_Node, Struct_Access_Node, Deref_Node))

    def resolve_type(self, node: Type_Node):
        if not node:
            return Type_Name_Map["void"]
        if isinstance(node, Pointer_Type_Node):
            return PointerType(base_type=self.resolve_type(node.base_type))
        type_name = node.name.lower() if hasattr(node, "name") else str(node).lower()
        
        if type_name == "self":
            if getattr(self, "current_struct", None):
                return self.current_struct.name
            return "self"

        if type_name in Type_Name_Map:
            return Type_Name_Map[type_name]

        # Check if it's a user declared struct in current scope 
        try:
            symbol = self.current_scope.resolve(node.name if hasattr(node, "name") else str(node))
            if symbol and (getattr(symbol, 'type_kind', None) in ("struct", "spec") or getattr(symbol, 'kind', None) in ("struct", "spec")):
                return symbol.name
        except NameError:
            pass
        
        raise SemanticError(f"Unknown type '{node.name if hasattr(node, 'name') else node}'")

    def is_assignable(self, expected, actual):
        if expected == actual:
            return True 
        if isinstance(expected, PointerType) and isinstance(actual, PointerType):
            return self.is_assignable(expected.base_type, actual.base_type)
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
        if symbol.state == SymbolState.DROPPED:
            raise SemanticError(f"Use of dropped variable '{symbol.name}'")
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
        if isinstance(node.target, str):
            target_symbol = self.current_scope.resolve(node.target)
            if target_symbol.state == SymbolState.DROPPED:
                raise SemanticError(f"Use of dropped variable '{target_symbol.name}'")
            target_type = target_symbol.type_kind
        else:
            target_type = self.visit(node.target)

        index_type = self.visit(node.index)

        if index_type not in INT_TYPES:
            raise SemanticError(f"Array index must be integer, got '{index_type}'")

        element_type = target_type.base_type if isinstance(target_type, PointerType) else target_type
        node.inferred_type = element_type
        return node.inferred_type
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

        if op in {"+", "-", "*", "/", "**"}:
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

        if op in {"&", "|", "^", "<<", ">>"}:
            if left in INT_TYPES and right in INT_TYPES:
                node.inferred_type = left
                return node.inferred_type
            raise SemanticError(f"Bitwise operator '{op}' requires integer operands, got {left} and {right}")

        if op in {"&&", "||"}:
            if left == bool_type and right == bool_type:
                node.inferred_type = bool_type
                return node.inferred_type
            raise SemanticError(f"Operator '{op}' requires bool operands, got {left} and {right}")

        raise SemanticError(f"Unknown binary operator '{op}'")
    
    def visit_Unaryops_Node(self, node: Unaryops_Node):
        operand_type = self.visit(node.operand)
        op = node.ops
        
        if op == "~" and operand_type in INT_TYPES:
            node.inferred_type = operand_type
            return node.inferred_type
        elif op == "!" and operand_type == Type_Name_Map["bool"]:
            node.inferred_type = Type_Name_Map["bool"]
            return node.inferred_type
        elif op == "-" and operand_type in NUMERIC_TYPES:
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
        if not self.is_assignable(expected_type, ret_type):
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
        if isinstance(target_type, PointerType):
            target_type = target_type.base_type

        struct_name = getattr(target_type, "name", str(target_type))
        struct_symbol = self.current_scope.resolve(struct_name)
        if not hasattr(struct_symbol, "fields"):
            raise SemanticError(f"Type '{struct_name}' is not a struct")
        if node.field not in struct_symbol.fields:
            raise SemanticError(f"Struct '{struct_name}' has no field '{node.field}'")
        node.inferred_type = struct_symbol.fields[node.field]
        return node.inferred_type

    def visit_Struct_Literal_Node(self, node: Struct_Literal_Node):
        struct_symbol = self.current_scope.resolve(node.struct_name)
        if not hasattr(struct_symbol, "fields"):
            raise SemanticError(f"'{node.struct_name}' is not a struct")

        if node.fields:
            for f_init in node.fields:
                if f_init.field not in struct_symbol.fields:
                    raise SemanticError(f"Struct '{node.struct_name}' has no field '{f_init.field}'")
                val_type = self.visit(f_init.value)
                expected_type = struct_symbol.fields[f_init.field]
                if not self.is_assignable(expected_type, val_type):
                    raise SemanticError(f"Cannot assign type '{val_type}' to field '{f_init.field}' of type '{expected_type}'")

        node.inferred_type = self.resolve_type(node.struct_name)
        return node.inferred_type

    def visit_Address_Node(self, node: Address_Node):
        if not self.is_lvalue(node.target):
            raise SemanticError("Cannot take address of a non-lvalue expression")
        target_type = self.visit(node.target)
        node.inferred_type = PointerType(base_type=target_type)
        return node.inferred_type

    def visit_Deref_Node(self, node: Deref_Node):
        target_type = self.visit(node.target)
        if not isinstance(target_type, PointerType):
            raise SemanticError(f"Cannot dereference non-pointer type '{target_type}'")
        node.inferred_type = target_type.base_type
        return node.inferred_type

    def visit_Trap_Node(self, node: Trap_Node):
        if node.trap_block:
            self.visit_block(node.trap_block)
        if node.catch_block:
            self.push_scope(kind="block")
            try:
                if node.catch_var:
                    self.current_scope.declare(node.catch_var, Type_Name_Map["str"])
                if isinstance(node.catch_block, list):
                    for stmt in node.catch_block:
                        self.visit(stmt)
                else:
                    self.visit(node.catch_block)
            finally:
                self.pop_scope()
        if node.always_block:
            self.visit_block(node.always_block)

    def visit_Raise_Node(self, node: Raise_Node):
        if node.expr is not None:
            self.visit(node.expr)

    def visit_Borrow_Node(self, node: Borrow_Node):
        # Evaluate target expression & get target symbol
        target_type = self.visit(node.target)
        target_name = node.target.ident if isinstance(node.target, Ident_Node) else None
        target_symbol = self.current_scope.resolve(target_name) if target_name else None

        if target_symbol :
            if target_symbol.state == SymbolState.DROPPED :
                raise SemanticError(f"Cannot borrow dropped variable '{target_symbol.name}'")
        
            if node.is_rw :
                if target_symbol.ro_borrow_count > 0 :
                    raise SemanticError(f"Cannot borrow '{target_symbol.name}' as rw while ro borrow exist")
                if target_symbol.rw_claimed :
                    raise SemanticError(f"Cannot borrow '{target_symbol.name}' as rw more than once")

                target_symbol.state = SymbolState.BORROWED_RW
                target_symbol.rw_claimed = True
            else:
                if target_symbol.rw_claimed:
                    raise SemanticError(f"Cannot borrow '{target_symbol.name}' as ro while rw borrow exists")

                target_symbol.state = SymbolState.BORROWED_RO
                target_symbol.ro_borrow_count += 1
        node.inferred_type = PointerType(base_type =target_type)
        return node.inferred_type 
    
    def visit_Drop_Node(self, node: Drop_Node):
        target_name = node.target if isinstance(node.target, str) else getattr(node.target, "ident", str(node.target))
        symbol = self.current_scope.resolve(target_name)
        if symbol.state == SymbolState.DROPPED:
            raise SemanticError(f"Variable '{symbol.name}' was already dropped")
        if symbol.ro_borrow_count > 0 or symbol.rw_claimed:
            raise SemanticError(f"Cannot drop '{symbol.name}' while active borrows exists")
        symbol.state = SymbolState.DROPPED

    def visit_Alloc_Node(self, node: Alloc_Node):
        count_type = self.visit(node.count)
        if count_type not in INT_TYPES:
            raise SemanticError(f"Alloc count must be integer, got '{count_type}'")
        element_type = self.resolve_type(node.type)
        node.inferred_type = PointerType(base_type=element_type)
        return node.inferred_type

    def visit_Free_Node(self, node: Free_Node):
        target_type = self.visit(node.target)
        target_name = node.target.ident if isinstance(node.target, Ident_Node) else None
        if target_name:
            symbol = self.current_scope.resolve(target_name)
            if symbol.state == SymbolState.DROPPED:
                raise SemanticError(f"Variable '{symbol.name}' was already freed/dropped")
            symbol.state = SymbolState.DROPPED
    

    def visit_Extension_Node(self, node: Extension_Node):
        try:
            struct_symbol = self.current_scope.resolve(node.ident)
        except NameError:
            raise SemanticError(f"Struct '{node.ident}' is not declared")

        if getattr(struct_symbol, "type_kind", None) != "struct":
            raise SemanticError(f"Type '{node.ident}' is not a struct and cannot be extended")

        if not hasattr(struct_symbol, "methods"):
            struct_symbol.methods = {}

        # If implementing a spec (e.g. ext Circle spec Shape)
        if getattr(node, "for_spec", None):
            try:
                spec_symbol = self.current_scope.resolve(node.for_spec)
            except NameError:
                raise SemanticError(f"Spec '{node.for_spec}' is not declared")

            if hasattr(spec_symbol, "methods"):
                methods_list = getattr(node, "method", getattr(node, "body", []))
                impl_methods = {stmt.ident for stmt in methods_list if hasattr(stmt, "ident")}
                for req_method in spec_symbol.methods:
                    if req_method not in impl_methods:
                        raise SemanticError(
                            f"Struct '{node.ident}' missing method '{req_method}' required by spec '{node.for_spec}'"
                        )

        # 1. Set current struct context for "self" resolution
        old_struct = getattr(self, "current_struct", None)
        self.current_struct = struct_symbol
        try:
            methods_list = getattr(node, "method", getattr(node, "body", []))
            if methods_list:
                for stmt in methods_list:
                    if isinstance(stmt, Procedure_Node):
                        struct_symbol.methods[stmt.ident] = stmt
                    self.visit(stmt)
        finally:
            self.current_struct = old_struct

    def visit_Spec_Decl_Node(self, node: Spec_Decl_Node):
        name = node.ident
        spec_symbol = self.current_scope.declare(name, "spec")
        spec_symbol.methods = {}
        if node.methods:
            for met in node.methods:
                if isinstance(met, Procedure_Node):
                    spec_symbol.methods[met.ident] = met
                             
