import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import parse
from semantic import Analyzer

def test_if_else_statement():
    code = """
    var int x = 10;
    if x > 5 {
        set x = 100;
    } else {
        set x = 10;
    }
    """

    ast = parse.parser.parse(code)
    assert ast is not None
    analyzer = Analyzer()
    analyzer.analyze(ast)
    print("✅ test_if_else_statement passed!")

def test_else_if_statement():
    from helper import run_pipeline
    code = """
    var int x = 15;
    if x > 20 {
        onscreen(1);
    } else if x > 10 {
        onscreen(2);
    } else {
        onscreen(3);
    }
    """
    proc = run_pipeline(code, "test_else_if.ctz")
    assert proc.stdout.strip() == "2"
    print("✅ test_else_if_statement passed!")

if __name__ == "__main__":
    test_if_else_statement()
    test_else_if_statement()

