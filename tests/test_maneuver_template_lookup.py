"""A maneuver is identified by its DISPLAY, not by an xmlid.

The 53 ``<MANEUVER>`` elements in ``Main6E.hdt`` carry no ``XMLID`` attribute at
all — ``DISPLAY="Killing Strike"`` is the whole of their identity, and every
HDC maneuver element is written ``<MANEUVER XMLID="MANEUVER" DISPLAY="...">``.
Indexing them by xmlid therefore files all 53 under the single key ``MANEUVER``
and the first one (Basic Strike) wins, so asking the provider what Killing
Strike costs answers 3 instead of 4.

Java resolves them by display (``Hero.java:2706-2731``)::

    String display = XMLUtility.getValue(sk, "DISPLAY");
    for (GenericObject o : template.getMartialArts()) {
        if (o instanceof Maneuver) {
            if (o.getDisplay().equals(display)) { ... }
        } else if (o instanceof com.hero.objects.List) {
            for (GenericObject o2 : li.getObjects())
                if (o2.getDisplay().equals(display)) { ... }
        }
    }
    // if we get here, then it's a custom maneuver...

— searching maneuvers nested inside a ``LIST`` container as well as top-level
ones, and falling through to a custom maneuver built from the HDC element alone
when nothing matches.
"""
import pytest

from kirby_cost.template.hdt_provider import HDTTemplateProvider


@pytest.fixture(scope="module")
def provider() -> HDTTemplateProvider:
    return HDTTemplateProvider()


def test_a_maneuver_resolves_by_its_own_display(provider):
    killing = provider.get_maneuver("Killing Strike")

    assert killing is not None
    assert killing.base_cost == 4.0


def test_maneuvers_do_not_collapse_onto_the_first(provider):
    basic = provider.get_maneuver("Basic Strike")
    killing = provider.get_maneuver("Killing Strike")

    assert basic.base_cost == 3.0
    assert killing.base_cost != basic.base_cost


def test_every_template_maneuver_is_reachable(provider):
    # Main6E.hdt states 53 <MANEUVER> elements; each must have its own entry.
    assert len(provider.get_maneuver_map()) == 53


def test_an_unknown_display_is_a_custom_maneuver(provider):
    # Java builds `new Maneuver(sk)` from the HDC element when no template
    # maneuver matches, so the provider must report "not mine" rather than
    # hand back a default.
    assert provider.get_maneuver("Spinning Dragon Fist of Nothing") is None


def test_a_maneuver_carries_the_attributes_of_its_own_element(provider):
    # Killing Strike is KILLING="Yes" and OCV -2; Basic Strike is neither.
    killing = provider.get_maneuver("Killing Strike")

    assert killing.attributes.get("KILLING") == "Yes"
    assert killing.attributes.get("OCV") == "-2"
