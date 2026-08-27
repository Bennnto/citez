import astnode
from pathlib import Path
import subprocess 
from ir import (
    HIRNode,
    HIRProgram,
    HIRAssign,
    HIRInt,
    HIRName,
    HIRBinary,
    HIRFloat,
    HIRString,
    HIRBool,
    HIRChar,
    HIRIf,
    HIRWhile,
    HIRFor,
    HIRProcedure,
    HIRBreak,
    HIRContinue,
    HIRReturn,
    HIROnscreen,
    HIRScan,
    HIRArrayliteral,
    HIRIndex,
    HIRArraydecl,
    HIRArgument,
    HIRCall,
    HIRPass,
    HIRLambda,
    HIRStructdecl,
    HIRField,
    HIRStructaccess,
    HIRAddress,
    HIRPointertype,
    HIRDeref,
    HIRTrap,
    HIRRaise,
    HIRBorrow,
    HIRDrop,
    HIRAlloc,
    HIRFree,
    HIRFieldInit,
    HIRStructLiteral,
)

TYPE_MAP = {
    "i8": "int8_t",
    "i16": "int16_t",
    "i32": "int32_t",
    "i64": "int64_t",
    "isize": "intptr_t",
    "u8": "uint8_t",
    "u16": "uint16_t",
    "u32": "uint32_t",
    "u64": "uint64_t",
    "usize": "uintptr_t",
    "char": "char",
    "bool": "bool",
    "f32": "double",
    "f64": "double",
    "float": "double",
    "int": "int32_t",
    "str": "const char *",
    "void": "void",
}

def c_type(type_name):
    if not type_name:
        return "int32_t"
    if hasattr(type_name, "name"):
        type_name = type_name.name
    type_key = str(type_name).lower()
    if type_key in TYPE_MAP:
        return TYPE_MAP[type_key]
    return str(type_name)


