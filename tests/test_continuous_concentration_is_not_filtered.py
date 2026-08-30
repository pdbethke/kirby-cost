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

  JOSEPH_OTANGA  TRANSFORM    INSTANT, has EXTRATIME  -> guard keeps it, -1.0
  SHADOW_COLOSSUS ENERGYBLAST INSTANT, no EXTRATIME   -> guard keeps it, -0.5

The second line used to read "Java filters on a static read, yet the oracle
records -0.5", an unexplained anomaly. It is explained: the guard reads
``getDuration()``, not the DURATION field, and this Blast carries CONTINUOUS,
so its effective duration is CONSTANT (GenericObject.java:1723-1725) and the
filter is never reached. Both assertions are kept -- the field says INSTANT,
the effective duration says CONSTANT.
"""
from tests.corpus import corpus_root
from pathlib import Path

import pytest

from kirby_cost.io.hdc_loader import HDCLoader

_ROOT = (corpus_root() or Path("/nonexistent"))
COLOSSUS = _ROOT / "villains/CV1HDFiles/CV1 HD Files ƒ/SHADOW_DESTROYER/SHADOW_COLOSSUS-CV1.hdc"
OTANGA = _ROOT / "villains/CV1HDFiles/CV1 HD Files ƒ/JOSEPH_OTANGA-CV1.hdc"


def _concentration(power):
    for m in power.assigned_modifiers:
        if m.xmlid == "CONCENTRATION":
            return m
    pytest.fail("no CONCENTRATION on this power")


def _power(hero, xmlid, name):
    for p in hero.powers:
        if p.xmlid == xmlid and p.name == name:
            return p
    pytest.fail(f"{xmlid} {name!r} not loaded")


@pytest.mark.skipif(not COLOSSUS.exists(), reason="machine-bound HDC corpus absent")
def test_continuous_concentration_still_counts_on_an_instant_power():
    """base -0.25 doubled by a +1.0 sub-modifier = -0.5, not the bare -0.25."""
    hero = HDCLoader().load_file(str(COLOSSUS))
    blast = _power(hero, "ENERGYBLAST", "Qliphothic Overload")

    assert blast.orig_duration == "INSTANT"       # the DURATION field
    assert blast.duration == "CONSTANT"           # CONTINUOUS rewrites it
    assert _concentration(blast).total_value == -0.5


@pytest.mark.skipif(not COLOSSUS.exists(), reason="machine-bound HDC corpus absent")
def test_the_blast_real_cost_matches_the_oracle():
    """195 active / (1 + 0.5 + 0.5) = 97.5, round-half-down to 97."""
    hero = HDCLoader().load_file(str(COLOSSUS))
    blast = _power(hero, "ENERGYBLAST", "Qliphothic Overload")

    assert blast.active_cost == 195
    assert blast.real_cost == 97


@pytest.mark.skipif(not OTANGA.exists(), reason="machine-bound HDC corpus absent")
def test_the_extratime_case_is_unchanged():
    """Already correct via the EXTRATIME guard — it must stay correct."""
    hero = HDCLoader().load_file(str(OTANGA))
    transform = _power(hero, "TRANSFORM", "Transform Others Into Animals")

    assert _concentration(transform).total_value == -1.0
