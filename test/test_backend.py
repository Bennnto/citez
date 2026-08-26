import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from backend_c import CodeGenerator
from ir import HIRProgram, HIRAssign, HIRInt, HIRBinary, HIRName, HIRIf

def test_c_string_generation():
    """Approach 1: Verify generated C code string structure."""
    program = HIRProgram(statements=[
        HIRAssign(ident='x', type='i32', value=HIRInt(value=10, type_name='i32')),
        HIRAssign(ident='y', type='i32', value=HIRInt(value=20, type_name='i32')),
        HIRAssign(
            ident='z',
            type='i32',
            value=HIRBinary(
                left=HIRName(name='x', type_name='i32'),
                right=HIRName(name='y', type_name='i32'),
                ops='+'
            )
        )
    ])

    c_code = CodeGenerator().generate(program)

    