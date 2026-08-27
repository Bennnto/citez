import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from helper import run_pipeline

def test_trap_catch_always():
    code = """
    proc divide(a: int, b: int): int {
        if b == 0 {
            raise "Division by zero!";
        }
        return a / b;
    }

    trap {
        var int result = divide(10, 0);
        onscreen(result);
    } catch err {
        onscreen(err);
    } always {
        onscreen("Cleanup always runs!");
    }
    """
    proc = run_pipeline(code, "test_trap.ctz")
    output_lines = [line.strip() for line in proc.stdout.strip().splitlines()]
    assert output_lines == [
        "Division by zero!",
        "Cleanup always runs!"
    ]
    print("✅ test_trap_catch_always PASSED!")

def test_trap_normal_flow_always():
    code = """
    trap {
        onscreen("Inside trap block");
    } catch err {
        onscreen(err);
    } always {
        onscreen("Always block executed");
    }
    """
    proc = run_pipeline(code, "test_trap_normal.ctz")
    output_lines = [line.strip() for line in proc.stdout.strip().splitlines()]
    assert output_lines == [
        "Inside trap block",
        "Always block executed"
    ]
    print("✅ test_trap_normal_flow_always PASSED!")

if __name__ == "__main__":
    test_trap_catch_always()
    test_trap_normal_flow_always()
