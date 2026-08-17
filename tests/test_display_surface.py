"""The display layer crashes on a real character. Four ported-wrong names.

The oracle proves the cost paths and says nothing about display: it compares
total/active/real cost, never the strings. So `damage_display` — the "3d6" a
character sheet or VTT actually renders — was never executed by anything.

Calling every zero-argument public method on every object of one loaded
character (GRAVITAR-CV1) raised 14 distinct exceptions. Twelve are these four
defects; the other two are `dialog()` on KnowledgeSkill and Language, which
raise NotImplementedError on purpose because the UI was not ported.

Each is a name that does not exist, in a branch the suite never reached:

1. ``GenericObject.sorting_value`` was missing. Java defines it on the base
   (``GenericObject.getSortingValue`` returns ``toString()``) and Sense
   overrides it; the port kept the override and dropped the base, so
   ``Sense.adder_string`` — which sorts adders by it — raised AttributeError
   on every Detect and SpatialAwareness.

2. ``Power.set_use_standard_effect()`` never existed. Java has
   ``Power.useStandardEffect()``, a method gating the field on
   ``standardEffectAllowed`` and the campaign rules; the port stored the field
   as a plain attribute and left four callers invoking a setter-shaped name
   that was never written. It broke ``damage_display`` on EnergyBlast,
   KillingAttackRanged, HandToHandAttack and Absorption.

3. ``GenericObject.adder_string`` was missing. Java defines it on the base
   (``getAdderString``, line 1185) and many subclasses override it; the port
   only wrote the overrides, so classes relying on the base — Money,
   EnvironmentalMovement — raised AttributeError from ``column2_output``.

4. ``CombatLevels.column2_output`` dereferenced a None option.

None of these is a cost path, which is exactly why 82,367 oracle-compared
values were silent on all of them.
"""
import os
from pathlib import Path

import pytest

from kirby_cost.io import HDCLoader
from tests.corpus import corpus_root

GRAVITAR = (corpus_root() or Path("/nonexistent")) / "villains/CV1HDFiles/CV1 HD Files ƒ/GRAVITAR-CV1.hdc"

pytestmark = pytest.mark.skipif(
    not os.environ.get("KIRBY_COST_HDT") or not GRAVITAR.exists(),
    reason="needs a template and the machine-bound corpus",
)


@pytest.fixture(scope="module")
def hero():
    return HDCLoader().load_file(str(GRAVITAR))


def _by_class(hero, name):
    for p in list(hero.powers) + list(hero.skills) + list(hero.talents) + list(hero.perks):
        if type(p).__name__ == name:
            return p
    pytest.skip(f"{name} not present on this character")


def test_every_object_has_a_sorting_value(hero):
    """Java puts it on GenericObject; adders are GenericObjects too."""
    for obj in list(hero.powers) + list(hero.characteristics):
        assert isinstance(obj.sorting_value, str)
        for adder in (getattr(obj, "assigned_adders", None) or []):
            assert isinstance(adder.sorting_value, str), type(adder).__name__


def test_a_sense_power_renders_its_adders(hero):
    """Sense.adder_string sorts by sorting_value and used to raise."""
    detect = _by_class(hero, "Detect")

    assert isinstance(detect.adder_string, str)
    assert isinstance(detect.column2_output, str)


def test_an_attack_power_renders_its_damage(hero):
    """damage_display is the '3d6' a sheet shows. It raised AttributeError."""
    blast = _by_class(hero, "EnergyBlast")

    assert isinstance(blast.damage_display, str)
    assert blast.damage_display.strip(), "damage display must not be empty"
    assert isinstance(blast.column2_output, str)


def test_use_standard_effect_is_gated_like_java(hero):
    """False unless the power allows it AND the flag is set."""
    blast = _by_class(hero, "EnergyBlast")

    assert blast.uses_standard_effect() is False, "not set on this character"

    blast.standard_effect_allowed = True
    blast.use_standard_effect = True
    assert blast.uses_standard_effect() is True

    blast.standard_effect_allowed = False
    assert blast.uses_standard_effect() is False, "allowed=False must veto"


def test_objects_relying_on_the_base_adder_string_render(hero):
    """Money and EnvironmentalMovement do not override it."""
    for name in ("Money", "EnvironmentalMovement"):
        obj = None
        for o in list(hero.perks) + list(hero.talents):
            if type(o).__name__ == name:
                obj = o
        if obj is None:
            continue
        assert isinstance(obj.adder_string, str)
        assert isinstance(obj.column2_output, str)


def test_no_public_zero_arg_method_raises(hero):
    """The sweep that found all of this, kept as a regression net."""
    import inspect

    allowed = {"dialog"}  # UI, deliberately NotImplementedError
    failures = []
    objs = (list(hero.characteristics) + list(hero.powers) + list(hero.skills)
            + list(hero.talents) + list(hero.perks))
    for o in objs:
        for name in dir(o):
            if name.startswith("_") or name in allowed:
                continue
            try:
                attr = getattr(o, name)
            except Exception as e:
                failures.append(f"{type(o).__name__}.{name} [attr]: {e}")
                continue
            if not callable(attr):
                continue
            try:
                sig = inspect.signature(attr)
            except (TypeError, ValueError):
                continue
            if any(p.default is p.empty
                   and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                   for p in sig.parameters.values()):
                continue
            try:
                attr()
            except NotImplementedError:
                continue
            except Exception as e:
                failures.append(f"{type(o).__name__}.{name}(): {type(e).__name__}: {e}")

    assert not failures, "public surface raised:\n  " + "\n  ".join(sorted(set(failures))[:15])
