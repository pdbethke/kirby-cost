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
