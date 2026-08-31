import sys
from pathlib import Path

# Add src/ directory to sys.path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR / "src"))

import parse
from semantic import Analyzer, SemanticError
from backend_c import Codegenerate

def main():
    print("Welcome to Citez interactive shell environment. Type 'exit' to quit.\n")
    analyzer = Analyzer()

    while True:
        try:
            line = input(":> ")
            if line.strip() == "exit":
                break
            if not line.strip():
                continue
            
            ast = parse.parser.parse(line)
            if ast is None:
                continue

            analyzer.analyze(ast)
            compiler = Codegenerate()
            c_code = compiler.generate(ast)

            print("--- Generated C Code ---")
            print(c_code)
            print("------------------------")

        except SemanticError as err:
            print(f"❌ Semantic Error: {err}")
        except Exception as err:
            print(f"❌ Error: {err}")

if __name__ == "__main__":
    main()
            

            
