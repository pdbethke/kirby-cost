"""Modifier intelligence is an editing affordance; a cost engine never applies it.

``Concentration.getAssignedModifiers`` drops a CONTINUOUSCONCENTRATION
sub-modifier when the power it sits on is INSTANT — Concentration "throughout"
is meaningless on a power that resolves instantly, so HD hides the option while
you are building the power. The whole thing is gated twice over on state a
headless engine does not have (``Concentration.java:50-71``)::

    if ((HeroDesigner.getActiveHero() == null)
            || HeroDesigner.getActiveHero().isLoading()
            || !p.getDuration().equals("INSTANT")
            || EXTRATIME / REGENEXTRATIME present
            || progenitor is MINDCONTROL/MINDSCAN/MINDLINK/TELEPATHY/FORCEWALL) {
        return ret;                       // <- keep it
    }
    ... remove CONTINUOUSCONCENTRATION

and, in getAvailableModifiers, on
``HeroDesigner.getInstance().getPrefs().isModifierIntelligenceOn()`` — a user
preference for interactive editing.

The port stubbed the hero-state guard with a TODO and assumed the branch that
filters. The corpus says the opposite: across all 8 CONCENTRATION sites that
carry a nested CONTINUOUSCONCENTRATION, the oracle's value is always the
unfiltered one.

Only two of those 8 reach the filter at all — the rest are CONSTANT-duration or
name-excluded — and they are the two asserted here:

  a TRANSFORM       INSTANT, has EXTRATIME  -> guard keeps it, -1.0
  an ENERGYBLAST    INSTANT, no EXTRATIME   -> guard keeps it, -0.5

The second line used to read "Java filters on a static read, yet the oracle
records -0.5", an unexplained anomaly. It is explained: the guard reads
``getDuration()``, not the DURATION field, and this Blast carries CONTINUOUS,
so its effective duration is CONSTANT (GenericObject.java:1723-1725) and the
filter is never reached. Both assertions are kept -- the field says INSTANT,
the effective duration says CONSTANT.
"""
import pytest

from kirby_cost.io.hdc_loader import HDCLoader
from tests.own_copy import own_copy


def _mod(xmlid, mod_id, base, option=None, inner="", alias=None):
    opt = f' OPTION="{option}" OPTIONID="{option}"' if option else ""
    return (f'<MODIFIER XMLID="{xmlid}" ID="{mod_id}" BASECOST="{base}" LEVELS="0" '
            f'ALIAS="{alias or xmlid}" POSITION="-1" MULTIPLIER="1.0"{opt} '
            f'PRIVATE="No" FORCEALLOW="No">{inner}</MODIFIER>')


def _concentration(option, base, mod_id):
    """CONCENTRATION with the nested "throughout" sub-modifier."""
    throughout = _mod("CONTINUOUSCONCENTRATION", mod_id + 1, 1.0, alias="throughout")
    return _mod("CONCENTRATION", mod_id, base, option, throughout)


def _blast(*modifiers):
    return ('<POWER XMLID="ENERGYBLAST" ID="9000000000020" BASECOST="0.0" LEVELS="10" '
            'ALIAS="Energy Blast" POSITION="99" MULTIPLIER="1.0" NAME="Probe" '
            'QUANTITY="1" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes" INPUT="ED">'
            + "".join(modifiers) + "</POWER>")


def _hero_with(tmp_path, power_xml):
    """PowerLad plus one Energy Blast, named "Probe", carrying ``power_xml``."""
    return HDCLoader().load_file(
        own_copy(tmp_path, section_xml=[("POWERS", power_xml)]))


def _concentration_of(power):
    for m in power.assigned_modifiers:
        if m.xmlid == "CONCENTRATION":
            return m
    pytest.fail("no CONCENTRATION on this power")


def _power(hero, xmlid, name):
    for p in hero.powers:
        if p.xmlid == xmlid and p.name == name:
            return p
    pytest.fail(f"{xmlid} {name!r} not loaded")


@pytest.fixture
def constant_blast(tmp_path):
    """An INSTANT-duration blast that CONTINUOUS rewrites to CONSTANT."""
    hero = _hero_with(tmp_path, _blast(
        _mod("CONTINUOUS", 9000000000021, 0.5),
        _concentration("HALF", -0.25, 9000000000022)))
    return _power(hero, "ENERGYBLAST", "Probe")


def test_continuous_concentration_still_counts_on_an_instant_power(constant_blast):
    """base -0.25 doubled by a +1.0 sub-modifier = -0.5, not the bare -0.25."""
    blast = constant_blast

    assert blast.orig_duration == "INSTANT"       # the DURATION field
    assert blast.duration == "CONSTANT"           # CONTINUOUS rewrites it
    assert _concentration_of(blast).total_value == -0.5


def test_the_blast_real_cost_follows_the_unfiltered_value(constant_blast):
    """75 active / (1 + 0.5) = 50 -- the Concentration counts at -0.5, not -0.25."""
    assert constant_blast.active_cost == 75
    assert constant_blast.real_cost == 50


def test_the_extratime_case_is_unchanged(tmp_path):
    """Already correct via the EXTRATIME guard — it must stay correct."""
    hero = _hero_with(tmp_path, _blast(
        _mod("EXTRATIME", 9000000000021, -1.25, "TURN"),
        _concentration("ZERO", -0.5, 9000000000022)))
    blast = _power(hero, "ENERGYBLAST", "Probe")

    assert blast.orig_duration == "INSTANT" and blast.duration == "INSTANT"
    assert _concentration_of(blast).total_value == -1.0
