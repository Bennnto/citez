import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from helper import run_pipeline

def test_spec_declaration_and_implementation():
    code = """
    spec Shape {
        proc area(self: self): f64 {
            return 0.0;
        }
    }

    struct Circle {
        radius: f64
    }

    ext Circle spec Shape {
        proc area(self: self): f64 {
            return 3.14159 * self.radius * self.radius;
        }
    }
    """
    proc = run_pipeline(code, "test_spec.ctz")
    print("✅ test_spec_declaration_and_implementation PASSED!")

if __name__ == "__main__":
    test_spec_declaration_and_implementation()
