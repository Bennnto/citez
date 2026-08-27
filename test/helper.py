import sys
import subprocess
from pathlib import Path

# Add src directory to path
SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

import parse
from semantic import Analyzer
from backend_c import CodeGenerator
from ir import (
    HIRProgram, HIRAssign, HIRInt, HIRFloat, HIRString, HIRBool, HIRChar, HIRBinary, HIRName,
    HIRIf, HIRWhile, HIRFor, HIRProcedure, HIRReturn, HIRBreak, HIRContinue,
    HIROnscreen, HIRScan, HIRArraydecl, HIRArrayliteral, HIRIndex, HIRCall, HIRArgument, HIRPass,
    HIRStructdecl, HIRField, HIRStructaccess, HIRAddress, HIRPointertype, HIRDeref,
    HIRTrap, HIRRaise, HIRBorrow, HIRDrop, HIRAlloc, HIRFree, HIRFieldInit, HIRStructLiteral
)

def lower_to_hir(ast) -> HIRProgram:
    hir_stmts = []
    if hasattr(ast, "statements"):
        for stmt in ast.statements:
            lowered = lower_stmt(stmt)
            if lowered:
                hir_stmts.append(lowered)
    return HIRProgram(statements=hir_stmts)

def lower_stmt(stmt):
    if stmt is None:
        return None
    name = type(stmt).__name__
    if name == "Assign_Node":
        t_name = None
        if stmt.type:
            if type(stmt.type).__name__ == "Pointer_Type_Node":
                base_n = getattr(stmt.type.base_type, "name", "int") if hasattr(stmt.type, "base_type") else "int"
                t_name = f"{base_n}*"
            else:
                t_name = getattr(stmt.type, "name", None)
        target = lower_expr(stmt.ident) if hasattr(stmt, "ident") and not isinstance(stmt.ident, str) else stmt.ident
        return HIRAssign(
            ident=target,
            type=t_name,
            value=lower_expr(stmt.value) if stmt.value else None
        )
    elif name == "Array_Decl_Node":
        t_name = stmt.type.name if stmt.type else "i32"
        val = lower_expr(stmt.value) if stmt.value else None
        return HIRArraydecl(ident=stmt.ident, type=t_name, size=stmt.size, value=val)
    elif name == "Onscreen_Node":
        return HIROnscreen(expr=lower_expr(stmt.expr))
    elif name == "Scan_Node":
        return HIRScan(expr=lower_expr(stmt.expr))
    elif name == "If_Node":
        return HIRIf(
            cond=lower_expr(stmt.cond),
            if_block=[lower_stmt(s) for s in stmt.if_block if s],
            else_block=[lower_stmt(s) for s in stmt.else_block if s] if stmt.else_block else None
        )
    elif name == "While_Node":
        return HIRWhile(
            cond=lower_expr(stmt.cond),
            body=[lower_stmt(s) for s in stmt.body if s]
        )
    elif name == "For_Node":
        return HIRFor(
            is_classic=stmt.is_classic,
            init=lower_stmt(stmt.init) if stmt.init else None,
            cond=lower_expr(stmt.cond) if stmt.cond else None,
            increment=lower_stmt(stmt.increment) if stmt.increment else None,
            range=lower_expr(stmt.range) if stmt.range else None,
            body=[lower_stmt(s) for s in stmt.body if s]
        )
    elif name == "Procedure_Node":
        ret_t = "void"
        if hasattr(stmt, "return_type") and stmt.return_type:
            ret_t = getattr(stmt.return_type, "name", "void")
        return HIRProcedure(
            ident=stmt.ident,
            return_type=ret_t,
            param=[lower_stmt(p) for p in stmt.param] if stmt.param else None,
            body=[lower_stmt(s) for s in stmt.body if s]
        )
    elif name == "Return_Node":
        return HIRReturn(value=lower_expr(stmt.value) if stmt.value else None)
    elif name == "Break_Node":
        return HIRBreak()
    elif name == "Continue_Node":
        return HIRContinue()
    elif name == "Call_Node":
        args = [lower_expr(a) for a in stmt.arguments] if stmt.arguments else []
        return HIRCall(func=stmt.func, arguments=args)
    elif name == "Pass_Node":
        return HIRPass()
    elif name == "Struct_Decl_Node":
        s_name = getattr(stmt, "name", getattr(stmt, "ident", "struct"))
        fields = []
        if stmt.fields:
            for f in stmt.fields:
                t_name = getattr(f.type_name, "name", "int") if hasattr(f, "type_name") else "int"
                fields.append(HIRField(name=f.name, type_name=t_name))
        return HIRStructdecl(name=s_name, fields=fields)
    elif name == "Trap_Node":
        t_block = [lower_stmt(s) for s in stmt.trap_block if s] if stmt.trap_block else []
        c_block = [lower_stmt(s) for s in stmt.catch_block if s] if stmt.catch_block else None
        a_block = [lower_stmt(s) for s in stmt.always_block if s] if stmt.always_block else None
        return HIRTrap(
            trap_block=t_block,
            catch_var=stmt.catch_var,
            catch_block=c_block,
            always_block=a_block
        )
    elif name == "Raise_Node":
        return HIRRaise(expr=lower_expr(stmt.expr) if stmt.expr else None)
    elif name == "Drop_Node":
        t_name = stmt.target if isinstance(stmt.target, str) else getattr(stmt.target, "ident", str(stmt.target))
        return HIRDrop(target=t_name)
    elif name == "Free_Node":
        return HIRFree(target=lower_expr(stmt.target))
    return stmt
    

