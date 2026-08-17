"""kirby-cost is pure code: no ORM, no web framework, no bundled data.

These are the invariants from the 2026-08-15 pure-code spec. The duplication
this spec removed survived for months precisely because nothing failed when
the layers blurred — so the boundary is asserted, not trusted.

NOTE: the bundled-data check lives in the follow-up plan; only the import
and dependency invariants are enforced here.
"""
import ast
import subprocess
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


def test_engine_never_imports_kirby_api():
    """The real defect (2026-08-15 pure-code spec) was an upward
    dependency: the engine (kirby-cost) importing from its own consumer
    (a consumer's own package). Duplicate table declarations were a
    *symptom* of that upward dependency, not the invariant itself — so
    assert the root cause directly, not just its side effect.

    `mod == "kirby"` is an exact top-level-component match (see
    `_top_level_imports`), so `import kirby_cost...` — kirby-cost's own
    package — can never trip this.
    """
    offenders = []
    for path in _tracked_py_files():
        for mod in _top_level_imports(path):
            if mod == "kirby":
                offenders.append(f"{path.relative_to(ROOT)}: imports kirby.* (a consumer package)")
    assert not offenders, (
        "kirby_cost/ must never import kirby.* — that is the "
        "upward dependency this gate exists to prevent:\n" + "\n".join(offenders)
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


def test_database_package_is_gone():
    assert not (ROOT / "kirby_cost" / "database").exists()


def test_builder_api_is_gone():
    assert not (ROOT / "kirby_cost" / "api").exists()
    assert not (ROOT / "frontend").exists()
