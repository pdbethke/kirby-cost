"""kirby-cost is pure code: no ORM, no web framework, no bundled data.

These are the invariants from the 2026-08-15 pure-code spec. The duplication
this spec removed survived for months precisely because nothing failed when
the layers blurred — so the boundary is asserted, not trusted.

NOTE: the bundled-data check lives in the follow-up plan; only the import
and dependency invariants are enforced here.
"""
import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# A full DB layer can be built without sqlalchemy (raw psycopg/sqlite3), and
# a full web layer without fastapi (starlette/flask/django) — the original
# list only caught sqlalchemy+fastapi, so the gate stayed green while a
# parallel DB/web stack grew back in.
FORBIDDEN = (
    "sqlalchemy", "fastapi", "requests", "httpx", "aiohttp", "urllib",
    "psycopg", "psycopg2", "sqlite3", "starlette", "flask", "django",
    "pymysql",
)


def _tracked_py_files():
    out = subprocess.run(
        ["git", "ls-files", "kirby_cost"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    return [ROOT / p for p in out if p.endswith(".py")]


def _top_level_imports(path: Path):
    """Yield the top-level module name of every import in `path`.

    Uses `ast` rather than a line-prefix scan for two reasons the old
    implementation missed:

    * Static imports (`import X`, `from X import Y`, `import X.Y as Z`) are
      parsed precisely, so a module name is matched exactly — not as a
      substring — meaning a future `requests_util.py` next to `requests`
      in FORBIDDEN can never false-positive, and `kirby_cost` itself can
      never false-positive against a `kirby` check.
    * Dynamic imports — `importlib.import_module("sqlalchemy")` and
      `__import__("sqlalchemy")` — are also caught; a line-prefix scan that
      only looks at lines starting with `import`/`from` misses both, since
      neither starts with those keywords.

    Relative imports (`from . import x`, `from .foo import x`) are skipped:
    they can only ever resolve within kirby_cost itself.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative import — `.` or `.foo`, never top-level
                continue
            if node.module:
                yield node.module.split(".")[0]
        elif isinstance(node, ast.Call):
            func = node.func
            is_dynamic_import = (
                (isinstance(func, ast.Attribute) and func.attr == "import_module")
                or (isinstance(func, ast.Name) and func.id == "__import__")
            )
            if not is_dynamic_import or not node.args:
                continue
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                yield arg.value.split(".")[0]


def test_engine_imports_no_orm_or_web_framework():
    offenders = []
    for path in _tracked_py_files():
        for mod in _top_level_imports(path):
            if mod.lower() in FORBIDDEN:
                offenders.append(f"{path.relative_to(ROOT)}: imports {mod!r}")
    assert not offenders, "kirby-cost must be pure code:\n" + "\n".join(offenders)


#: What this layer may depend on. An ALLOWLIST, deliberately.
#:
#: This test used to be a denylist named after the package it forbade. That
#: name shipped: the published 0.4.0 sdist carries 66 test files, and this
#: function's old name announced a private, unreleased package to anyone who
#: downloaded it. A reader does not need the import to exist — the name of a
#: test forbidding it is enough to infer what sits above.
#:
#: An allowlist says this layer's position positively and names nothing above
#: it. It is also strictly stronger: it catches a consumer nobody anticipated,
#: which a denylist by construction cannot.
_OWN = {"kirby_cost"}
_DECLARED = {"typing_extensions", "lxml"}   # must match pyproject `dependencies`
_ALLOWED = _OWN | _DECLARED | set(sys.stdlib_module_names)


def test_the_allowlist_is_not_vacuous():
    """Guards the guard: if `_ALLOWED` became everything, the test below could
    not fail."""
    assert "lxml" in _ALLOWED and "os" in _ALLOWED
    assert "sqlalchemy" not in _ALLOWED, "the allowlist has stopped excluding anything"


def test_the_engine_imports_only_what_sits_below_it():
    """The real defect (2026-08-15 pure-code spec) was an UPWARD dependency:
    the engine importing from something that consumes it. Duplicate table
    declarations were a symptom of that, not the invariant — so this asserts
    the direction itself.

    Relative imports are skipped: they are intra-package by definition and
    cannot point upward.
    """
    offenders = []
    for path in _tracked_py_files():
        for mod in sorted(_top_level_imports(path)):
            if mod not in _ALLOWED:
                offenders.append(f"{path.relative_to(ROOT)}: imports {mod!r}")
    assert not offenders, (
        "kirby_cost/ may import only the standard library, itself, and its "
        "declared dependencies. Anything else is a dependency on a layer at "
        "or above this one:\n" + "\n".join(offenders)
    )


def test_packaging_declares_only_pure_dependencies():
    """No ORM, web framework or driver may enter the dependency list.

    Reads pyproject.toml, which replaced setup.py on 2026-08-17. The guard is
    the point, not the filename: this test failed when setup.py was deleted,
    which is the guard working — a dependency check that silently stops
    checking is worse than none.
    """
    path = ROOT / "pyproject.toml"
    assert path.exists(), "packaging metadata missing — this guard reads it"
    text = path.read_text().lower()
    for banned in FORBIDDEN:
        assert banned not in text, f"{banned} must not be a dependency"


def test_the_declared_runtime_dependencies_are_the_expected_two():
    """Pin the whole list, so an addition is a deliberate act.

    FORBIDDEN catches what we thought to ban; this catches what we did not.
    """
    import re

    text = (ROOT / "pyproject.toml").read_text()
    block = re.search(r"^dependencies = \[(.*?)^\]", text, re.S | re.M)
    assert block, "could not find the dependencies list"
    names = re.findall(r'"([A-Za-z0-9_.-]+)', block.group(1))
    assert names == ["typing-extensions", "lxml"], names


def test_the_version_is_written_in_exactly_one_place():
    """pyproject.toml owns the number; __init__ reads it from the metadata.

    A literal in __init__.py drifted silently: it still said 0.1.0 while PyPI
    served 0.2.0 and then 0.2.1, so a consumer version-gating on
    ``kirby_cost.__version__`` was told the wrong thing by an installed wheel.
    Two places to write a number is one place too many.
    """
    import re

    text = (ROOT / "kirby_cost" / "__init__.py").read_text()
    literal = re.search(r'^__version__\s*=\s*["\']', text, re.M)
    assert not literal, (
        "__version__ is restated as a literal in kirby_cost/__init__.py — "
        "read it from importlib.metadata instead, or it will drift again"
    )

    import kirby_cost
    from importlib.metadata import version

    assert kirby_cost.__version__ == version("kirby-cost")


def test_py_typed_marker_ships():
    """The `Typing :: Typed` classifier is a promise the wheel has to keep.

    PEP 561: a type checker ignores an *installed* package's inline annotations
    unless a py.typed marker sits in the package directory. 0.2.0 and 0.2.1
    both carried the classifier and shipped no marker, so every consumer's mypy
    silently treated the engine as untyped.
    """
    assert (ROOT / "kirby_cost" / "py.typed").is_file(), "py.typed marker missing"

    text = (ROOT / "pyproject.toml").read_text()
    assert 'kirby_cost = ["py.typed"]' in text, (
        "py.typed exists but pyproject does not declare it as package-data, so "
        "include-package-data = false will leave it out of the wheel"
    )


def test_database_package_is_gone():
    assert not (ROOT / "kirby_cost" / "database").exists()


def test_builder_api_is_gone():
    assert not (ROOT / "kirby_cost" / "api").exists()
    assert not (ROOT / "frontend").exists()
