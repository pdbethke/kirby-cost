"""Two crashes found by static analysis, neither reachable from the test suite.

Both are the same species: a name that is wrong in a branch nothing exercises,
so the code imports, the suite passes, and the defect waits. Neither is a cost
path, which is why 82,367 oracle-compared values said nothing about them.

1. ``PowerInstance`` — the Python-class fallback the module advertises in its
   own docstring ("Uses JSON behavior if available, falls back to Python class
   otherwise") had never once run. ``power_class`` is imported at module level
   and then assigned to inside ``__init__``, which makes it local for the whole
   function, so the call on the right-hand side raises UnboundLocalError before
   it can return anything.

   The 60 behaviour tests all register a JSON behaviour first, so
   ``behavior(xmlid)`` is never None for them and the fallback branch is never
   entered. Constructing a PowerInstance for any xmlid WITHOUT a JSON behaviour
   — the case the fallback exists for — crashes.

2. ``SenseGroup.set_sense_adders`` assigns ``self._sense_adders_has_hero =
   has_hero``, and ``has_hero`` is never defined in that method. Only ``hero``
   is. It raises NameError whenever ``sense_id is None``, which is the
   method's own default argument.

   It has no callers anywhere in the package or the tests, which is the only
   reason it has never been hit.

3. ``HDCParser.create_hero_from_file`` called the ``active_hero`` GETTER with an
   argument instead of ``set_active_hero``, raising TypeError. ``HDCParser`` is
   exported from the package root, so this is public API that has never worked
   — it is used by nothing inside the package (``HDCLoader`` is the path
   everything actually takes) and sits at 5% coverage.
"""
import pytest

from kirby_cost.behaviors.power_instance import PowerInstance
from kirby_cost.core.context import EngineContext
from kirby_cost.objects.powers.sense_group import SenseGroup


def test_power_instance_falls_back_to_the_python_class():
    """An xmlid with no JSON behaviour must still construct."""
    pi = PowerInstance("ENERGYBLAST", {"levels": 4})

    assert pi.xmlid == "ENERGYBLAST"


def test_sense_group_caches_whether_it_saw_a_hero():
    """sense_id=None is the default, and it took the NameError branch."""
    group = SenseGroup()

    result = group.set_sense_adders(None)

    assert isinstance(result, list)
    # No hero attached, so the cached flag records exactly that.
    assert group._sense_adders_has_hero is False


def test_sense_group_records_a_hero_when_one_is_attached():
    """The flag is not hardcoded — it follows the hero."""
    group = SenseGroup()

    class _Hero:
        powers: list = []
        equipment: list = []

    group._loaded_hero = _Hero()
    group.set_sense_adders(None)

    assert group._sense_adders_has_hero is True


def test_hdc_parser_can_build_a_hero(tmp_path):
    """Exported public API: it must at least not raise."""
    import textwrap
    from kirby_cost.io.hdc_parser import HDCParser

    xml = textwrap.dedent("""\
        <?xml version="1.0" encoding="UTF-16"?>
        <CHARACTER version="6.0" TEMPLATE="builtIn.Superheroic6E.hdt">
          <CHARACTER_INFO CHARACTER_NAME="Probe" />
          <CHARACTERISTICS>
            <STR XMLID="STR" ID="1" BASECOST="0.0" LEVELS="10" ALIAS="STR"
                 POSITION="0" MULTIPLIER="1.0" />
          </CHARACTERISTICS>
          <SKILLS /><PERKS /><TALENTS /><POWERS /><DISADVANTAGES />
        </CHARACTER>
        """)
    p = tmp_path / "probe.hdc"
    p.write_bytes(xml.encode("utf-16"))

    hero = HDCParser().create_hero_from_file(str(p))

    assert hero is not None
    assert EngineContext.active_hero() is hero
