import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))

from helper import run_pipeline
from semantic import SemanticError

def test_ro_borrow_multiple_reads():
    code = """
    var int val = 100;
    var *int r1 = ro val;
    var *int r2 = ro val;
    onscreen(*r1);
    onscreen(*r2);
    """
    proc = run_pipeline(code, "test_ro_borrow.ctz")
    output_lines = [line.strip() for line in proc.stdout.strip().splitlines()]
    assert output_lines == ["100", "100"]
    print("✅ test_ro_borrow_multiple_reads PASSED!")

def test_rw_borrow_exclusive_mutation():
    code = """
    var int val = 50;
    var *int m1 = rw val;
    set *m1 = 200;
    onscreen(*m1);
    """
    proc = run_pipeline(code, "test_rw_borrow.ctz")
    assert proc.stdout.strip() == "200"
    print("✅ test_rw_borrow_exclusive_mutation PASSED!")

def test_rw_conflict_with_ro():
    code = """
    var int val = 10;
    var *int r1 = ro val;
    var *int m1 = rw val;
    """
    with pytest.raises(SemanticError, match="Cannot borrow 'val' as rw while ro borrow exist"):
        run_pipeline(code, "test_rw_conflict.ctz")
    print("✅ test_rw_conflict_with_ro PASSED!")

def test_use_after_drop_error():
    code = """
    var int x = 42;
    drop x;
    onscreen(x);
    """
    with pytest.raises(SemanticError, match="Use of dropped variable 'x'"):
        run_pipeline(code, "test_drop.ctz")
    print("✅ test_use_after_drop_error PASSED!")

if __name__ == "__main__":
    test_ro_borrow_multiple_reads()
    test_rw_borrow_exclusive_mutation()
    test_rw_conflict_with_ro()
    test_use_after_drop_error()
