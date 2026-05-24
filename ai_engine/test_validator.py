"""
Test Validator — AST-based gate that blocks bad AI-generated code before execution.
Checks: syntax, test functions, assertions, forbidden patterns.
This is the "validation layer" recommended in v2 architecture.
"""
from __future__ import annotations
import ast, re, sys
from pathlib import Path

# Patterns that must NOT appear in generated tests
_FORBIDDEN = [
    r"\bimport subprocess\b",
    r"\bos\.system\s*\(",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\b__import__\s*\(",
    r"open\s*\(.+['\"][wa]['\"]",    # file write/append
    r"shutil\.rmtree",
    r"os\.remove",
]


def validate_syntax(code: str) -> tuple[bool, str]:
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError line {e.lineno}: {e.msg}"


def has_test_functions(code: str) -> tuple[bool, str]:
    # Match BOTH module-level (^def test_) and class-method-level (    def test_)
    # Using \bdef instead of ^def so indented class methods are also detected.
    funcs = re.findall(r"\bdef (test_\w+)\s*\(", code)
    if not funcs:
        return False, "No test_ functions found"
    return True, f"{len(funcs)} test function(s)"


def has_assertions(code: str) -> tuple[bool, str]:
    if re.search(r"\bassert\b", code) or re.search(r"\bexpect\s*\(", code):
        return True, "assertions present"
    return False, "No assertions found (assert/expect missing)"


def check_forbidden(code: str) -> list[str]:
    return [p for p in _FORBIDDEN if re.search(p, code)]


def validate_code(code: str) -> dict:
    """Validate a code string. Returns {valid, errors, warnings}."""
    errors, warnings = [], []

    ok, msg = validate_syntax(code)
    if not ok:
        errors.append(msg)

    ok, msg = has_test_functions(code)
    if not ok:
        errors.append(msg)

    ok, msg = has_assertions(code)
    if not ok:
        warnings.append(msg)

    forbidden = check_forbidden(code)
    if forbidden:
        errors.append(f"Forbidden patterns: {forbidden}")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def validate_file(file_path: Path) -> dict:
    try:
        code = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return {"file": str(file_path), "valid": False, "errors": [str(e)], "warnings": []}
    result = validate_code(code)
    result["file"] = str(file_path)
    return result


def validate_directory(tests_dir: Path) -> tuple[bool, list[dict]]:
    results = [validate_file(f) for f in sorted(tests_dir.glob("test_*.py"))]
    return all(r["valid"] for r in results), results


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("tests")
    if path.is_file():
        r = validate_file(path)
        print("✅ VALID" if r["valid"] else "❌ INVALID", path)
        for e in r["errors"]:   print(f"  ERROR:   {e}")
        for w in r["warnings"]: print(f"  WARNING: {w}")
        sys.exit(0 if r["valid"] else 1)
    else:
        ok, results = validate_directory(path)
        for r in results:
            print(("✅" if r["valid"] else "❌"), r["file"])
            for e in r["errors"]:   print(f"    ERROR:   {e}")
            for w in r["warnings"]: print(f"    WARNING: {w}")
        sys.exit(0 if ok else 1)
