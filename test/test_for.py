import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from helper import run_pipeline

def test_for_syntax():
    code = """
    for var int i = 0; i < 5; set i = i + 1 {
        var int x = i;
    }
    """
    proc = run_pipeline(code, "test_for.ctz")
    print("✅ test_for_syntax PASSED!")

if __name__ == "__main__":
    test_for_syntax()
