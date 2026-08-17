#!/usr/bin/env python3
"""CST-based de-Java-ify transformation for hero-designer-python.

Converts Java-style get_/set_/is_ methods to Pythonic @property / bare names
using libcst for safe, syntax-aware transformations.

Usage:
    python scripts/dejavaify.py --phase 1 --dry-run
    python scripts/dejavaify.py --phase 2
    python scripts/dejavaify.py --phase 3
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import libcst as cst
import libcst.matchers as m

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dejavaify_config import ATTRIBUTE_RENAMES, EXCLUDE_METHODS, SETTER_PAIRS

# Directories to process (relative to repo root)
SEARCH_DIRS = ("kirby_cost", "tests", "scripts")

# Files to skip (this script and its config)
SKIP_FILES = {"dejavaify.py", "dejavaify_config.py"}

# The dataclass file whose attributes must NOT be renamed in Phase 2
DATACLASS_REL = "kirby_cost/template/dataclasses.py"


# ===========================================================================
# Helpers
# ===========================================================================

def collect_py_files(repo: Path) -> list[Path]:
    """Return all .py files under SEARCH_DIRS, skipping SKIP_FILES."""
    files: list[Path] = []
    for d in SEARCH_DIRS:
        dirpath = repo / d
        if dirpath.is_dir():
            files.extend(
                p for p in sorted(dirpath.rglob("*.py"))
                if p.name not in SKIP_FILES
            )
    return files


def strip_prefix(name: str) -> str | None:
    """Strip get_/set_/is_ prefix, returning the bare name or None."""
    if name.startswith("get_"):
        return name[4:]
    if name.startswith("set_"):
        return name[4:]
    if name.startswith("is_"):
        return name[3:]
    return None


# ===========================================================================
# Phase 1: Non-conflicting parameterless get_/is_ → @property
# ===========================================================================

class _MethodScanner(cst.CSTVisitor):
    """First pass: collect method signatures across all files."""

    def __init__(self) -> None:
        # method_name -> set of file paths where it's defined
        self.methods: dict[str, set[str]] = {}
        self._current_file: str = ""

    def set_file(self, path: str) -> None:
        self._current_file = path

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        name = node.name.value
        self.methods.setdefault(name, set()).add(self._current_file)


def _has_property_decorator(node: cst.FunctionDef) -> bool:
    """Check if a FunctionDef already has @property."""
    for dec in node.decorators:
        if m.matches(dec.decorator, m.Name("property")):
            return True
    return False


def _is_setter_decorator(node: cst.FunctionDef, prop_name: str) -> bool:
    """Check if a FunctionDef has @prop_name.setter."""
    for dec in node.decorators:
        if m.matches(
            dec.decorator,
            m.Attribute(value=m.Name(prop_name), attr=m.Name("setter")),
        ):
            return True
    return False


def _param_count(node: cst.FunctionDef) -> int:
    """Count non-self parameters."""
    params = node.params
    count = len(params.params)
    # First param is typically 'self'
    if count > 0 and params.params[0].name.value == "self":
        count -= 1
    return count


class Phase1Transformer(cst.CSTTransformer):
    """Convert non-conflicting parameterless get_/is_ methods to @property.

    Also converts matching set_ methods to @X.setter and updates call sites.
    """

    def __init__(self, targets: set[str], setter_targets: dict[str, str]) -> None:
        super().__init__()
        # targets: set of getter method names to convert (e.g. "get_foo")
        self.targets = targets
        # setter_targets: getter_name -> setter_name for those that have setters
        self.setter_targets = setter_targets
        # Derived: setter_name -> property_name
        self._setter_to_prop: dict[str, str] = {}
        for getter, setter in setter_targets.items():
            prop = strip_prefix(getter)
            if prop:
                self._setter_to_prop[setter] = prop
        # Stats
        self.methods_converted = 0
        self.setters_converted = 0
        self.calls_updated = 0

    def _prop_name(self, method_name: str) -> str | None:
        return strip_prefix(method_name)

    def leave_FunctionDef(
        self, original: cst.FunctionDef, updated: cst.FunctionDef
    ) -> cst.FunctionDef | cst.RemovalSentinel:
        name = updated.name.value

        # --- Convert getter → @property ---
        if name in self.targets:
            if _has_property_decorator(updated):
                return updated
            if _param_count(updated) != 0:
                return updated
            prop = self._prop_name(name)
            if prop is None:
                return updated

            self.methods_converted += 1
            prop_decorator = cst.Decorator(
                decorator=cst.Name("property"),
                leading_lines=[],
            )
            new_decorators = list(updated.decorators) + [prop_decorator]
            return updated.with_changes(
                name=cst.Name(prop),
                decorators=new_decorators,
            )

        # --- Convert setter → @X.setter ---
        if name in self._setter_to_prop:
            if _param_count(updated) != 1:
                return updated
            prop = self._setter_to_prop[name]
            # Check not already a setter
            if _is_setter_decorator(updated, prop):
                return updated

            self.setters_converted += 1
            setter_decorator = cst.Decorator(
                decorator=cst.Attribute(
                    value=cst.Name(prop), attr=cst.Name("setter")
                ),
                leading_lines=[],
            )
            new_decorators = list(updated.decorators) + [setter_decorator]
            return updated.with_changes(
                name=cst.Name(prop),
                decorators=new_decorators,
            )

        return updated

    def leave_Call(
        self, original: cst.Call, updated: cst.Call
    ) -> cst.BaseExpression:
        """Rewrite .get_foo() → .foo and .is_foo() → .foo call sites."""
        # Match: expr.method_name()
        if not m.matches(updated.func, m.Attribute()):
            return updated

        func = updated.func
        assert isinstance(func, cst.Attribute)
        method_name = func.attr.value

        # --- getter call sites ---
        if method_name in self.targets and len(updated.args) == 0:
            prop = self._prop_name(method_name)
            if prop is None:
                return updated
            self.calls_updated += 1
            return func.with_changes(attr=cst.Name(prop))

        # --- setter call sites: .set_foo(val) → .foo = val ---
        # We do NOT rewrite setter call sites to assignment here because
        # `.set_foo(val)` → `obj.foo = val` is a statement-level change
        # that requires parent-node awareness.  Instead we just rename
        # the method call to match the new @setter name.
        # Actually, setter call sites like obj.set_foo(val) need to stay as
        # method calls to the new name.  But since @X.setter is invoked via
        # assignment, we need to convert these to assignments.
        # However, libcst makes this hard at the Call level because we'd need
        # to replace the entire SimpleStatementLine.
        # For now, just rename the call: .set_foo(val) → .foo(val)
        # which will fail at runtime — but Phase 1 SETTER_PAIRS is small (3)
        # and we'll do a targeted fix after.
        # Actually let's handle this properly in leave_SimpleStatementLine.

        return updated

    def leave_Expr(
        self, original: cst.Expr, updated: cst.Expr
    ) -> cst.BaseExpression | cst.RemovalSentinel | cst.Expr:
        """Convert standalone obj.set_foo(val) → obj.foo = val."""
        # We only handle Expr nodes containing a Call to a setter
        if not isinstance(updated.value, cst.Call):
            return updated

        call = updated.value
        if not m.matches(call.func, m.Attribute()):
            return updated

        func = call.func
        assert isinstance(func, cst.Attribute)
        method_name = func.attr.value

        if method_name not in self._setter_to_prop:
            return updated
        if len(call.args) != 1:
            return updated

        prop = self._setter_to_prop[method_name]
        value_arg = call.args[0].value

        self.calls_updated += 1
        # Build: obj.prop = value
        return cst.Expr(
            value=cst.Assign(
                targets=[
                    cst.AssignTarget(
                        target=cst.Attribute(
                            value=func.value,
                            attr=cst.Name(prop),
                        )
                    )
                ],
                value=value_arg,
            )
        )


# ===========================================================================
# Phase 2: Attribute-conflicting methods — rename attrs, then convert
# ===========================================================================

class Phase2AttrRenamer(cst.CSTTransformer):
    """Rename self.X → self._X for all attributes in ATTRIBUTE_RENAMES.

    Skips the dataclass file.
    """

    def __init__(self, renames: dict[str, str], is_dataclass_file: bool = False) -> None:
        super().__init__()
        self.renames = renames  # attr_name -> _attr_name
        self.is_dataclass_file = is_dataclass_file
        self.attrs_renamed = 0
        # Track whether we're inside a class that is a dataclass
        self._in_dataclass = False
        self._class_stack: list[bool] = []

    def visit_ClassDef(self, node: cst.ClassDef) -> bool:
        is_dc = False
        if self.is_dataclass_file:
            for dec in node.decorators:
                if m.matches(dec.decorator, m.Name("dataclass")) or m.matches(
                    dec.decorator, m.Call(func=m.Name("dataclass"))
                ):
                    is_dc = True
                    break
        self._class_stack.append(is_dc)
        self._in_dataclass = is_dc
        return True

    def leave_ClassDef(self, original: cst.ClassDef, updated: cst.ClassDef) -> cst.ClassDef:
        self._class_stack.pop()
        self._in_dataclass = bool(self._class_stack and self._class_stack[-1])
        return updated

    def leave_Attribute(
        self, original: cst.Attribute, updated: cst.Attribute
    ) -> cst.Attribute:
        if self._in_dataclass:
            return updated

        attr_name = updated.attr.value
        if attr_name not in self.renames:
            return updated

        # Only rename self.X access
        if m.matches(updated.value, m.Name("self")):
            self.attrs_renamed += 1
            return updated.with_changes(
                attr=cst.Name(self.renames[attr_name])
            )

        return updated


class Phase2MethodTransformer(cst.CSTTransformer):
    """Convert get_X → @property X (and set_X → @X.setter) for Phase 2 targets.

    Also updates call sites.
    """

    def __init__(self, targets: set[str], setter_targets: dict[str, str]) -> None:
        super().__init__()
        # targets: set of getter names like "get_base_cost"
        self.targets = targets
        self.setter_targets = setter_targets
        self._setter_to_prop: dict[str, str] = {}
        for getter, setter in setter_targets.items():
            prop = strip_prefix(getter)
            if prop:
                self._setter_to_prop[setter] = prop
        self.methods_converted = 0
        self.setters_converted = 0
        self.calls_updated = 0

    def leave_FunctionDef(
        self, original: cst.FunctionDef, updated: cst.FunctionDef
    ) -> cst.FunctionDef:
        name = updated.name.value

        if name in self.targets:
            if _has_property_decorator(updated):
                return updated
            if _param_count(updated) != 0:
                return updated
            prop = strip_prefix(name)
            if prop is None:
                return updated

            self.methods_converted += 1
            prop_decorator = cst.Decorator(
                decorator=cst.Name("property"),
                leading_lines=[],
            )
            return updated.with_changes(
                name=cst.Name(prop),
                decorators=list(updated.decorators) + [prop_decorator],
            )

        if name in self._setter_to_prop:
            if _param_count(updated) != 1:
                return updated
            prop = self._setter_to_prop[name]
            if _is_setter_decorator(updated, prop):
                return updated

            self.setters_converted += 1
            setter_decorator = cst.Decorator(
                decorator=cst.Attribute(
                    value=cst.Name(prop), attr=cst.Name("setter")
                ),
                leading_lines=[],
            )
            return updated.with_changes(
                name=cst.Name(prop),
                decorators=list(updated.decorators) + [setter_decorator],
            )

        return updated

    def leave_Call(
        self, original: cst.Call, updated: cst.Call
    ) -> cst.BaseExpression:
        if not m.matches(updated.func, m.Attribute()):
            return updated

        func = updated.func
        assert isinstance(func, cst.Attribute)
        method_name = func.attr.value

        if method_name in self.targets and len(updated.args) == 0:
            prop = strip_prefix(method_name)
            if prop is None:
                return updated
            self.calls_updated += 1
            return func.with_changes(attr=cst.Name(prop))

        return updated

    def leave_Expr(
        self, original: cst.Expr, updated: cst.Expr
    ) -> cst.Expr:
        if not isinstance(updated.value, cst.Call):
            return updated

        call = updated.value
        if not m.matches(call.func, m.Attribute()):
            return updated

        func = call.func
        assert isinstance(func, cst.Attribute)
        method_name = func.attr.value

        if method_name not in self._setter_to_prop:
            return updated
        if len(call.args) != 1:
            return updated

        prop = self._setter_to_prop[method_name]
        value_arg = call.args[0].value

        self.calls_updated += 1
        return cst.Expr(
            value=cst.Assign(
                targets=[
                    cst.AssignTarget(
                        target=cst.Attribute(
                            value=func.value,
                            attr=cst.Name(prop),
                        )
                    )
                ],
                value=value_arg,
            )
        )


# ===========================================================================
# Phase 3: Parameterized method renames
# ===========================================================================

class Phase3Scanner(cst.CSTTransformer):
    """Collect parameterized get_/set_/is_ methods (read-only scan)."""

    def __init__(self, already_converted: set[str]) -> None:
        super().__init__()
        self.already_converted = already_converted
        self.targets: set[str] = set()  # method names to rename

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        name = node.name.value
        if name in EXCLUDE_METHODS or name in self.already_converted:
            return
        bare = strip_prefix(name)
        if bare is None:
            return
        # Must have params beyond self
        if _param_count(node) == 0:
            return
        # Skip if already a property or setter
        if _has_property_decorator(node):
            return
        self.targets.add(name)


class Phase3Transformer(cst.CSTTransformer):
    """Rename parameterized get_/set_/is_ methods, dropping the prefix."""

    def __init__(self, targets: set[str]) -> None:
        super().__init__()
        self.targets = targets
        self.methods_renamed = 0
        self.calls_updated = 0

    def leave_FunctionDef(
        self, original: cst.FunctionDef, updated: cst.FunctionDef
    ) -> cst.FunctionDef:
        name = updated.name.value
        if name not in self.targets:
            return updated
        bare = strip_prefix(name)
        if bare is None:
            return updated
        self.methods_renamed += 1
        return updated.with_changes(name=cst.Name(bare))

    def leave_Call(
        self, original: cst.Call, updated: cst.Call
    ) -> cst.BaseExpression:
        if not m.matches(updated.func, m.Attribute()):
            return updated
        func = updated.func
        assert isinstance(func, cst.Attribute)
        method_name = func.attr.value
        if method_name not in self.targets:
            return updated
        bare = strip_prefix(method_name)
        if bare is None:
            return updated
        self.calls_updated += 1
        return updated.with_changes(
            func=func.with_changes(attr=cst.Name(bare))
        )


# ===========================================================================
# Orchestration
# ===========================================================================

def _parse_file(path: Path) -> cst.Module:
    return cst.parse_module(path.read_text())


def _determine_phase1_targets(
    repo: Path, files: list[Path]
) -> tuple[set[str], dict[str, str]]:
    """Determine which get_/is_ methods are Phase 1 targets.

    Returns (getter_targets, setter_pairs_for_phase1).
    """
    conflicting = set(ATTRIBUTE_RENAMES.keys())
    targets: set[str] = set()

    for fpath in files:
        try:
            tree = _parse_file(fpath)
        except Exception:
            continue

        for node in tree.children:
            _scan_methods_in_node(node, targets, conflicting)

    # Filter to non-conflicting, non-excluded parameterless getters
    # We collected all get_/is_ method names; now filter
    return targets, {
        g: s for g, s in SETTER_PAIRS.items() if g in targets
    }


def _scan_methods_in_node(
    node: cst.CSTNode, targets: set[str], conflicting: set[str]
) -> None:
    """Recursively scan for get_/is_ method defs."""
    if isinstance(node, cst.FunctionDef):
        name = node.name.value
        if name in EXCLUDE_METHODS:
            return
        bare = strip_prefix(name)
        if bare is None:
            return
        if not name.startswith("set_"):  # only getters/is_ for property conversion
            if bare in conflicting:
                return  # Phase 2
            if _has_property_decorator(node):
                return
            if _param_count(node) != 0:
                return  # Phase 3
            targets.add(name)
    elif isinstance(node, cst.ClassDef):
        for child in node.body.body:
            _scan_methods_in_node(child, targets, conflicting)
    elif isinstance(node, cst.If):
        # Handle if TYPE_CHECKING blocks etc
        for child in node.body.body:
            _scan_methods_in_node(child, targets, conflicting)


def _determine_phase1_setter_targets(
    files: list[Path], getter_targets: set[str]
) -> dict[str, str]:
    """Find set_ methods that correspond to Phase 1 getters."""
    # Build mapping: for each getter target, what's the expected setter name?
    possible_setters: dict[str, str] = {}  # setter_name -> prop_name
    for getter_name in getter_targets:
        bare = strip_prefix(getter_name)
        if bare:
            setter_name = f"set_{bare}"
            possible_setters[setter_name] = bare

    # Also include explicit SETTER_PAIRS
    for getter, setter in SETTER_PAIRS.items():
        if getter in getter_targets:
            bare = strip_prefix(getter)
            if bare:
                possible_setters[setter] = bare

    # Scan files for setter definitions
    found_setters: dict[str, str] = {}  # getter_name -> setter_name
    for fpath in files:
        try:
            tree = _parse_file(fpath)
        except Exception:
            continue
        for node in tree.children:
            _find_setters_in_node(node, possible_setters, found_setters)

    return found_setters


def _find_setters_in_node(
    node: cst.CSTNode,
    possible_setters: dict[str, str],
    found_setters: dict[str, str],
) -> None:
    if isinstance(node, cst.FunctionDef):
        name = node.name.value
        if name in possible_setters and _param_count(node) == 1:
            prop = possible_setters[name]
            getter = f"get_{prop}"
            found_setters[getter] = name
    elif isinstance(node, cst.ClassDef):
        for child in node.body.body:
            _find_setters_in_node(child, possible_setters, found_setters)


def run_phase1(repo: Path, files: list[Path], dry_run: bool) -> None:
    """Phase 1: Non-conflicting parameterless methods → @property."""
    print("=" * 60)
    print("Phase 1: Non-conflicting parameterless get_/is_ → @property")
    print("=" * 60)

    # Scan for targets
    conflicting = set(ATTRIBUTE_RENAMES.keys())
    getter_targets: set[str] = set()
    for fpath in files:
        try:
            tree = _parse_file(fpath)
        except Exception:
            continue
        for node in tree.children:
            _scan_methods_in_node(node, getter_targets, conflicting)

    # Find corresponding setters
    setter_map = _determine_phase1_setter_targets(files, getter_targets)
    # Merge with explicit SETTER_PAIRS (only those whose getter is a Phase 1 target)
    for g, s in SETTER_PAIRS.items():
        if g in getter_targets:
            setter_map[g] = s

    print(f"  Getter targets: {len(getter_targets)}")
    print(f"  Setter pairs:   {len(setter_map)}")
    if getter_targets:
        sample = sorted(getter_targets)[:10]
        print(f"  Sample targets: {sample}")

    total_methods = 0
    total_setters = 0
    total_calls = 0
    files_changed = 0

    for fpath in files:
        try:
            tree = _parse_file(fpath)
        except Exception as e:
            print(f"  SKIP {fpath.relative_to(repo)}: {e}")
            continue

        transformer = Phase1Transformer(getter_targets, setter_map)
        new_tree = tree.visit(transformer)

        if transformer.methods_converted or transformer.setters_converted or transformer.calls_updated:
            files_changed += 1
            total_methods += transformer.methods_converted
            total_setters += transformer.setters_converted
            total_calls += transformer.calls_updated

            rel = fpath.relative_to(repo)
            if transformer.methods_converted:
                print(f"  {rel}: {transformer.methods_converted} getter(s) → @property")
            if transformer.setters_converted:
                print(f"  {rel}: {transformer.setters_converted} setter(s) → @X.setter")
            if transformer.calls_updated:
                print(f"  {rel}: {transformer.calls_updated} call site(s) updated")

            if not dry_run:
                fpath.write_text(new_tree.code)

    print()
    print(f"  TOTAL: {total_methods} getters, {total_setters} setters, "
          f"{total_calls} call sites across {files_changed} files")
    if dry_run:
        print("  (dry run — no files modified)")


def run_phase2(repo: Path, files: list[Path], dry_run: bool) -> None:
    """Phase 2: Attribute-conflicting methods → @property with attr rename."""
    print("=" * 60)
    print("Phase 2: Attribute-conflicting get_/is_ → @property")
    print("=" * 60)

    # Build getter targets from ATTRIBUTE_RENAMES
    getter_targets: set[str] = set()
    for attr_name in ATTRIBUTE_RENAMES:
        getter_targets.add(f"get_{attr_name}")

    # Phase 2 setter pairs (subset of SETTER_PAIRS whose getter is Phase 2)
    p2_setter_pairs = {g: s for g, s in SETTER_PAIRS.items() if g in getter_targets}

    dataclass_path = repo / DATACLASS_REL
    dataclass_resolved = dataclass_path.resolve() if dataclass_path.exists() else None

    print(f"  Attribute renames: {len(ATTRIBUTE_RENAMES)}")
    print(f"  Getter targets:    {len(getter_targets)}")
    print(f"  Setter pairs:      {len(p2_setter_pairs)}")

    total_attrs = 0
    total_methods = 0
    total_setters = 0
    total_calls = 0
    files_changed = 0

    for fpath in files:
        try:
            tree = _parse_file(fpath)
        except Exception as e:
            print(f"  SKIP {fpath.relative_to(repo)}: {e}")
            continue

        is_dc = (dataclass_resolved and fpath.resolve() == dataclass_resolved)

        # Step 1: Rename attributes
        renamer = Phase2AttrRenamer(ATTRIBUTE_RENAMES, is_dataclass_file=is_dc)
        tree = tree.visit(renamer)

        # Step 2: Convert methods and call sites
        method_xform = Phase2MethodTransformer(getter_targets, p2_setter_pairs)
        tree = tree.visit(method_xform)

        changed = (
            renamer.attrs_renamed
            + method_xform.methods_converted
            + method_xform.setters_converted
            + method_xform.calls_updated
        )
        if changed:
            files_changed += 1
            total_attrs += renamer.attrs_renamed
            total_methods += method_xform.methods_converted
            total_setters += method_xform.setters_converted
            total_calls += method_xform.calls_updated

            rel = fpath.relative_to(repo)
            parts = []
            if renamer.attrs_renamed:
                parts.append(f"{renamer.attrs_renamed} attr(s)")
            if method_xform.methods_converted:
                parts.append(f"{method_xform.methods_converted} getter(s)")
            if method_xform.setters_converted:
                parts.append(f"{method_xform.setters_converted} setter(s)")
            if method_xform.calls_updated:
                parts.append(f"{method_xform.calls_updated} call(s)")
            print(f"  {rel}: {', '.join(parts)}")

            if not dry_run:
                fpath.write_text(tree.code)

    print()
    print(f"  TOTAL: {total_attrs} attr renames, {total_methods} getters, "
          f"{total_setters} setters, {total_calls} call sites across {files_changed} files")
    if dry_run:
        print("  (dry run — no files modified)")


def run_phase3(repo: Path, files: list[Path], dry_run: bool) -> None:
    """Phase 3: Parameterized method renames (drop prefix)."""
    print("=" * 60)
    print("Phase 3: Parameterized get_/set_/is_ → drop prefix")
    print("=" * 60)

    # Collect already-converted setter names from Phase 1 & 2
    already_converted: set[str] = set()
    for g, s in SETTER_PAIRS.items():
        already_converted.add(s)
    already_converted.update(EXCLUDE_METHODS)

    # Scan for parameterized targets
    targets: set[str] = set()
    for fpath in files:
        try:
            tree = _parse_file(fpath)
        except Exception:
            continue
        scanner = Phase3Scanner(already_converted)
        tree.visit(scanner)
        targets.update(scanner.targets)

    print(f"  Targets: {len(targets)}")
    if targets:
        sample = sorted(targets)[:10]
        print(f"  Sample:  {sample}")

    total_methods = 0
    total_calls = 0
    files_changed = 0

    for fpath in files:
        try:
            tree = _parse_file(fpath)
        except Exception:
            continue

        transformer = Phase3Transformer(targets)
        new_tree = tree.visit(transformer)

        if transformer.methods_renamed or transformer.calls_updated:
            files_changed += 1
            total_methods += transformer.methods_renamed
            total_calls += transformer.calls_updated

            rel = fpath.relative_to(repo)
            parts = []
            if transformer.methods_renamed:
                parts.append(f"{transformer.methods_renamed} method(s)")
            if transformer.calls_updated:
                parts.append(f"{transformer.calls_updated} call(s)")
            print(f"  {rel}: {', '.join(parts)}")

            if not dry_run:
                fpath.write_text(new_tree.code)

    print()
    print(f"  TOTAL: {total_methods} methods, {total_calls} call sites "
          f"across {files_changed} files")
    if dry_run:
        print("  (dry run — no files modified)")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="De-Java-ify: convert get_/set_/is_ methods to Pythonic style"
    )
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3],
        required=True,
        help="Transformation phase to run",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files",
    )
    args = parser.parse_args(argv)

    repo = Path(__file__).resolve().parent.parent
    files = collect_py_files(repo)
    print(f"Scanning {len(files)} Python files in {repo}")
    print()

    if args.phase == 1:
        run_phase1(repo, files, args.dry_run)
    elif args.phase == 2:
        run_phase2(repo, files, args.dry_run)
    elif args.phase == 3:
        run_phase3(repo, files, args.dry_run)


if __name__ == "__main__":
    main()
