import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from helper import run_pipeline

def test_bitwise_operators():
    code = """
    var int a = 5;
    var int b = 3;
    var int res_and = a & b;
    var int res_or  = a | b;
    var int res_xor = a ^ b;
    var int res_not = ~a;
    var int res_shl = a << 2;
    var int res_shr = a >> 1;
    onscreen(res_and);
    """
    proc = run_pipeline(code, "test_bitwise.ctz")
    assert proc.stdout.strip() == "1"
    print("✅ test_bitwise_operators PASSED!")

if __name__ == "__main__":
    test_bitwise_operators()
