"""
Shared fixtures for kirby-cost tests.

Provides factory functions for building GenericObjects, Modifiers, and Adders
with specific attributes, avoiding the need to parse XML for unit tests.

Also points the suite at a template. kirby-cost ships none, so anything that
loads a character needs a ``.hdt`` from a HERO Designer installation:
``KIRBY_COST_HDT`` if the environment sets one, otherwise a developer's own
copy under ``HERODesignerSource/`` (untracked, and not part of the package).

Where neither exists — CI is the case that matters, since no Hero Games data
may ship — the tests that need one SKIP rather than fail. They are not broken
there, they are unrunnable: the licensed input they cost against is absent by
design. Failing instead would paint 44 red marks on every CI run and drown the
377 tests that do not need a template. A template that IS configured but
unreadable still fails loudly; only "none configured at all" converts to a skip.
"""

import os
from pathlib import Path

import pytest

from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.adder import Adder
from tests.corpus import GENERATED, INPUTS, missing_inputs

#: Everything the suite can be given: variables to set, plus fixtures to
#: generate. Counted together because the guard treats them alike.
_INPUT_COUNT = len(INPUTS) + len(GENERATED)


_REPO_ROOT = Path(__file__).resolve().parent.parent

#: Untracked, and the only place a maintainer's own paths are written down.
#: See .env.test.example for the shape. Loaded here rather than by a shell
#: wrapper so that a plain `pytest`, an IDE runner and CI all behave alike —
#: PyCharm does not source anyone's shell profile.
_ENV_FILE = _REPO_ROOT / ".env.test"


def _parse_env_file(text: str) -> "dict[str, str]":
    """KEY=VALUE pairs from dotenv-ish text. No dependency, no interpolation.

    Tolerates `export KEY=value`, surrounding quotes, blank lines and #
    comments, and expands a leading ~. Anything else is left exactly as
    written: these are paths, and a path is allowed to contain # or =.
    """
    found: "dict[str, str]" = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        found[key] = os.path.expanduser(value)
    return found


def _load_env_file(path: Path) -> "list[str]":
    """Apply `path`'s assignments to os.environ, without overriding it.

    An explicit variable always wins, so a one-off
    `KIRBY_COST_CORPUS=... pytest` still overrides the file.
    """
    if not path.is_file():
        return []
    applied = []
    for key, value in _parse_env_file(path.read_text()).items():
        if not os.environ.get(key):
            os.environ[key] = value
            applied.append(key)
    return applied


#: Recorded for the run header. Populated at import, before anything below
#: reads the environment.
LOADED_FROM_ENV_FILE = _load_env_file(_ENV_FILE)


_LOCAL_HDT = (
    Path(__file__).resolve().parent.parent
    / "HERODesignerSource" / "template" / "Main6E.hdt"
)

if not os.environ.get("KIRBY_COST_HDT") and _LOCAL_HDT.is_file():
    os.environ["KIRBY_COST_HDT"] = str(_LOCAL_HDT)

#: True when the suite has a template to cost against. Read once, at import,
#: so a test that clears the variable mid-run cannot turn real failures green.
TEMPLATE_CONFIGURED = bool(os.environ.get("KIRBY_COST_HDT"))

# The provider's own words when nothing is configured — matched rather than
# re-derived so this stays wrong-proof if the message is reworded loosely.
_NO_TEMPLATE = "No HERO Designer template configured"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Turn "no template configured" into a skip, at setup, call or teardown.

    A module-scoped fixture that builds a provider raises during setup, which
    pytest reports as an ERROR rather than a failure, so this hooks the report
    itself instead of any one phase.
    """
    outcome = yield
    if TEMPLATE_CONFIGURED or call.excinfo is None:
        return
    exc = call.excinfo.value
    if not isinstance(exc, FileNotFoundError) or _NO_TEMPLATE not in str(exc):
        return
    report = outcome.get_result()
    report.outcome = "skipped"
    report.longrepr = (
        str(item.path),
        item.location[1] or 0,
        "Skipped: no HERO Designer template configured (set KIRBY_COST_HDT)",
    )


# ---------------------------------------------------------------------------
# The skip guard
#
# Every skip in this suite means one thing: an input the tests need is not on
# this machine. That is correct and expected for anyone but the maintainer, and
# the suite passes without any of them.
#
# It is also, for the maintainer, indistinguishable from coverage quietly
# draining away. Two real cases, both green the whole time they were broken:
# the oracle fixtures skipped for months after the Kirby rename left their
# paths pointing at the old workspace, and the whole-character roundtrip
# skipped from the day its hardcoded path was scrubbed for publication
# (ed775fb) until 2026-08-18 — nothing ever pointed the replacement variable
# at a file.
#
# So the guard is conditional on there being nothing left to blame: when every
# input resolves — the five variables AND the generated fixtures — a skip is no
# longer "unrunnable here", it is a defect, and the run fails. Configure nothing
# and it never fires, which is every case but the maintainer's.
# ---------------------------------------------------------------------------

#: nodeid -> reason, for skips seen this session.
_SKIPPED: "dict[str, str]" = {}


def _skip_reason(report) -> str:
    """A skip's reason, whether pytest phrased it as a tuple or a string."""
    longrepr = report.longrepr
    if isinstance(longrepr, tuple) and len(longrepr) == 3:
        return str(longrepr[2]).removeprefix("Skipped: ")
    return str(longrepr) if longrepr else "no reason given"