class Codegenerate:
    def __init__(self):
        self.lines: list[str] = []
        self.indent = 0 
        
    def emit_line(self, line: str = ""):
        self.lines.append("    " * self.indent + line)

    def escape_string(self, s: str) -> str:
        return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')
        
    def generate(self, program: HIRProgram):
        self.emit_header()
        self.emit_line()
        
        main_stmts = []
        fn_stmts = []
        
        if getattr(program, "statements", None):
            for stmt in program.statements:
                if isinstance(stmt, HIRProcedure):
                    fn_stmts.append(stmt)
                else:
                    main_stmts.append(stmt)
            
        for fn in fn_stmts:
            self.emit_stmt(fn)
            self.emit_line()

        self.emit_main(main_stmts)
        
        return "\n".join(self.lines)
    
    def emit_header(self):
        self.emit_line("#include <stdio.h>")
        self.emit_line("#include <stdlib.h>")
        self.emit_line("#include <stdbool.h>")
        self.emit_line("#include <stdint.h>")
        self.emit_line("#include <stddef.h>")
        self.emit_line("#include <math.h>")
        self.emit_line("#include <setjmp.h>")
        self.emit_line()
        self.emit_line("static jmp_buf __citez_jmp_env;")
        self.emit_line('static const char *__citez_err_msg = "";')
        
    def emit_main(self, statements):
        self.emit_line("int main(void) {")
        self.indent += 1
        for stmt in statements:
            self.emit_stmt(stmt)
        self.emit_line("return 0;")
        self.indent -= 1
        self.emit_line("}")
    
    def emit_inline_stmt(self, node) -> str:
        if isinstance(node, HIRAssign):
            if node.type is None:
                if node.value is None:
                    return f"{node.ident}"
                expr = self.emit_expr(node.value)
                return f"{node.ident} = {expr}"
            else:
                c_t = c_type(node.type)
                if node.value is None:
                    return f"{c_t} {node.ident}"
                expr = self.emit_expr(node.value)
                return f"{c_t} {node.ident} = {expr}"
        return ""
        
    def emit_stmt(self, node):
        
        if isinstance(node, HIRAssign):
            target_str = self.emit_expr(node.ident) if isinstance(node.ident, HIRNode) else str(node.ident)
            if node.type is None:
                if node.value is None:
                    self.emit_line(f"{target_str};")
                else:
                    expr = self.emit_expr(node.value)
                    self.emit_line(f"{target_str} = {expr};")
            else:
                c_t = c_type(node.type)
                if node.value is None:
                    self.emit_line(f"{c_t} {target_str};")
                else:
                    expr = self.emit_expr(node.value)
                    self.emit_line(f"{c_t} {target_str} = {expr};")

        elif isinstance(node, HIRIf):
            cond_str = self.emit_expr(node.cond)
            self.emit_line(f"if ({cond_str}) {{")
            self.indent += 1
            for stmt in node.if_block:
                self.emit_stmt(stmt)
            self.indent -= 1

            if node.else_block:
                self.emit_line("} else {")
                self.indent += 1
                for stmt in node.else_block:
                    self.emit_stmt(stmt)
                self.indent -= 1
                self.emit_line("}")
            else : 
                self.emit_line("}")
        
        elif isinstance(node, HIRWhile):
            cond_str = self.emit_expr(node.cond)
            self.emit_line(f"while ({cond_str}) {{")
            self.indent += 1
            for stmt in node.body:
                self.emit_stmt(stmt)
            self.indent -= 1
            self.emit_line("}")

        elif isinstance(node, HIRFor):
            if node.is_classic :
                init = self.emit_inline_stmt(node.init) if node.init else ""
                cond = self.emit_expr(node.cond) if node.cond else ""
                incr = self.emit_inline_stmt(node.increment) if node.increment else ""
                self.emit_line(f"for ({init}; {cond}; {incr}) {{")
            
            elif node.range is not None :
                var_name = node.init.ident if node.init else ""
                range_str = self.emit_expr(node.range)
                self.emit_line(f"for (int32_t {var_name} = 0; {var_name} < {range_str}; {var_name}++) {{")

            elif node.cond is not None :
                cond = self.emit_expr(node.cond)
                self.emit_line(f"while ({cond}) {{")

            self.indent += 1
            for stmt in node.body :
                self.emit_stmt(stmt)
            self.indent -= 1
            self.emit_line("}")
        
        elif isinstance(node, HIRProcedure):
            param_str = ""
            if node.param :
                param_list = []
                for param in node.param:
                    param_type = c_type(param.type_name) if hasattr(param, 'type_name') and param.type_name else "int32_t" 
                    param_name = param.name if hasattr(param, 'name') else str(param)
                    param_list.append(f"{param_type} {param_name}")
                param_str = ", ".join(param_list)
            func_ident = node.ident 
            return_type = c_type(node.return_type) if node.return_type else "void"
            self.emit_line(f"{return_type} {func_ident}({param_str}) {{")
            self.indent += 1
            for stmt in node.body :
                self.emit_stmt(stmt)
            self.indent -= 1
            self.emit_line("}")

        elif isinstance(node, HIRLambda):
            param_str = ""
            if node.param :
                p_list = []
                for p in node.param:
                    p_name = p.name if hasattr(p, "name") else str(p)
                    p_type = c_type(p.type) if hasattr(p, 'type') and p_type else "int32_t"
                    p_list.append(f"{p_type} {p_name}")
                param_str = ", ".join(p_list)
            return_type = c_type(node.return_type) if node.return_type else "void"
            fn_name = getattr(node, "ident", "__lambda_0")
            self.emit_line(f"{return_type} {fn_name}({param_str}) {{")
            self.indent += 1
            if isinstance(node.body , list):
                for stmt in node.body:
                    self.emit_stmt(stmt)
            else:
                self.emit_stmt(node.body)
            self.indent -= 1 
            self.emit_line("}")
            
    
        elif isinstance(node, HIRBreak):
            self.emit_line("break;")

        elif isinstance(node, HIRContinue):
            self.emit_line("continue;")
        
        elif isinstance(node, HIRReturn):
            if node.value is None :
                self.emit_line("return;")
            else :
                self.emit_line(f"return {self.emit_expr(node.value)};")
        
        elif isinstance(node, HIROnscreen):
            expr_str = self.emit_expr(node.expr)
            t_name = getattr(node.expr, "type_name", "int")

            if t_name == "str":
                self.emit_line(f'printf("%s\\n", {expr_str});')
            elif t_name in ("float", "f32", "f64") :
                self.emit_line(f'printf("%f\\n", {expr_str});')
            elif t_name == "char" :
                self.emit_line(f'printf("%c\\n", {expr_str});')
            else:
                self.emit_line(f'printf("%d\\n", {expr_str});')
            
        elif isinstance(node, HIRScan):
            expr_str = self.emit_expr(node.expr)
            t_name = getattr(node.expr, "type_name", "int")

            if t_name == "str":
                self.emit_line(f'scanf("%s", {expr_str});')
            elif t_name in ("float", "f32", "f64"):
                self.emit_line(f'scanf("%f", &{expr_str});')
            elif t_name == "char":
                self.emit_line(f'scanf("%c", &{expr_str});')
            else:
                self.emit_line(f'scanf("%d", &{expr_str});')
        
        elif isinstance(node, HIRArraydecl):
            c_t = c_type(node.type)
            if node.value is None:
                self.emit_line(f"{c_t} {node.ident}[{node.size}];")
            else:
                init_expr = self.emit_expr(node.value)
                self.emit_line(f"{c_t} {node.ident}[{node.size}] = {init_expr};")
        
        elif isinstance(node, HIRCall):
            call_str = self.emit_expr(node)
            self.emit_line(f"{call_str};")
        
        elif isinstance(node, HIRPass):
            self.emit_line("/* pass */")

        elif isinstance(node, HIRStructdecl):
            name = node.name
            self.emit_line(f"typedef struct {name} {{")
            self.indent += 1
            if node.fields :
                for f in node.fields:
                    f_name = f.name if hasattr(f, "name") else str(f)
                    t_value = getattr(f, "type_name", getattr(f, "type", "int"))
                    f_type = c_type(t_value)
                    self.emit_line(f"{f_type} {f_name};")
            self.indent -= 1
            self.emit_line(f"}} {name};")

        elif isinstance(node, HIRTrap):
            self.emit_line("if (setjmp(__citez_jmp_env) == 0) {")
            self.indent += 1
            if node.trap_block:
                for s in node.trap_block:
                    self.emit_stmt(s)
            self.indent -= 1
            if node.catch_block:
                self.emit_line("} else {")
                self.indent += 1
                c_var = node.catch_var if node.catch_var else "err"
                self.emit_line(f"const char *{c_var} = __citez_err_msg;")
                for s in node.catch_block:
                    self.emit_stmt(s)
                self.indent -= 1
                self.emit_line("}")
            else:
                self.emit_line("}")

            if node.always_block:
                for s in node.always_block:
                    self.emit_stmt(s)

        elif isinstance(node, HIRRaise):
            if node.expr is not None:
                err_str = self.emit_expr(node.expr)
                self.emit_line(f"__citez_err_msg = {err_str};")
            else:
                self.emit_line('__citez_err_msg = "Error raised";')
            self.emit_line("longjmp(__citez_jmp_env, 1);")

        elif isinstance(node, HIRDrop):
            self.emit_line(f"/* drop {node.target} */")

        elif isinstance(node, HIRFree):
            target_str = self.emit_expr(node.target)
            self.emit_line(f"free({target_str});")

    

    def emit_expr(self, node) -> str:
        if isinstance(node, HIRName):
            return node.name
        elif isinstance(node, HIRInt):
            return str(node.value)
        elif isinstance(node, HIRFloat):
            return repr(node.value)
        elif isinstance(node, HIRString):
            return '"' + self.escape_string(node.value) + '"'
        elif isinstance(node, HIRChar):
            return "'" + self.escape_string(node.value) + "'"
        elif isinstance(node, HIRBool):
            return "true" if node.value else "false"
        elif isinstance(node, HIRBinary):
            left = self.emit_expr(node.left)
            right = self.emit_expr(node.right)
            if node.ops == "**":
                return f"pow({left}, {right})"
            return f"({left} {node.ops} {right})"
        elif isinstance(node, HIRArrayliteral):
            elems = [self.emit_expr(e) for e in node.elements]
            return "{" + ", ".join(elems) + "}"
        elif isinstance(node, HIRIndex):
            target = self.emit_expr(node.target) if isinstance(node.target, HIRNode) else str(node.target)
            idx = self.emit_expr(node.index)
            return f"{target}[{idx}]"
        elif isinstance(node, HIRArgument):
            if node.value is None:
                return self.emit_expr(node.name) if isinstance(node.name, HIRNode) else str(node.name)
            else :
                return self.emit_expr(node.value)
        elif isinstance(node, HIRCall): 
            func_name = node.func
            if node.arguments:
                arg_strs = [self.emit_expr(arg) for arg in node.arguments]
                args = ", ".join(arg_strs)
                return f"{func_name}({args})"
            else:
                return f"{func_name}()"

        elif isinstance(node, HIRField):
            name = node.name
            c_t = c_type(node.type_name) if node.type_name else str(node.type_name)
            return f"{c_t} {name};"

        elif isinstance(node, HIRStructaccess):
            target = self.emit_expr(node.target)
            field = node.field
            op = "->" if getattr(node, "is_arrow", False) else "."
            return f"{target}{op}{field}"

        elif isinstance(node, HIRStructLiteral):
            inits = [f".{f.field} = {self.emit_expr(f.value)}" for f in node.fields] if node.fields else []
            inits_str = ", ".join(inits)
            return f"(struct {node.struct_name}){{ {inits_str} }}"
        
        elif isinstance(node, HIRAddress):
            target = self.emit_expr(node.target)
            return f"&{target}"

        elif isinstance(node, HIRPointertype):
            base_type = c_type(node.base_type) if node.base_type else str(node.base_type)
            return f"{base_type}*"
        
        elif isinstance(node, HIRDeref):
            target = self.emit_expr(node.target)
            return f"*{target}"

        elif isinstance(node, HIRBorrow):
            target = self.emit_expr(node.target)
            return f"&{target}"

        elif isinstance(node, HIRAlloc):
            ct = c_type(node.type_name)
            cnt = self.emit_expr(node.count)
            return f"({ct} *)malloc(sizeof({ct}) * ({cnt}))"


        return ""
    

    def Compile(self, file_path: str, program: HIRProgram):
        input_path = Path(file_path)
        c_code = self.generate(program)
        c_path = input_path.with_suffix(".c")
        c_path.write_text(c_code)
        exe_path = input_path.with_suffix("")

        compile_proc = subprocess.run(
            ["gcc", str(c_path), "-o", str(exe_path)],
            capture_output=True,
            text=True
        )
        if compile_proc.returncode != 0:
            raise RuntimeError(f"GCC Compilation Failed:\n{compile_proc.stderr}")
        return exe_path

CodeGenerator = Codegenerate