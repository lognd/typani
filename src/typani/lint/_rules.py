"""AST visitor implementing the TYP001-TYP005 misuse rules for typani.lint."""

from __future__ import annotations

import ast
import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typani.lint import Finding

_log = logging.getLogger(__name__)

# frob:doc docs/lint.md#rules
# frob:ticket T-0011
RULES: dict[str, str] = {
    "TYP000": "syntax error while parsing the file",
    "TYP001": "a typani property called as a method (extra parentheses)",
    "TYP002": "truthiness test on a Result/Option payload attribute",
    "TYP003": "a Result/Option value constructed or chained but never inspected",
    "TYP004": "manual propagation boilerplate better written with unwrap()/@propagate",
    "TYP005": "assert on a typani invariant, stripped under python -O",
}

# Properties on Result/Option that are misused when called with zero args.
_PROPERTY_NAMES = frozenset(
    {
        "is_ok",
        "is_err",
        "ok",
        "err",
        "danger_ok",
        "danger_err",
        "notes",
        "is_some",
        "is_nothing",
        "some",
        "danger_some",
        "value",
        "error",
    }
)

# Attribute -> the boolean property that should be tested instead (TYP002).
_TRUTHINESS_ATTRS = {
    "ok": "is_ok",
    "err": "is_err",
    "some": "is_some",
}

# Constructors that always produce a fresh Result/Option (TYP003 a/c).
_CONSTRUCTOR_NAMES = frozenset({"Ok", "Err", "Some", "Nothing"})

# Attribute-call combinators that consume a Result/Option and must be chained
# further or assigned -- calling one as a bare statement discards the result.
# `inspect`/`inspect_err` are deliberately excluded: they exist precisely to
# be called for their side effect with the return value discarded (Rust's
# `inspect` idiom), so a bare `Ok(1).inspect(print)` is not a bug.
_COMBINATOR_ATTRS = frozenset(
    {
        "map",
        "map_err",
        "and_then",
        "or_else",
        "note",
        "filter",
        "ok_or",
        "ok_or_else",
        "to_option",
    }
)

_DANGER_ATTRS = frozenset({"danger_ok", "danger_err", "danger_some"})
_ASSERT_TEST_ATTRS = frozenset({"is_ok", "is_err", "is_some"})

_SUPPRESS_RE = re.compile(r"#.*typani:\s*ignore(?:\[([A-Za-z0-9_,\s]+)\])?")
_SKIP_FILE_RE = re.compile(r"typani:\s*skip-file")


# frob:doc docs/lint.md#is_skip_file
# frob:ticket T-0011
def is_skip_file(source: str) -> bool:
    """True when a 'typani: skip-file' marker appears in the first 5 lines."""
    lines = source.splitlines()[:5]
    return any(_SKIP_FILE_RE.search(line) for line in lines)


# frob:doc docs/lint.md#apply_suppressions
# frob:ticket T-0011
def apply_suppressions(source: str, findings: list["Finding"]) -> list["Finding"]:
    """Drop findings whose source line carries a matching 'typani: ignore' comment."""
    lines = source.splitlines()
    kept: list["Finding"] = []
    for finding in findings:
        if finding.line < 1 or finding.line > len(lines):
            kept.append(finding)
            continue
        match = _SUPPRESS_RE.search(lines[finding.line - 1])
        if match is None:
            kept.append(finding)
            continue
        rule_list = match.group(1)
        if rule_list is None:
            _log.debug(
                "apply_suppressions: %s suppressed at line %d",
                finding.rule,
                finding.line,
            )
            continue
        suppressed_rules = {r.strip() for r in rule_list.split(",")}
        if finding.rule in suppressed_rules:
            _log.debug(
                "apply_suppressions: %s suppressed by rule-specific comment at line %d",
                finding.rule,
                finding.line,
            )
            continue
        kept.append(finding)
    return kept


def _is_result_or_option_annotation(annotation: ast.expr | None) -> bool:
    """True when an unparsed return annotation names Result[...] or Option[...]."""
    if annotation is None:
        return False
    if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
        # A forward-reference string annotation, e.g. `-> "Result[int, str]"`.
        text = annotation.value.strip()
    else:
        try:
            text = ast.unparse(annotation)
        except Exception:  # pragma: no cover - defensive against exotic nodes
            return False
    return (
        text.startswith("Result[")
        or text.startswith("Option[")
        or text in ("Result", "Option")
        or text.startswith("typani.result.Result[")
        or text.startswith("typani.option.Option[")
    )


