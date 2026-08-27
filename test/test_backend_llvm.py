import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import parse
import semantic
from helper import lower_to_hir
from backend_llvm import LLVMCodeGenerator

def test_llvm_backend_basic_codegen():
    code = """
    var int x = 10;
    var int y = 20;
    var int z = x + y;
    onscreen(z);
    """
    ast = parse.parser.parse(code)
    analyzer = semantic.Analyzer()
    analyzer.analyze(ast)
    hir = lower_to_hir(ast)

    llvm_gen = LLVMCodeGenerator()
    llvm_ir_str = llvm_gen.generate(hir)

    assert 'define i32 @"main"()' in llvm_ir_str
    assert "alloca i32" in llvm_ir_str
    assert 'call i32 (i8*, ...) @"printf"' in llvm_ir_str
    print("✅ test_llvm_backend_basic_codegen PASSED!")

def test_llvm_backend_control_flow():
    code = """
    var int val = 5;
    if val > 2 {
        onscreen(100);
    } else {
        onscreen(200);
    }
    """
    ast = parse.parser.parse(code)
    analyzer = semantic.Analyzer()
    analyzer.analyze(ast)
    hir = lower_to_hir(ast)

    llvm_gen = LLVMCodeGenerator()
    llvm_ir_str = llvm_gen.generate(hir)

    assert "if.then:" in llvm_ir_str
    assert "if.else:" in llvm_ir_str
    assert "if.end:" in llvm_ir_str
    print("✅ test_llvm_backend_control_flow PASSED!")

if __name__ == "__main__":
    test_llvm_backend_basic_codegen()
    test_llvm_backend_control_flow()
