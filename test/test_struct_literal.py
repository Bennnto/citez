import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))

from helper import run_pipeline
from semantic import SemanticError

def test_struct_literal_instantiation():
    code = """
    struct Point {
        x: int,
        y: int
    }

    var Point p = Point { x: 10, y: 20 };
    onscreen(p.x);
    onscreen(p.y);
    """
    proc = run_pipeline(code, "test_struct_lit.ctz")
    output_lines = [line.strip() for line in proc.stdout.strip().splitlines()]
    assert output_lines == ["10", "20"]
    print("✅ test_struct_literal_instantiation PASSED!")

def test_pointer_arrow_access():
    code = """
    struct Player {
        id: int,
        score: int
    }

    var Player p1 = Player { id: 7, score: 99 };
    var *Player p_ref = ro p1;
    onscreen(p_ref->id);
    onscreen(p_ref->score);
    """
    proc = run_pipeline(code, "test_arrow.ctz")
    output_lines = [line.strip() for line in proc.stdout.strip().splitlines()]
    assert output_lines == ["7", "99"]
    print("✅ test_pointer_arrow_access PASSED!")

def test_struct_literal_type_mismatch():
    code = """
    struct Point {
        x: int,
        y: int
    }

    var Point p = Point { x: "invalid", y: 20 };
    """
    with pytest.raises(SemanticError, match="Cannot assign type"):
        run_pipeline(code, "test_struct_mismatch.ctz")
    print("✅ test_struct_literal_type_mismatch PASSED!")

if __name__ == "__main__":
    test_struct_literal_instantiation()
    test_pointer_arrow_access()
    test_struct_literal_type_mismatch()