def lower_expr(expr):
    if expr is None:
        return None
    name = type(expr).__name__
    if name == "Int_Node":
        return HIRInt(value=expr.value, type_name="int")
    elif name == "Float_Node":
        return HIRFloat(value=expr.value, type_name="float")
    elif name == "String_Node":
        return HIRString(value=expr.value, type_name="str")
    elif name == "Bool_Node":
        return HIRBool(value=expr.value, type_name="bool")
    elif name == "Char_Node":
        return HIRChar(value=expr.value, type_name="char")
    elif name == "Ident_Node":
        t_name = "int"
        inf_t = getattr(expr, "inferred_type", None)
        if inf_t:
            t_str = str(inf_t).lower()
            if "str" in t_str:
                t_name = "str"
            elif "float" in t_str:
                t_name = "float"
            elif "char" in t_str:
                t_name = "char"
        return HIRName(name=expr.ident, type_name=t_name)
    elif name == "Binaryops_Node":
        return HIRBinary(
            left=lower_expr(expr.left),
            right=lower_expr(expr.right),
            ops=expr.ops
        )
    elif name == "Array_Literal_Node":
        return HIRArrayliteral(elements=[lower_expr(e) for e in expr.elements])
    elif name == "Index_Node":
        target = lower_expr(expr.target) if hasattr(expr, "target") and not isinstance(expr.target, str) else expr.target
        return HIRIndex(target=target, index=lower_expr(expr.index))
    elif name == "Struct_Access_Node":
        target = lower_expr(expr.target) if hasattr(expr, "target") and not isinstance(expr.target, str) else expr.target
        return HIRStructaccess(target=target, field=expr.field, is_arrow=getattr(expr, "is_arrow", False))
    elif name == "Struct_Literal_Node":
        inits = [HIRFieldInit(field=f.field, value=lower_expr(f.value)) for f in expr.fields] if expr.fields else []
        return HIRStructLiteral(struct_name=expr.struct_name, fields=inits)
    elif name == "Address_Node":
        return HIRAddress(target=lower_expr(expr.target))
    elif name == "Deref_Node":
        return HIRDeref(target=lower_expr(expr.target))
    elif name == "Pointer_Type_Node":
        return HIRPointertype(base_type=expr.base_type.name)
    elif name == "Call_Node":
        args = [lower_expr(a) for a in expr.arguments] if expr.arguments else []
        return HIRCall(func=expr.func, arguments=args)
    elif name == "Argument_Node":
        if expr.value is not None:
            return HIRArgument(name=expr.name, value=lower_expr(expr.value))
        return HIRArgument(name=expr.name, value=None)
    elif name == "Borrow_Node":
        return HIRBorrow(target=lower_expr(expr.target), is_rw=getattr(expr, "is_rw", False))
    elif name == "Alloc_Node":
        t_name = getattr(expr.type, "name", str(expr.type)) if hasattr(expr, "type") else "int"
        return HIRAlloc(type_name=t_name, count=lower_expr(expr.count))
    return expr

def run_pipeline(code_str: str, file_name: str) -> subprocess.CompletedProcess:
    # 1. Parse AST
    ast = parse.parser.parse(code_str)
    assert ast is not None, "Failed to parse AST"

    # 2. Semantic Check
    analyzer = Analyzer()
    analyzer.analyze(ast)

    # 3. Lower AST to HIR
    hir = lower_to_hir(ast)

    # 4. Save to temporary .ctz file & Compile C code
    tmp_file = Path("/tmp") / file_name
    tmp_file.write_text(code_str)

    compiler = CodeGenerator()
    exe_path = compiler.Compile(str(tmp_file), hir)

    # 5. Run compiled binary
    proc = subprocess.run([str(exe_path)], capture_output=True, text=True)
    assert proc.returncode == 0, f"Binary execution failed with code {proc.returncode}"
    return proc
