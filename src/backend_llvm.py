from llvmlite import ir, binding
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

class LLVMCodeGenerator:
    def __init__(self):
        self.module = ir.Module(name="citez_module")
        self.module.triple = binding.get_default_triple()
        # Variable Environment: map variable names to LLVM alloca pointers
        self.variables = {}

        # Context tracking
        self.builder = None
        self.func = None

        # Setup standard C runtime function prototypes
        self.setup_builtins()
    
    def setup_builtins(self):
        printf_type = ir.FunctionType(ir.IntType(32), [ir.PointerType(ir.IntType(8))], var_arg=True)
        self.printf = ir.Function(self.module, printf_type, name="printf")

        malloc_type = ir.FunctionType(ir.PointerType(ir.IntType(8)), [ir.IntType(64)])
        self.malloc = ir.Function(self.module, malloc_type, name="malloc")

        free_type = ir.FunctionType(ir.VoidType(), [ir.PointerType(ir.IntType(8))])
        self.free = ir.Function(self.module, free_type, name="free")

    def to_llvm_type(self, type_name: str) -> ir.Type:
        if type_name is None:
            return ir.IntType(32)
        
        if isinstance(type_name, str):
            if type_name.endswith("*"):
                base_type = type_name[:-1]
                return ir.PointerType(self.to_llvm_type(base_type))

            t = type_name.lower()
            if t in ("int", "i32", "isize", "usize"):
                return ir.IntType(32)
            elif t == "i64":
                return ir.IntType(64)
            elif t == "i16":
                return ir.IntType(16)
            elif t in ("i8", "char", "u8"):
                return ir.IntType(8)
            elif t in ("f32", "float"):
                return ir.FloatType()
            elif t == "f64":
                return ir.DoubleType()
            elif t == "bool":
                return ir.IntType(1)
            elif t == "str":
                return ir.PointerType(ir.IntType(8))
            elif t == "void":
                return ir.VoidType()
        return ir.IntType(32)

    def emit_expr(self, node):
        if isinstance(node, HIRInt):
            return ir.Constant(ir.IntType(32), int(node.value))
        elif isinstance(node, HIRFloat):
            return ir.Constant(ir.FloatType(), float(node.value))
        elif isinstance(node, HIRBool):
            return ir.Constant(ir.IntType(1), 1 if node.value else 0)
        elif isinstance(node, HIRString):
            fmt = node.value + "\0"
            c_str = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)), bytearray(fmt.encode("utf-8")))
            global_str = ir.GlobalVariable(self.module, c_str.type, name=f".str.{id(node)}")
            global_str.linkage = 'internal'
            global_str.global_constant = True
            global_str.initializer = c_str
            zero = ir.Constant(ir.IntType(32), 0)
            return self.builder.gep(global_str, [zero, zero])

        elif isinstance(node, HIRName):
            if node.name in self.variables:
                ptr = self.variables[node.name]
                return self.builder.load(ptr, name=node.name)
            raise RuntimeError(f"Undefined variable in LLVM backend: '{node.name}'")

        elif isinstance(node, HIRBinary):
            left = self.emit_expr(node.left)
            right = self.emit_expr(node.right)
            op = node.ops
            # Float math
            if isinstance(left.type, ir.FloatType) or isinstance(right.type, ir.FloatType):
                if op == "+": return self.builder.fadd(left, right)
                elif op == "-": return self.builder.fsub(left, right)
                elif op == "*": return self.builder.fmul(left, right)
                elif op == "/": return self.builder.fdiv(left, right)
                elif op in ("==", "!=", "<", ">", "<=", ">="):
                    return self.builder.fcmp_ordered(op, left, right)

            # Integer math
            if op == "+":
                return self.builder.add(left, right)
            elif op == "-":
                return self.builder.sub(left, right)
            elif op == "*":
                return self.builder.mul(left, right)
            elif op == "/":
                return self.builder.sdiv(left, right)
            elif op == "%":
                return self.builder.srem(left, right)
            elif op in ("==", "!=", "<", ">", "<=", ">="):
                return self.builder.icmp_signed(op, left, right)

        elif isinstance(node, HIRAddress):
            if isinstance(node.target, HIRName):
                return self.variables[node.target.name]
        
        elif isinstance(node, HIRDeref):
            ptr = self.emit_expr(node.target)
            return self.builder.load(ptr)

        elif isinstance(node, HIRBorrow):
            if isinstance(node.target, HIRName):
                return self.variables[node.target.name]
            return self.emit_expr(node.target)

        elif isinstance(node, HIRAlloc):
            elem_type = self.to_llvm_type(node.type_name)
            cnt = self.emit_expr(node.count)
            if cnt.type != ir.IntType(64):
                cnt = self.builder.zext(cnt, ir.IntType(64))
            size_const = ir.Constant(ir.IntType(64), 4)
            total_bytes = self.builder.mul(cnt, size_const)
            raw_ptr = self.builder.call(self.malloc, [total_bytes])
            return self.builder.bitcast(raw_ptr, ir.PointerType(elem_type))

        elif isinstance(node, HIRCall):
            func_name = node.func
            if hasattr(self.module, "globals") and func_name in self.module.globals:
                callee = self.module.globals[func_name]
                args = [self.emit_expr(a.value if isinstance(a, HIRArgument) else a) for a in (node.arguments or [])]
                return self.builder.call(callee, args)

        return None

    def emit_string_literal(self, text: str):
        if not hasattr(self, "string_constants"):
            self.string_constants = {}
            self.string_counter = 0

        if text in self.string_constants:
            return self.string_constants[text]

        self.string_counter += 1
        fmt = text + "\0"
        c_str = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)), bytearray(fmt.encode("utf-8")))
        global_str = ir.GlobalVariable(self.module, c_str.type, name=f".str.{self.string_counter}")
        global_str.linkage = 'internal'
        global_str.global_constant = True
        global_str.initializer = c_str
        zero = ir.Constant(ir.IntType(32), 0)
        gep = self.builder.gep(global_str, [zero, zero])
        self.string_constants[text] = gep
        return gep

    def emit_stmt(self, node):
        if isinstance(node, HIRAssign):
            var_name = node.ident if isinstance(node.ident, str) else getattr(node.ident, "name", str(node.ident))
            llvm_type = self.to_llvm_type(node.type)
            if var_name not in self.variables:
                ptr = self.builder.alloca(llvm_type, name=var_name)
                self.variables[var_name] = ptr
            else:
                ptr = self.variables[var_name]
            if node.value is not None:
                val = self.emit_expr(node.value)
                self.builder.store(val, ptr)

        elif isinstance(node, HIROnscreen):
            val = self.emit_expr(node.expr)
            if isinstance(val.type, ir.IntType) and val.type.width == 32:
                fmt_str = self.emit_string_literal("%d\n")
                self.builder.call(self.printf, [fmt_str, val])
            elif isinstance(val.type, (ir.FloatType, ir.DoubleType)):
                fmt_str = self.emit_string_literal("%f\n")
                val_double = self.builder.fpext(val, ir.DoubleType()) if isinstance(val.type, ir.FloatType) else val
                self.builder.call(self.printf, [fmt_str, val_double])
            elif isinstance(val.type, ir.PointerType):
                fmt_str = self.emit_string_literal("%s\n")
                self.builder.call(self.printf, [fmt_str, val])

        elif isinstance(node, HIRIf):
            cond_val = self.emit_expr(node.cond)
            then_block = self.func.append_basic_block(name="if.then")
            else_block = self.func.append_basic_block(name="if.else")
            merge_block = self.func.append_basic_block(name="if.end")

            self.builder.cbranch(cond_val, then_block, else_block)

            # Then block
            self.builder.position_at_end(then_block)
            if node.if_block:
                for s in node.if_block:
                    self.emit_stmt(s)
            if not self.builder.block.is_terminated:
                self.builder.branch(merge_block)

            # Else block
            self.builder.position_at_end(else_block)
            if node.else_block:
                for s in node.else_block:
                    self.emit_stmt(s)
            if not self.builder.block.is_terminated:
                self.builder.branch(merge_block)

            self.builder.position_at_end(merge_block)

        elif isinstance(node, HIRWhile):
            cond_block = self.func.append_basic_block(name="while.cond")
            body_block = self.func.append_basic_block(name="while.body")
            after_block = self.func.append_basic_block(name="while.end")

            self.builder.branch(cond_block)

            # Cond block
            self.builder.position_at_end(cond_block)
            cond_val = self.emit_expr(node.cond)
            self.builder.cbranch(cond_val, body_block, after_block)

            # Body block
            self.builder.position_at_end(body_block)
            if node.body:
                for s in node.body:
                    self.emit_stmt(s)
            if not self.builder.block.is_terminated:
                self.builder.branch(cond_block)

            self.builder.position_at_end(after_block)

        elif isinstance(node, HIRProcedure):
            param_types = [self.to_llvm_type(p.type_name) for p in (node.params or [])]
            ret_type = self.to_llvm_type(node.return_type)
            func_type = ir.FunctionType(ret_type, param_types)

            proc_func = ir.Function(self.module, func_type, name=node.name)
            entry_block = proc_func.append_basic_block(name="entry")

            old_builder, old_func, old_vars = self.builder, self.func, dict(self.variables)
            self.func = proc_func
            self.builder = ir.IRBuilder(entry_block)

            for idx, p in enumerate(node.params or []):
                p_ptr = self.builder.alloca(param_types[idx], name=p.name)
                self.builder.store(proc_func.args[idx], p_ptr)
                self.variables[p.name] = p_ptr

            if node.body:
                for s in node.body:
                    self.emit_stmt(s)

            if not self.builder.block.is_terminated:
                if isinstance(ret_type, ir.VoidType):
                    self.builder.ret_void()
                else:
                    self.builder.ret(ir.Constant(ret_type, 0))

            self.builder, self.func, self.variables = old_builder, old_func, old_vars

        elif isinstance(node, HIRFree):
            ptr = self.emit_expr(node.target)
            raw_ptr = self.builder.bitcast(ptr, ir.PointerType(ir.IntType(8)))
            self.builder.call(self.free, [raw_ptr])

        elif isinstance(node, HIRReturn):
            if node.expr is not None:
                val = self.emit_expr(node.expr)
                self.builder.ret(val)
            else:
                self.builder.ret_void()

    def generate(self, program: HIRProgram) -> str:
        main_type = ir.FunctionType(ir.IntType(32), [])
        main_func = ir.Function(self.module, main_type, name="main")
        entry_block = main_func.append_basic_block(name="entry")

        self.func = main_func
        self.builder = ir.IRBuilder(entry_block)

        if program and program.statements:
            for stmt in program.statements:
                self.emit_stmt(stmt)

        if not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(ir.IntType(32), 0))

        return str(self.module)