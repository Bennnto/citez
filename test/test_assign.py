import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from helper import run_pipeline

def test_assign_syntax():
    code = """
    var int x = 10;
    var int y = 20;
    set x = x + y;
    """
    proc = run_pipeline(code, "test_assign.ctz")
    print("✅ test_assign_syntax PASSED!")

def test_pow_operator():
    code = """
    var int res = 2 ** 3;
    onscreen(res);
    """
    proc = run_pipeline(code, "test_pow.ctz")
    assert proc.stdout.strip() == "8"
    print("✅ test_pow_operator PASSED!")

if __name__ == "__main__":
    test_assign_syntax()
    test_pow_operator()
