"""A *GROUP sense option takes the group rate, with or without a TEMPLATE.

This file used to assert the opposite, and the story of why is worth keeping.

The claim was: Hero Designer derives its sense *groups* from the loaded
template, so a character file with no ``TEMPLATE`` attribute has none, cannot
resolve ``SMELLGROUP`` as a group, and charges the single-sense rate. It was
backed by a corpus measurement that looked decisive:

    has TEMPLATE + *GROUP option  ->  group rate   (72 of 72)
    no  TEMPLATE + *GROUP option  ->  single rate  ( 1 of  1)

and it made UNDEAD_GHOUL match. The reasoning about HD is even correct as far
as it goes — ``SenseGroup.clear()`` really does populate the group registry
during a template load.

**But the 1-of-1 was an artifact of a broken oracle.** The headless HD fork
could not resolve any ``builtIn.`` template name (fixed in
kirby-hd-oracle, 2026-08-17). Characters silently kept the Main6E
bootstrap, and Main6E itself loaded *without the parent chain that registers
the sense groups*. The oracle's "no template" reading was really "template
loaded incompletely", and a rule was written into the engine to reproduce it.

With the oracle fixed, UNDEAD_GHOUL takes the group rate like the other 72:
3 levels x 2 = 6, not 3. ``SenseAdder.sense_groups_defined`` no longer gates
the group rate.

The lesson, which cost a day: a corpus measurement is only as sound as the
oracle that produced it. 72-of-72 against 1-of-1 reads like an overwhelming
majority confirming a real exception. It was 73 readings from an instrument
with a systematic fault.
"""
import textwrap

import pytest

from kirby_cost.io.hdc_loader import HDCLoader


def _write_hdc(tmp_path, template_attr: str) -> str:
    """Minimal character with one 3-level ENHANCEDPERCEPTION on SMELLGROUP."""
    xml = textwrap.dedent(
        f"""\
        <?xml version="1.0" encoding="UTF-16"?>
        <CHARACTER version="6.0"{template_attr}>
          <CHARACTER_INFO CHARACTER_NAME="Probe" />
          <CHARACTERISTICS />
          <SKILLS />
          <PERKS />
          <TALENTS />
          <POWERS>
            <POWER XMLID="ENHANCEDPERCEPTION" ID="1" BASECOST="0.0" LEVELS="3"
                   ALIAS="Enhanced Perception" POSITION="0" MULTIPLIER="1.0"
                   OPTION="SMELLGROUP" OPTIONID="SMELLGROUP"
                   OPTION_ALIAS="Smell/Taste Group" NAME="Probe Nose">
              <NOTES />
            </POWER>
          </POWERS>
          <DISADVANTAGES />
        </CHARACTER>
        """
    )
    p = tmp_path / f"probe{'_tmpl' if template_attr else ''}.hdc"
    p.write_bytes(xml.encode("utf-16"))
    return str(p)


def _perception(hero):
    for p in hero.powers:
        if p.xmlid == "ENHANCEDPERCEPTION":
            return p
    pytest.fail("ENHANCEDPERCEPTION not loaded")


def test_group_option_without_a_template_still_costs_the_group_rate(tmp_path):
    """3 levels x 2 CP = 6. This asserted 3.0 until 2026-08-17 — see above."""
    hero = HDCLoader().load_file(_write_hdc(tmp_path, ""))
    power = _perception(hero)

    assert power.levels == 3
    assert power.total_cost == 6.0, (
        f"ENHANCEDPERCEPTION on SMELLGROUP with no template cost "
        f"{power.total_cost}; a *GROUP option charges the Sense Group rate "
        "(2 CP per level = 6.0) whether or not the file names a template."
    )


def test_group_option_with_a_template_costs_the_group_rate(tmp_path):
    """The 72 template-bearing fixtures must be unaffected: 2 CP per level."""
    hero = HDCLoader().load_file(
        _write_hdc(tmp_path, ' TEMPLATE="builtIn.Heroic6E.hdt"')
    )
    power = _perception(hero)

    assert power.levels == 3
    assert power.total_cost == 6.0, (
        f"ENHANCEDPERCEPTION on SMELLGROUP WITH a template cost "
        f"{power.total_cost}; it must still charge the Sense Group rate "
        "(2 CP per level = 6.0). Regressing this would break 72 oracle fixtures."
    )
