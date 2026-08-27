import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from helper import run_pipeline

def test_procedure_syntax():
    code = """
    proc add(x: int, y: int): int {
        return x + y;
    }
    var int result = add(10, 20);
    onscreen(result);
    """
    proc = run_pipeline(code, "test_proc.ctz")
    assert proc.stdout.strip() == "30"
    print("✅ test_procedure_syntax PASSED!")

if __name__ == "__main__":
    test_procedure_syntax()
