"""Check the unambiguous structural parts of Lion's source conventions."""

import ast
from pathlib import Path


def inspect_module(path):
    errors = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            errors.append((node.lineno, "application machinery must use modules, not classes"))
        elif isinstance(node, ast.Global):
            errors.append((node.lineno, "mutate global containers instead of rebinding them"))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            parameters = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
            ordinary = [parameter for parameter in parameters if parameter.arg != "flags"]
            if len(ordinary) > 2 or node.args.vararg or node.args.kwarg:
                errors.append((node.lineno, f"{node.name}: use at most two ordinary arguments"))
            name = node.name.lstrip("_")
            if name.startswith(("handle_", "on_")) and len(name.split("_")) < 4:
                errors.append((node.lineno, f"{node.name}: callbacks need three meaningful words after the prefix"))
    return errors


def check_source_conventions():
    root = Path(__file__).resolve().parents[1]
    errors = []
    for path in sorted((root / "src" / "arcs").glob("*.py")):
        errors.extend(f"{path.name}:{line}: {message}" for line, message in inspect_module(path))
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    print("Source conventions passed (arguments, callback name shape, classes, global rebinding).")
    print("Naming roles and register/context choices also require human review.")


if __name__ == "__main__":
    check_source_conventions()
