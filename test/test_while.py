import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from helper import run_pipeline

def test_while_syntax():
    code = """
    var int count = 5;
    while count > 0 {
        set count = count - 1;
    }
    """
    proc = run_pipeline(code, "test_while.ctz")
    print("✅ test_while_syntax PASSED!")

if __name__ == "__main__":
    test_while_syntax()