def pytest_report_header(config):
    """Say what the run is configured with, before it says anything else."""
    lines = []
    if LOADED_FROM_ENV_FILE:
        lines.append(
            f"kirby-cost: {len(LOADED_FROM_ENV_FILE)} inputs from "
            f".env.test ({', '.join(sorted(LOADED_FROM_ENV_FILE))})"
        )
    missing = missing_inputs()
    if missing:
        lines.append(
            f"kirby-cost: {_INPUT_COUNT - len(missing)}/{_INPUT_COUNT} inputs "
            f"present; tests needing {', '.join(missing)} will skip"
        )
    else:
        lines.append(
            f"kirby-cost: all {_INPUT_COUNT} inputs present — "
            "any skip will fail the run"
        )
    return lines


def pytest_runtest_logreport(report):
    if report.skipped:
        _SKIPPED.setdefault(report.nodeid, _skip_reason(report))


def _guard_verdict() -> "tuple[bool, list[str]]":
    """(should_fail, missing_inputs). Kept pure so it can be tested directly."""
    if os.environ.get("KIRBY_COST_ALLOW_SKIPS"):
        return False, []
    missing = missing_inputs()
    return (bool(_SKIPPED) and not missing), missing


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    should_fail, _ = _guard_verdict()
    if not should_fail:
        return
    terminalreporter.section("skips with every input configured", red=True)
    terminalreporter.write_line(
        f"{len(_SKIPPED)} test(s) skipped, but all {_INPUT_COUNT} inputs in "
        "tests/corpus.py resolve. A skip here is not 'unrunnable on this "
        "machine' — it is coverage that has gone missing."
    )
    for nodeid, reason in sorted(_SKIPPED.items()):
        terminalreporter.write_line(f"  {nodeid}\n      {reason}")
    terminalreporter.write_line(
        "Set KIRBY_COST_ALLOW_SKIPS=1 to proceed anyway (deliberate skips only)."
    )


def pytest_sessionfinish(session, exitstatus):
    should_fail, _ = _guard_verdict()
    if should_fail and session.exitstatus == 0:
        session.exitstatus = 1


class ConcreteObject(GenericObject):
    """Concrete subclass of GenericObject for testing (ABC can't be instantiated)."""
    pass


class ConcreteModifier(Modifier):
    """Concrete subclass of Modifier for testing."""
    pass


class ConcreteAdder(Adder):
    """Concrete subclass of Adder for testing."""
    pass


def make_object(
    *,
    base_cost: float = 0.0,
    level_cost: float = 0.0,
    level_value: float = 0.0,
    levels: int = 0,
    xmlid: str = "TEST_OBJECT",
    minimum_cost: float = 0.0,
    max_cost: float = 0.0,
    min_set: bool = False,
    max_set: bool = False,
    types: list | None = None,
    uses_end: bool = False,
    duration: str = "",
) -> ConcreteObject:
    """Factory to build a GenericObject with given attributes."""
    obj = ConcreteObject()
    obj.base_cost = base_cost
    obj.level_cost = level_cost
    obj.level_value = level_value
    obj.levels = levels
    obj.xmlid = xmlid
    obj.minimum_cost = minimum_cost
    obj.max_cost = max_cost
    obj.min_set = min_set
    obj.max_set = max_set
    obj.types = types or []
    obj.uses_end = uses_end
    obj.duration = duration
    return obj


def make_modifier(
    *,
    base_cost: float = 0.0,
    level_cost: float = 0.0,
    level_value: float = 0.0,
    levels: int = 0,
    xmlid: str = "TEST_MODIFIER",
    minimum_cost: float = -10.0,
    max_cost: float = 10.0,
    min_set: bool = True,
    max_set: bool = True,
) -> ConcreteModifier:
    """Factory to build a Modifier with given attributes."""
    mod = ConcreteModifier()
    mod.base_cost = base_cost
    mod.level_cost = level_cost
    mod.level_value = level_value
    mod.levels = levels
    mod.xmlid = xmlid
    mod.minimum_cost = minimum_cost
    mod.max_cost = max_cost
    mod.min_set = min_set
    mod.max_set = max_set
    return mod


def make_adder(
    *,
    base_cost: float = 0.0,
    level_cost: float = 0.0,
    level_value: float = 0.0,
    levels: int = 0,
    xmlid: str = "TEST_ADDER",
    required: bool = False,
    selected: bool = True,
) -> ConcreteAdder:
    """Factory to build an Adder with given attributes."""
    adder = ConcreteAdder()
    adder.base_cost = base_cost
    adder.level_cost = level_cost
    adder.level_value = level_value
    adder.levels = levels
    adder.xmlid = xmlid
    adder._required = required
    adder._selected = selected
    return adder


@pytest.fixture
def provider():
    """The configured HDT provider, or skip. Rules validate against a real
    template, so authoring them needs one resolvable."""
    from kirby_cost.template.hdt_provider import HDTTemplateProvider
    if not os.environ.get("KIRBY_COST_HDT"):
        pytest.skip("KIRBY_COST_HDT is not set")
    return HDTTemplateProvider()
