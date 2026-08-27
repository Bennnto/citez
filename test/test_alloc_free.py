import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))

from helper import run_pipeline
from semantic import SemanticError

def test_alloc_and_free_execution():
    code = """
    var int count = 3;
    var *int ptr = alloc(int, count);
    set ptr[0] = 10;
    set ptr[1] = 20;
    set ptr[2] = 30;
    onscreen(ptr[0] + ptr[1] + ptr[2]);
    free(ptr);
    """
    proc = run_pipeline(code, "test_alloc.ctz")
    assert proc.stdout.strip() == "60"
    print("✅ test_alloc_and_free_execution PASSED!")

def test_use_after_free_error():
    code = """
    var int count = 2;
    var *int ptr = alloc(int, count);
    free(ptr);
    onscreen(ptr[0]);
    """
    with pytest.raises(SemanticError, match="Use of dropped variable 'ptr'"):
        run_pipeline(code, "test_use_after_free.ctz")
    print("✅ test_use_after_free_error PASSED!")

if __name__ == "__main__":
    test_alloc_and_free_execution()
    test_use_after_free_error()
