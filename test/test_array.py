import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from helper import run_pipeline

def test_array_execution():
    code = """
    var [i32, 5] numarray = [10, 20, 30, 40, 50];
    onscreen(numarray[0]);
    onscreen(numarray[4]);
    """
    proc = run_pipeline(code, "test_array.ctz")
    output = proc.stdout.strip().split()
    assert output == ["10", "50"], f"Expected ['10', '50'], got {output}"
    print("✅ test_array_execution PASSED!")

def test_array_mutation():
    code = """
    var [i32, 5] numarray = [10, 20, 30, 40, 50];
    set numarray[0] = 99;
    set numarray[4] = 88;
    onscreen(numarray[0]);
    onscreen(numarray[4]);
    """
    proc = run_pipeline(code, "test_array_mut.ctz")
    output = proc.stdout.strip().split()
    assert output == ["99", "88"], f"Expected ['99', '88'], got {output}"
    print("✅ test_array_mutation PASSED!")

if __name__ == "__main__":
    test_array_execution()
    test_array_mutation()