class _FunctionRegistry(ast.NodeVisitor):
    """First pass: collects same-module functions/methods that return Result/Option.

    Top-level ``def`` statements populate ``module_funcs`` (looked up for
    plain-name calls); ``def`` statements nested one level inside a class
    populate ``method_funcs`` (looked up for ``self.<name>(...)`` calls).
    Deeper nesting (closures) is intentionally left unrecognized -- a miss,
    not a false positive.
    """

    def __init__(self) -> None:
        """Initialize the two name -> qualifies maps this registry builds."""
        self.module_funcs: dict[str, bool] = {}
        self.method_funcs: dict[str, bool] = {}

    def visit_Module(self, node: ast.Module) -> None:
        """Scan only the module's direct statement list for top-level defs."""
        for stmt in node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._record(self.module_funcs, stmt)
            elif isinstance(stmt, ast.ClassDef):
                self._scan_class(stmt)

    def _scan_class(self, node: ast.ClassDef) -> None:
        """Scan a class body's direct statement list for method defs."""
        for stmt in node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._record(self.method_funcs, stmt)

    def _record(
        self,
        table: dict[str, bool],
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        """Store *node*'s Result/Option-returning status into *table* by name."""
        qualifies = _is_result_or_option_annotation(node.returns)
        table[node.name] = qualifies or table.get(node.name, False)


def _is_constructor_call(node: ast.expr) -> bool:
    """True when *node* is a call to Ok/Err/Some/Nothing."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in _CONSTRUCTOR_NAMES
    )


class MisuseVisitor(ast.NodeVisitor):
    """Walks one module's AST and records typani misuse Findings."""

    def __init__(self, path: str) -> None:
        """Bind the visitor to *path* (used only for Finding.path) and reset state."""
        self.path = path
        self.findings: list["Finding"] = []
        self._scope_stack: list[dict[str, bool]] = []
        self._qual_stack: list[str] = []
        registry = _FunctionRegistry()
        self._module_funcs: dict[str, bool] = {}
        self._method_funcs: dict[str, bool] = {}
        self._registry = registry

    def visit_Module(self, node: ast.Module) -> None:
        """Run the function-return-type pre-pass, then walk the module body."""
        self._registry.visit(node)
        self._module_funcs = self._registry.module_funcs
        self._method_funcs = self._registry.method_funcs
        self.generic_visit(node)

    # -- scope tracking for TYP003c local-variable binding ------------------

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Push a fresh local-binding scope and qualname segment, then pop both."""
        self._scope_stack.append({})
        self._qual_stack.append(node.name)
        self.generic_visit(node)
        self._qual_stack.pop()
        self._scope_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Async twin of visit_FunctionDef: same scope push/pop discipline."""
        self._scope_stack.append({})
        self._qual_stack.append(node.name)
        self.generic_visit(node)
        self._qual_stack.pop()
        self._scope_stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Push a qualname segment for the class body, then pop it after visiting."""
        self._qual_stack.append(node.name)
        self.generic_visit(node)
        self._qual_stack.pop()

    def visit_Assign(self, node: ast.Assign) -> None:
        """Track `name = Ok(...)`-shaped bindings so TYP003c can follow the name."""
        if self._scope_stack and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                self._scope_stack[-1][target.id] = self._produces_result_or_option(
                    node.value
                )
        self.generic_visit(node)

    def _produces_result_or_option(self, node: ast.expr) -> bool:
        """True when *node* is a call known (by this pass) to yield a Result/Option."""
        if _is_constructor_call(node):
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            return self._module_funcs.get(node.func.id, False)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "self"
        ):
            return self._method_funcs.get(node.func.attr, False)
        return False

    def _lookup_local(self, name: str) -> bool:
        """True when *name* is bound in the innermost scope to a producing call."""
        if not self._scope_stack:
            return False
        return self._scope_stack[-1].get(name, False)

    def _has_result_option_evidence(self, node: ast.expr) -> bool:
        """True when *node* is (or is bound to) a known Result/Option producer."""
        if self._produces_result_or_option(node):
            return True
        return isinstance(node, ast.Name) and self._lookup_local(node.id)

    # -- TYP001: property called as a method ---------------------------------

    def visit_Call(self, node: ast.Call) -> None:
        """Dispatch TYP001 (property-as-method) and TYP003 (discarded chain) checks."""
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in _PROPERTY_NAMES
            and not node.args
            and not node.keywords
        ):
            self._add(
                "TYP001",
                node,
                f"'{node.func.attr}' is a property, not a method: drop the parentheses",
                "error",
            )
        self.generic_visit(node)

    # -- TYP002: truthiness of a payload attribute ---------------------------

    def _check_truthiness(self, test: ast.expr) -> None:
        """Flag a bare `X.ok`/`X.err`/`X.some` used directly as a boolean test.

        Restricted to subjects with local evidence of being a Result/Option
        (a constructor call, a same-module Result/Option-returning function
        call, or a name bound to one of those earlier in the same function).
        Real-world codebases have plenty of unrelated ``.ok``-named boolean
        fields (e.g. a build report's ``report.ok``); without that evidence
        this rule is dominated by false positives (see docs/lint.md#typ002).
        """
        if (
            isinstance(test, ast.Attribute)
            and test.attr in _TRUTHINESS_ATTRS
            and self._has_result_option_evidence(test.value)
        ):
            is_prop = _TRUTHINESS_ATTRS[test.attr]
            self._add(
                "TYP002",
                test,
                f"'{test.attr}' is the payload or None; falsy payloads "
                f"(0, '', []) will be misread -- test '{is_prop}' instead",
                "error",
            )

    def visit_If(self, node: ast.If) -> None:
        """Check the if/elif test, then continue walking normally."""
        self._check_truthiness(node.test)
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        """Check the while test, then continue walking normally."""
        self._check_truthiness(node.test)
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        """Check a ternary's test expression, then continue walking normally."""
        self._check_truthiness(node.test)
        self.generic_visit(node)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        """Check `not X.ok`-shaped operands, then continue walking normally."""
        if isinstance(node.op, ast.Not):
            self._check_truthiness(node.operand)
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        """Check every operand of an `and`/`or` chain, then continue walking."""
        for value in node.values:
            self._check_truthiness(value)
        self.generic_visit(node)

    # -- TYP003: discarded Result/Option --------------------------------------

    def visit_Expr(self, node: ast.Expr) -> None:
        """Flag a statement that constructs or chains off a Result/Option, discarded."""
        value = node.value
        if isinstance(value, ast.Call):
            if _is_constructor_call(value):
                callee = ast.unparse(value.func)
                self._add(
                    "TYP003",
                    node,
                    f"Result/Option discarded: the value of '{callee}' "
                    "is never inspected",
                    "error",
                )
            elif isinstance(value.func, ast.Name) and self._module_funcs.get(
                value.func.id, False
            ):
                callee = value.func.id
                self._add(
                    "TYP003",
                    node,
                    f"Result/Option discarded: the value of '{callee}' "
                    "is never inspected",
                    "error",
                )
            elif (
                isinstance(value.func, ast.Attribute)
                and isinstance(value.func.value, ast.Name)
                and value.func.value.id == "self"
                and self._method_funcs.get(value.func.attr, False)
            ):
                callee = f"self.{value.func.attr}"
                self._add(
                    "TYP003",
                    node,
                    f"Result/Option discarded: the value of '{callee}' "
                    "is never inspected",
                    "error",
                )
            elif isinstance(value.func, ast.Attribute) and value.func.attr in (
                _COMBINATOR_ATTRS
            ):
                receiver = value.func.value
                receiver_produces = _is_constructor_call(receiver) or (
                    isinstance(receiver, ast.Name) and self._lookup_local(receiver.id)
                )
                if receiver_produces:
                    callee = value.func.attr
                    self._add(
                        "TYP003",
                        node,
                        f"Result/Option discarded: the value of '{callee}' "
                        "is never inspected",
                        "error",
                    )
        self.generic_visit(node)

    # -- TYP004: propagation boilerplate --------------------------------------

    def _check_boilerplate(self, node: ast.If) -> None:
        """Flag `if X.is_err: return Err(X.danger_err)` and the Option twin."""
        if len(node.body) != 1 or not isinstance(node.body[0], ast.Return):
            return
        ret = node.body[0]
        test = node.test
        if not isinstance(test, ast.Attribute):
            return
        subject = test.value

        if test.attr == "is_err" and isinstance(ret.value, ast.Call):
            call = ret.value
            if (
                isinstance(call.func, ast.Name)
                and call.func.id == "Err"
                and len(call.args) == 1
                and not call.keywords
                and isinstance(call.args[0], ast.Attribute)
                and call.args[0].attr == "danger_err"
                and ast.dump(call.args[0].value) == ast.dump(subject)
            ):
                self._add(
                    "TYP004",
                    node,
                    "propagation boilerplate: use 'X.unwrap()' inside an "
                    "@propagate function",
                    "info",
                )
            return

        if test.attr == "is_nothing" and isinstance(ret.value, ast.Call):
            call = ret.value
            if (
                isinstance(call.func, ast.Name)
                and call.func.id == "Nothing"
                and not call.args
                and not call.keywords
            ):
                self._add(
                    "TYP004",
                    node,
                    "propagation boilerplate: use 'X.unwrap()' inside an "
                    "@propagate function",
                    "info",
                )

    # -- TYP005: assert stripped under -O -------------------------------------

    def _check_assert_pair(self, body: list[ast.stmt]) -> None:
        """Scan statements for `assert X.is_ok*` followed by a `X.danger_*` use."""
        for index, stmt in enumerate(body[:-1]):
            if not isinstance(stmt, ast.Assert):
                continue
            test = stmt.test
            if not (
                isinstance(test, ast.Attribute) and test.attr in _ASSERT_TEST_ATTRS
            ):
                continue
            subject_dump = ast.dump(test.value)
            next_stmt = body[index + 1]
            if self._contains_danger_use(next_stmt, subject_dump):
                self._add(
                    "TYP005",
                    stmt,
                    "'assert X.is_ok' is stripped under python -O; use "
                    "'X.unwrap()' or 'X.expect(msg)'",
                    "info",
                )

    def _contains_danger_use(self, node: ast.AST, subject_dump: str) -> bool:
        """True when *node* contains a danger_* attribute access on the same subject."""
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Attribute)
                and child.attr in _DANGER_ATTRS
                and ast.dump(child.value) == subject_dump
            ):
                return True
        return False

    def _walk_body_for_pairs_and_boilerplate(self, body: list[ast.stmt]) -> None:
        """Run TYP004/TYP005 checks over every If/Assert reachable in *body*."""
        self._check_assert_pair(body)
        for stmt in body:
            if isinstance(stmt, ast.If):
                self._check_boilerplate(stmt)

    def visit_Module_body_helper(self) -> None:  # pragma: no cover - unused hook
        """Reserved: not used, structural checks are dispatched via generic hooks."""
        return None

    # Structural bodies are visited generically; hook every statement-list
    # owner so TYP004/TYP005 see every `body` in the tree.
    def _generic_body_visit(self, node: ast.AST) -> None:
        """Run body-level checks for any node exposing a `.body` statement list."""
        body = getattr(node, "body", None)
        if isinstance(body, list):
            self._walk_body_for_pairs_and_boilerplate(body)
        orelse = getattr(node, "orelse", None)
        if isinstance(orelse, list):
            self._walk_body_for_pairs_and_boilerplate(orelse)

    def generic_visit(self, node: ast.AST) -> None:
        """Run body-level TYP004/TYP005 checks, then continue the normal walk."""
        self._generic_body_visit(node)
        super().generic_visit(node)

    # -- shared -----------------------------------------------------------

    def _current_symref(self) -> str:
        """Return this symref: bare path at module scope, else path::qualname."""
        if not self._qual_stack:
            return self.path
        return f"{self.path}::{'.'.join(self._qual_stack)}"

    def _add(self, rule: str, node: ast.AST, message: str, severity: str) -> None:
        """Append one Finding at *node*'s location; imported lazily to avoid a cycle."""
        from typani.lint import Finding

        self.findings.append(
            Finding(
                rule=rule,
                path=self.path,
                line=getattr(node, "lineno", 1),
                col=getattr(node, "col_offset", 0),
                message=message,
                severity=severity,
                symref=self._current_symref(),
            )
        )
