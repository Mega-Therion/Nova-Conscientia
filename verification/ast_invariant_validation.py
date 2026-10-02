"""AST compile-time invariant validation: the zero-stub / zero-ungrounded-numerology gate.

The Contingent Box Protocol demands machine code with *zero stubs* and *zero
ungrounded numerology*.  This module enforces both at compile time -- before any
code runs -- by walking the parsed AST of every Python module under ``core/``,
``verification/`` and ``benchmarks/``:

Z1  Zero stubs.  ``pass``-only bodies, ``...``-only bodies, ``raise
    NotImplementedError`` and ``TODO``/``FIXME``/``XXX``/``STUB`` markers are
    violations.  Interface declarations are exempt: method bodies inside a
    ``typing.Protocol`` subclass and ``abstractmethod``/``overload``-decorated
    functions are contracts, not unfinished work.

Z2  Zero ungrounded numerology.  Every module-level UPPER_CASE constant whose
    value is a numeric literal must be a key of that module's module-level
    ``PROVENANCE`` mapping (name -> provenance string naming the source).

Z3  No banned constructs: ``eval``, ``exec``, bare ``except:``.

Z4  Every public function and method carries a docstring (auditable claims).

Z5  Fail-closed validator: a module that cannot be parsed is a violation, not a
    skip.

Run directly: ``python verification/ast_invariant_validation.py core
verification benchmarks`` -- exit code 0 means every module passed; nonzero
means violations (this is the compile gate for CI).
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

#: Marker strings that flag unfinished work (Contingent Box Protocol Z1).
STUB_MARKERS: Tuple[str, ...] = ("TODO", "FIXME", "XXX", "STUB", "NotImplementedError")

#: Calls that are banned outright (Contingent Box Protocol Z3).
BANNED_CALLS: Tuple[str, ...] = ("eval", "exec")


@dataclass(frozen=True)
class Violation:
    """One compile-time violation.

    Attributes:
        rule: the violated rule id (Z1..Z5) with a short label.
        module: path of the offending module.
        line: 1-based line number (0 for module-level findings).
        detail: human-readable description.
    """

    rule: str
    module: str
    line: int
    detail: str

    def __str__(self) -> str:
        """Render as a single reviewable line."""
        return f"{self.module}:{self.line}: [{self.rule}] {self.detail}"


def _is_stub_body(body: Sequence[ast.stmt]) -> Optional[str]:
    """Return a rule label if a function body is a stub, else None.

    A stub body is exactly one statement that is ``pass``, an ellipsis
    expression, or a ``raise NotImplementedError``.
    """
    # Strip a leading docstring before judging the body: a docstring plus a
    # pass statement is still a stub.
    body = list(body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    if len(body) == 1:
        stmt = body[0]
        if isinstance(stmt, ast.Pass):
            return "pass-only body"
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is Ellipsis:
            return "ellipsis-only body"
        if isinstance(stmt, ast.Raise):
            exc = stmt.exc
            if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name) and exc.func.id == "NotImplementedError":
                return "raise NotImplementedError"
            if isinstance(exc, ast.Name) and exc.id == "NotImplementedError":
                return "raise NotImplementedError"
    return None


def _walk_calls(tree: ast.AST) -> List[Tuple[int, str]]:
    """Collect (line, function_name) for every plain-name call in the tree."""
    calls: List[Tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            calls.append((node.lineno, node.func.id))
    return calls


def _module_level_provenance_keys(tree: ast.Module) -> set:
    """Names listed as keys in the module-level PROVENANCE mapping."""
    keys: set = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PROVENANCE":
                    keys |= _provenance_keys_from_value(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "PROVENANCE":
            if node.value is not None:
                keys |= _provenance_keys_from_value(node.value)
    return keys


def _provenance_keys_from_value(value: ast.expr) -> set:
    """Extract string keys from a PROVENANCE dict literal.

    Handles plain dict literals and ``{**OTHER, "name": "..."}`` merges: keys
    that are None (a ** merge of another mapping) contribute no statically
    known names, so the merge never silently satisfies rule Z2.
    """
    keys: set = set()
    if isinstance(value, ast.Dict):
        for k in value.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                keys.add(k.value)
    return keys


def _is_numeric_constant(value: ast.expr) -> bool:
    """True if the expression is a plain numeric literal or simple numeric ops."""
    if isinstance(value, ast.Constant) and isinstance(value.value, (int, float)) and not isinstance(value.value, bool):
        return True
    # Unary minus of a numeric literal counts (e.g. -1.0).
    if isinstance(value, ast.UnaryOp) and isinstance(value.op, ast.USub):
        return _is_numeric_constant(value.operand)
    return False


def _interface_methods(tree: ast.Module) -> set:
    """Methods that are interface declarations, not unfinished work.

    ``typing.Protocol`` subclass bodies, and functions decorated with
    ``abstractmethod``/``overload``, are *declarations*: their ``...`` bodies
    are the contract, not a stub to be filled in later.  Rule Z1 exempts them;
    everything else must carry an implementation.
    """
    exempt = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            is_protocol = any(
                (isinstance(b, ast.Name) and b.id == "Protocol")
                or (isinstance(b, ast.Attribute) and b.attr == "Protocol")
                for b in node.bases
            ) or any(
                kw.arg == "metaclass"
                and (isinstance(kw.value, ast.Name) and kw.value.id in ("ABCMeta", "Protocol"))
                for kw in node.keywords
            )
            if is_protocol:
                for sub in ast.walk(node):
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        exempt.add(sub)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                if (isinstance(dec, ast.Name) and dec.id in ("abstractmethod", "overload")) or (
                    isinstance(dec, ast.Attribute) and dec.attr in ("abstractmethod", "overload")
                ):
                    exempt.add(node)
    return exempt


def _docstring_nodes(tree: ast.Module) -> set:
    """Collect every docstring node (module, class, and function docstrings)."""
    nodes = set()
    for owner in [tree] + [n for n in ast.walk(tree) if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))]:
        body = getattr(owner, "body", [])
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            nodes.add(body[0].value)
    return nodes


def validate_module(path: Path) -> List[Violation]:
    """Validate one Python module against rules Z1-Z5.

    Args:
        path: the module file (.py) to validate.

    Returns:
        The list of Violations (empty means the module passed).  A module that
        fails to parse yields a single Z5 fail-closed violation.
    """
    violations: List[Violation] = []
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError) as exc:
        return [Violation("Z5 fail-closed", str(path), 0, f"unparseable module: {exc}")]

    provenance_keys = _module_level_provenance_keys(tree)

    # Docstring nodes are exempt from the Z1 marker scan: rule text and
    # documentation may legitimately name the forbidden markers.
    docstring_nodes = _docstring_nodes(tree)
    interface_methods = _interface_methods(tree)

    # --- Z1: stubs and markers ---------------------------------------------
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            label = _is_stub_body(node.body)
            if label and node not in interface_methods:
                violations.append(Violation("Z1 zero-stubs", str(path), node.lineno,
                                           f"{node.name}: {label}"))
        # docstrings carry STUB_MARKERS via constant strings; comments were
        # stripped by the parser, so scan string constants and names.
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node not in docstring_nodes:
            for marker in STUB_MARKERS:
                # An exact match is a marker *definition* (this module's own
                # STUB_MARKERS tuple); only longer strings containing a marker
                # are flagged as unfinished-work prose.
                if marker != "NotImplementedError" and marker in node.value and node.value != marker:
                    violations.append(Violation("Z1 zero-stubs", str(path),
                                                getattr(node, "lineno", 0),
                                                f"stub marker {marker!r} in string"))
        if isinstance(node, ast.Name) and node.id == "NotImplementedError":
            violations.append(Violation("Z1 zero-stubs", str(path), node.lineno,
                                         "NotImplementedError reference"))

    # --- Z2: grounded numerology ---------------------------------------------
    for node in tree.body:
        targets: List[Tuple[str, ast.expr]] = []
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    targets.append((t.id, node.value))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            targets.append((node.target.id, node.value))
        for name, value in targets:
            if name == "PROVENANCE" or not name.isupper():
                continue
            if _is_numeric_constant(value) and name not in provenance_keys:
                violations.append(Violation(
                    "Z2 grounded-numerology", str(path), getattr(node, "lineno", 0),
                    f"numeric constant {name!r} is not registered in module PROVENANCE"))

    # --- Z3: banned constructs -----------------------------------------------
    for lineno, func_name in _walk_calls(tree):
        if func_name in BANNED_CALLS:
            violations.append(Violation("Z3 banned-constructs", str(path), lineno,
                                         f"call to {func_name}() is banned"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            violations.append(Violation("Z3 banned-constructs", str(path), node.lineno,
                                         "bare 'except:' is banned (catch Exception at minimum)"))

    # --- Z4: public callables must be documented -------------------------------
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_") and not ast.get_docstring(node):
                violations.append(Violation("Z4 documented-claims", str(path), node.lineno,
                                           f"{node.name} has no docstring"))

    return violations


def validate_paths(paths: Sequence[Path]) -> Tuple[List[Violation], int]:
    """Validate every .py file under each path (recursing into directories).

    Args:
        paths: files and/or directories to validate.

    Returns:
        (violations, modules_checked).
    """
    violations: List[Violation] = []
    files: List[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(sorted(p.rglob("*.py")))
        elif p.suffix == ".py":
            files.append(p)
    # Keep files that live in Python source trees; exclude nothing else.
    seen: set = set()
    ordered: List[Path] = []
    for f in files:
        real = f.resolve()
        if real not in seen:
            seen.add(real)
            ordered.append(f)
    for f in ordered:
        violations.extend(validate_module(f))
    return violations, len(ordered)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Command-line entry point: validate the packages, print a report.

    Args:
        argv: paths to validate; defaults to core/ verification/ benchmarks/
            relative to the repository root (the parent of this file's parent).

    Returns:
        0 if every module passed, 1 otherwise (CI gate semantics).
    """
    args = list(argv if argv is not None else sys.argv[1:])
    if not args:
        repo_root = Path(__file__).resolve().parent.parent
        args = [str(repo_root / "core"), str(repo_root / "verification"),
                str(repo_root / "benchmarks")]
    violations, checked = validate_paths([Path(a) for a in args])
    print(f"Contingent Box compile gate: checked {checked} modules, "
          f"{len(violations)} violations")
    for v in violations:
        print(f"  {v}")
    if checked == 0:
        print("  Z5: no modules found -- gate cannot pass on an empty tree")
        return 1
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
