"""The loader builds the modifier CLASS the registry names -- for every one.

Until 2026-08-29 ``Modifier.get_instance`` chose a subclass from a hand-written
``modifier_map`` of xmlid -> class NAME and imported ``modifiers/<name.lower()>``
inside a bare try/except. Four classes live in underscored modules, so the
import failed, the except swallowed it, and the loader quietly built a generic
``Modifier`` for SELFONLY, NOKB, DOESBODY and DOESKB -- on 112 corpus
characters between them. Cost and display were unaffected (those subclasses
override neither), which is exactly why nothing caught it: the oracle cannot
see a validation method that is never called.

This test asks the one question that would have caught it: does the loader
build, for every registered modifier xmlid, the class the registry says?
"""
import xml.etree.ElementTree as ET

import pytest

import kirby_cost.objects._registry_imports  # noqa: F401
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.modifier import Modifier


def _registered_modifiers():
    return sorted(
        (x, c) for x, c in GenericObject._registry.items()
        if c is not Modifier and isinstance(c, type) and issubclass(c, Modifier)
    )


def _element(xmlid: str) -> ET.Element:
    return ET.Element(
        "MODIFIER", XMLID=xmlid, ID="1", BASECOST="0.25", LEVELS="0", ALIAS=xmlid,
        POSITION="-1", MULTIPLIER="1.0", NAME="", COMMENTS="", PRIVATE="No",
        FORCEALLOW="No",
    )


def test_there_are_registered_modifiers():
    assert len(_registered_modifiers()) > 50


@pytest.mark.parametrize("xmlid,cls", _registered_modifiers(), ids=lambda v: v if isinstance(v, str) else v.__name__)
def test_get_instance_builds_the_registered_class(xmlid, cls):
    built = Modifier.get_instance(_element(xmlid))
    assert type(built) is cls, f"{xmlid}: loader built {type(built).__name__}, registry says {cls.__name__}"


@pytest.mark.parametrize("xmlid", ["SELFONLY", "NOKB", "DOESBODY", "DOESKB"])
def test_the_four_underscored_modules_dispatch(xmlid):
    """The specific regression. Each of these lives in an underscored module
    (self_only.py, ...) and was silently generic before 2026-08-29."""
    built = Modifier.get_instance(_element(xmlid))
    assert type(built) is not Modifier
    assert built.xmlid == xmlid


def test_an_unknown_xmlid_still_falls_back_to_the_base_class():
    built = Modifier.get_instance(_element("NO_SUCH_MODIFIER_XMLID"))
    assert type(built) is Modifier
