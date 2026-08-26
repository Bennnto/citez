import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import parse
from semantic import Analyzer

def test_struct_semantic():
    code = """
    struct Point {
        x: int,
        y: int
    }
    """
    ast = parse.parser.parse(code)
    assert ast is not None, "Failed to parse Struct AST"
    analyzer = Analyzer()
    analyzer.analyze(ast)
    
    # Verify Point struct is declared in global scope with correct fields
    symbol = analyzer.global_scope.resolve("Point")
    assert symbol is not None, "Struct Point symbol not found"
    assert hasattr(symbol, "fields"), "Symbol missing fields map"
    from symbol import TYPE_NAME_MAP as Type_Name_Map
    assert symbol.fields == {"x": Type_Name_Map["int"], "y": Type_Name_Map["int"]}
    print("✅ test_struct_semantic PASSED!")

if __name__ == "__main__":
    test_struct_semantic()
