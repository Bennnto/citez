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

if __name__ == "__main__":
    test_assign_syntax()
