"""A specialised template extends Main6E and overrides only what differs.

Every non-root `.hdt` declares its parent on the root element:

    <TEMPLATE version="2.0" extends="builtIn.Main6E.hdt">

Main6E declares none. So Vehicle6E, Computer6E, Automaton6E and Superheroic6E
are each a thin override layer over Main6E, and a character built on one gets
that layer's rates on top of Main6E's — which is why most of them are
indistinguishable from Main6E on most characters, and why the few overridden
entries matter enormously to the characters that use them.

The provider follows the chain by loading child first and parent after, because
indexing is first-wins; that is the same ordering already used for the
earlier-edition fallback (`Main6E.hdt` -> `Main.hdt`).

`builtIn.` is HD's marker for "one of the templates that ship with the app",
and resolves to the file of that name in the same template directory. It is not
a path.
"""
import os
from pathlib import Path

import pytest

from kirby_cost.template.hdt_provider import HDTTemplateProvider

TEMPLATE_DIR = Path(os.environ["KIRBY_COST_HDT"]).parent if os.environ.get(
    "KIRBY_COST_HDT") else None

pytestmark = pytest.mark.skipif(
    TEMPLATE_DIR is None or not (TEMPLATE_DIR / "Vehicle6E.hdt").is_file(),
    reason="HERO Designer template directory not available",
)


def test_the_parser_reports_the_parent():
    from kirby_cost.io.hdt_parser import HDTParser

    child = HDTParser().parse_file(str(TEMPLATE_DIR / "Vehicle6E.hdt"))
    root = HDTParser().parse_file(str(TEMPLATE_DIR / "Main6E.hdt"))
    assert child["extends"] == "builtIn.Main6E.hdt"
    assert root["extends"] == ""


def test_a_specialised_template_inherits_what_it_does_not_override():
    """Vehicle6E defines SIZE and a handful of others; STR comes from Main6E."""
    vehicle = HDTTemplateProvider(TEMPLATE_DIR / "Vehicle6E.hdt")

    assert vehicle.get_template_data("SIZE") is not None, "Vehicle6E's own"
    assert vehicle.get_template_data("STR") is not None, "inherited from Main6E"
    assert vehicle.get_template_data("ENERGYBLAST") is not None, "inherited"


def test_the_child_wins_where_it_overrides():
    """Vehicle6E's FLIGHT is USESEND="No"; Main6E's is "Yes"."""
    main = HDTTemplateProvider(TEMPLATE_DIR / "Main6E.hdt")
    vehicle = HDTTemplateProvider(TEMPLATE_DIR / "Vehicle6E.hdt")

    assert main.get_template_data("FLIGHT").uses_end is True
    assert vehicle.get_template_data("FLIGHT").uses_end is False


def test_automaton_overrides_a_characteristic_rate():
    """Automaton6E prices EGO at 2/level against Main6E's 1 — the GOLEM case."""
    main = HDTTemplateProvider(TEMPLATE_DIR / "Main6E.hdt")
    automaton = HDTTemplateProvider(TEMPLATE_DIR / "Automaton6E.hdt")

    assert main.get_template_data("EGO").level_cost == 1.0
    assert automaton.get_template_data("EGO").level_cost == 2.0


def test_main6e_is_unaffected_by_the_chain():
    """The root template has no parent; loading it must not change."""
    main = HDTTemplateProvider(TEMPLATE_DIR / "Main6E.hdt")

    assert main.get_template_data("SIZE") is None, "SIZE is Vehicle6E's, not Main6E's"
    assert main.get_template_data("FLIGHT").uses_end is True
