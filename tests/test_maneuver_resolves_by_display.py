"""The loader resolves a maneuver's template by DISPLAY, not by its xmlid.

Every HDC maneuver is written ``<MANEUVER XMLID="MANEUVER" DISPLAY="...">``, so
looking its template up by xmlid hands back whichever ``<MANEUVER>`` the
template states first — Basic Strike. Java matches on display instead
(``Hero.java:2706-2731``).

The corpus does not catch this: all 308 maneuver elements across the 794 HDC
files carry an explicit ``BASECOST``, which wins over any template default, so
every maneuver costs correctly while wearing Basic Strike's other defaults.
What leaks is the rest of the element — Martial Dodge is ``TARGET="SELFONLY"``
and loads as Basic Strike's ``DCV`` — and the cost of any maneuver whose HDC
element omits BASECOST.
"""
import textwrap

import pytest

from kirby_cost.io.hdc_loader import HDCLoader


def _write_hdc(tmp_path, maneuvers: str, name: str = "probe") -> str:
    xml = textwrap.dedent(
        f"""\
        <?xml version="1.0" encoding="UTF-16"?>
        <CHARACTER version="6.0" TEMPLATE="builtIn.Superheroic6E.hdt">
          <CHARACTER_INFO CHARACTER_NAME="Probe" />
          <CHARACTERISTICS />
          <SKILLS />
          <PERKS />
          <TALENTS />
          <MARTIALARTS>
        {maneuvers}
          </MARTIALARTS>
          <POWERS />
          <DISADVANTAGES />
        </CHARACTER>
        """
    )
    p = tmp_path / f"{name}.hdc"
    p.write_bytes(xml.encode("utf-16"))
    return str(p)


def _only_maneuver(hero):
    assert len(hero.martial_arts) == 1, f"expected one maneuver, got {hero.martial_arts}"
    return hero.martial_arts[0]


def test_a_maneuver_wears_its_own_target_not_basic_strikes(tmp_path):
    """Martial Dodge is TARGET="SELFONLY"; Basic Strike is TARGET="DCV"."""
    hdc = _write_hdc(tmp_path, textwrap.indent(
        '<MANEUVER XMLID="MANEUVER" ID="1" BASECOST="4.0" LEVELS="0" '
        'ALIAS="Martial Dodge" POSITION="0" DISPLAY="Martial Dodge" '
        'OCV="--" DCV="+5" PHASE="1/2" EFFECT="Dodge, Affects All Attacks, Abort" '
        'ADDSTR="No" ACTIVECOST="0" DAMAGETYPE="0" MAXSTR="0" STRMULT="1" '
        'USEWEAPON="No" WEAPONEFFECT="[NORMALDC] Strike" />', "    "))

    dodge = _only_maneuver(HDCLoader().load_file(hdc))

    assert dodge.display == "Martial Dodge"
    assert dodge.target == "SELFONLY"


def test_a_maneuver_without_an_explicit_basecost_costs_its_own(tmp_path):
    """No BASECOST on the element => the template's, and Killing Strike is 4."""
    hdc = _write_hdc(tmp_path, textwrap.indent(
        '<MANEUVER XMLID="MANEUVER" ID="1" LEVELS="0" ALIAS="Killing Strike" '
        'POSITION="0" DISPLAY="Killing Strike" OCV="-2" DCV="+0" PHASE="1/2" '
        'EFFECT="[KILLINGDC]" ADDSTR="Yes" ACTIVECOST="0" DAMAGETYPE="0" '
        'MAXSTR="20" STRMULT="1" USEWEAPON="No" '
        'WEAPONEFFECT="[WEAPONKILLINGDC]" />', "    "))

    killing = _only_maneuver(HDCLoader().load_file(hdc))

    assert killing.total_cost == 4.0, (
        f"Killing Strike cost {killing.total_cost}; the template states 4 and "
        "Basic Strike's 3 is what an xmlid lookup would give."
    )


def test_a_custom_maneuver_keeps_the_cost_it_states(tmp_path):
    """No template maneuver matches => Java builds it from the element alone."""
    hdc = _write_hdc(tmp_path, textwrap.indent(
        '<MANEUVER XMLID="MANEUVER" ID="1" BASECOST="7.0" LEVELS="0" '
        'ALIAS="Custom Maneuver" POSITION="0" DISPLAY="Spinning Dragon Fist" '
        'OCV="+1" DCV="+1" PHASE="1/2" EFFECT="Weird" ADDSTR="Yes" '
        'ACTIVECOST="0" DAMAGETYPE="0" MAXSTR="0" STRMULT="1" '
        'USEWEAPON="No" WEAPONEFFECT="[NORMALDC] Strike" />', "    "))

    custom = _only_maneuver(HDCLoader().load_file(hdc))

    assert custom.total_cost == 7.0
