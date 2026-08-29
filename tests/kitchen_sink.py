"""A synthetic 6E character that takes every rule no corpus character takes.

**Why this exists.** kirby-cost's rules are derived from the book, not from the
corpus -- PeterB: *"there are some obscure powers no one ever takes. but
someone will some day."* Measured 2026-08-29 against the full registry and
all 655 oracle fixtures, 24 registered 6E rules appeared in no character at
all. This module builds one character that carries all of them, so the Java
oracle can be asked what each costs and how each prints, and the answer
pinned in ``tests/fixtures/authored/KitchenSink.json`` like any other
authored character.

**Why a generator and not a committed .hdc.** The other authored characters
are real people's builds and are found through ``KIRBY_COST_AUTHORED`` rather
than redistributed. This one is nobody's build -- it is a test input -- so it
lives in the repo as the code that writes it. ``build()`` is deterministic
(fixed object IDs, no timestamps), which is what lets the oracle's per-object
JSON match it across machines. ``write()`` puts it wherever the caller likes.

Regenerate the oracle fixture with::

    venv/bin/python -c "from tests.kitchen_sink import write; print(write('/tmp/KitchenSink.hdc'))"
    (cd ../kirby-hd-oracle && ./hd6cli.sh /tmp/KitchenSink.hdc) > tests/fixtures/authored/KitchenSink.json

The characteristics block is copied from Bokor (an authored character) so the
file is a complete, valid HD document; the values are only numbers.
"""
from __future__ import annotations

from pathlib import Path

_ID = 20260829000000  # deterministic; incremented per object


def _next() -> int:
    global _ID
    _ID += 1
    return _ID


_STD = ('POSITION="{pos}" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" '
        'SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes"')
_MODSTD = 'COMMENTS="" PRIVATE="No" FORCEALLOW="No"'


def modifier(xmlid, alias, basecost, levels=0, option=None, option_alias=None, input_=None, adders=()):
    opt = f' OPTION="{option}" OPTIONID="{option}" OPTION_ALIAS="{option_alias or option}"' if option else ""
    inp = f' INPUT="{input_}"' if input_ else ""
    body = "\n".join(adders)
    return (f'<MODIFIER XMLID="{xmlid}" ID="{_next()}" BASECOST="{basecost}" LEVELS="{levels}" '
            f'ALIAS="{alias}" {_STD.format(pos=-1)}{opt}{inp} NAME="" {_MODSTD}>\n<NOTES />\n{body}\n</MODIFIER>')


def adder(xmlid, alias, basecost, levels=0):
    return (f'<ADDER XMLID="{xmlid}" ID="{_next()}" BASECOST="{basecost}" LEVELS="{levels}" '
            f'ALIAS="{alias}" {_STD.format(pos=-1)} NAME="" SHOWALIAS="Yes" PRIVATE="No" '
            f'REQUIRED="No" INCLUDEINBASE="No" DISPLAYINSTRING="Yes" GROUP="No" SELECTED="YES">\n<NOTES />\n</ADDER>')


def power(xmlid, alias, levels, pos, name="", option=None, option_alias=None, input_=None, children=(), extra=""):
    opt = f' OPTION="{option}" OPTIONID="{option}" OPTION_ALIAS="{option_alias or option}"' if option else ""
    inp = f' INPUT="{input_}"' if input_ else ""
    body = "\n".join(children)
    return (f'<POWER XMLID="{xmlid}" ID="{_next()}" BASECOST="0.0" LEVELS="{levels}" ALIAS="{alias}" '
            f'{_STD.format(pos=pos)}{opt}{inp} NAME="{name}" QUANTITY="1" AFFECTS_PRIMARY="No" '
            f'AFFECTS_TOTAL="Yes"{extra}>\n<NOTES />\n{body}\n</POWER>')


def build() -> str:
    global _ID
    _ID = 20260829000000
    powers = [
        # --- sense modifiers: a POWER whose OPTION is the sense or group ---
        power("ADJACENT", "Adjacent", 0, 0, option="SIGHTGROUP", option_alias="Sight Group"),
        power("ADJACENTFIXED", "Adjacent (Fixed Perception Point)", 0, 1, option="SIGHTGROUP", option_alias="Sight Group"),
        power("DIMENSIONALALL", "Perceive into any dimension", 0, 2, option="SIGHTGROUP", option_alias="Sight Group"),
        power("DIMENSIONALGROUP", "Perceive into a related group of dimensions", 0, 3, option="HEARINGGROUP", option_alias="Hearing Group"),
        power("RAPID", "Rapid", 1, 4, option="SIGHTGROUP", option_alias="Sight Group"),
        # --- END Reserve with its nested Recovery ---
        power("ENDURANCERESERVE", "Endurance Reserve", 40, 5, name="Reserve", children=[
            power("ENDURANCERESERVEREC", "Recovery", 6, -1)]),
        power("DIFFERINGMODIFIER", "Differing Modifiers", 5, 6, input_="Blast"),
        # --- modifier carriers, at most two unexercised modifiers each ---
        power("ENERGYBLAST", "Blast", 8, 7, name="Explosive Blast", children=[
            modifier("AOE", "Area Of Effect", "0.0", levels=8, option="RADIUS", option_alias="Radius",
                     adders=[adder("EXPLOSION", "Explosion", "-0.5")])]),
        power("ENERGYBLAST", "Blast", 8, 8, name="All Or Nothing Blast", children=[
            modifier("AVAD", "Attack Versus Alternate Defense", "0.5", option="VERYCOMMON",
                     option_alias="Very Common -> Common", adders=[adder("NND", "All Or Nothing", "-0.5")])]),
        power("ENERGYBLAST", "Blast", 8, 9, name="Deflectable Blast", children=[
            modifier("CANBEMISSILEDEFLECTED", "Can Be Deflected", "-0.25"),
            modifier("HALFRANGEMODIFIER", "Half Range Modifier", "0.25")]),
        power("FLIGHT", "Flight", 20, 10, name="Banking Flight", children=[
            modifier("TURNMODE", "Turn Mode", "-0.25")]),
        power("FLIGHT", "Flight", 10, 11, name="Timed Flight", children=[
            modifier("DELAYEDEFFECT", "Delayed Effect", "0.25", levels=1),
            modifier("TIMELIMIT", "Time Limit", "0.25", option="1TURN", option_alias="1 Turn")]),
        power("DRAIN", "Drain", 2, 12, name="Cumulative Drain", input_="STR", children=[
            modifier("CUMULATIVE", "Cumulative", "0.5", levels=1)]),
        power("AID", "Aid", 2, 13, name="Restoring Aid", input_="STR", children=[
            modifier("ONLYTOSTARTING", "Only Restores To Starting Values", "-0.5")]),
        power("TELEPATHY", "Telepathy", 4, 14, name="Private Telepathy", children=[
            modifier("NOTTHROUGHMINDLINK", "Cannot Be Used Through Mind Link", "-0.25")]),
        power("MINDCONTROL", "Mind Control", 4, 15, name="Obvious Mind Control", children=[
            modifier("VISIBLE", "Perceivable", "-0.5", option="INVISIBLEOBVIOUS",
                     option_alias="Invisible Power becomes Obvious"),
            modifier("SUBJECTTORANGEMODIFIER", "Subject To Range Modifier", "-0.25")]),
    ]
    chars = _CHARACTERISTICS
    # ONLYONAPPROPRIATETERRAIN is defined inside RUNNING in Main6E.hdt; it goes on the characteristic.
    terrain = modifier("ONLYONAPPROPRIATETERRAIN", "Only On Appropriate Terrain", "-0.5")
    chars = chars.replace("<RUNNING", "<RUNNING", 1)
    import re as _re
    chars = _re.sub(r'(<RUNNING [^>]*>\s*<NOTES />)', r'\1\n' + terrain.replace('\\', '\\\\'), chars, count=1)
    talents = (f'<TALENT XMLID="CUSTOMTALENT" ID="{_next()}" BASECOST="0.0" LEVELS="5" ALIAS="Custom Talent" '
               f'{_STD.format(pos=0)} NAME="Kitchen Sink Talent" INPUT="">\n<NOTES />\n</TALENT>')
    perks = "\n".join([
        f'<PERK XMLID="FAVOR" ID="{_next()}" BASECOST="3.0" LEVELS="0" ALIAS="Favor" {_STD.format(pos=0)} NAME="Owed by the GM">\n<NOTES />\n</PERK>',
        f'<PERK XMLID="RESOURCE_POOL" ID="{_next()}" BASECOST="0.0" LEVELS="25" ALIAS="Resource Points" {_STD.format(pos=1)} '
        f'OPTION="EQUIPMENT" OPTIONID="EQUIPMENT" OPTION_ALIAS="Equipment Points" NAME="">\n<NOTES />\n</PERK>',
    ])
    martial = "\n".join([
        f'<MANEUVER XMLID="MANEUVER" ID="{_next()}" BASECOST="4.0" LEVELS="0" ALIAS="Choke Hold" {_STD.format(pos=0)} '
        f'NAME="" CUSTOM="Yes" CATEGORY="Hand to Hand" DISPLAY="Custom Maneuver" OCV="+0" DCV="+0" DC="2" PHASE="1/2" '
        f'EFFECT="Grab One Limb, [DAMAGE]" ADDSTR="Yes" ACTIVECOST="0" DAMAGETYPE="4" MAXSTR="0" STRMULT="1" USEWEAPON="No" '
        f'WEAPONEFFECT="Grab One Limb, [DAMAGE]">\n<NOTES />\n</MANEUVER>',
        f'<RANGEDDC XMLID="RANGEDDC" ID="{_next()}" BASECOST="0.0" LEVELS="2" ALIAS="+2 Ranged Damage Class(es)" '
        f'{_STD.format(pos=1)} NAME="">\n<NOTES />\n</RANGEDDC>',
    ])
    return f"""<?xml version="1.0" encoding="UTF-16"?>
<CHARACTER version="6.0" TEMPLATE="builtIn.Superheroic6E.hdt">
<BASIC_CONFIGURATION BASE_POINTS="400" DISAD_POINTS="75" EXPERIENCE="0" RULES="Default" />
{_INFO}
<BACKGROUND />
<PERSONALITY />
<QUOTE />
<TACTICS />
<CAMPAIGN_USE />
<APPEARANCE />
<NOTES1 />
<NOTES2 />
<NOTES3 />
<NOTES4 />
<NOTES5 />
</CHARACTER_INFO>
{chars}
<SKILLS />
<PERKS>
{perks}
</PERKS>
<TALENTS>
{talents}
</TALENTS>
<MARTIALARTS>
{martial}
</MARTIALARTS>
<POWERS>
{chr(10).join(powers)}
</POWERS>
<DISADVANTAGES />
<EQUIPMENT />
</CHARACTER>
"""


def write(path: str | Path) -> Path:
    """Write the character as HD does -- UTF-16 with a BOM -- and return the path."""
    p = Path(path)
    p.write_bytes(build().encode("utf-16"))
    return p


_INFO = '<CHARACTER_INFO CHARACTER_NAME="Kitchen Sink" ALTERNATE_IDENTITIES="" PLAYER_NAME="" HEIGHT="180.0" WEIGHT="80.0" HAIR_COLOR="" EYE_COLOR="" CAMPAIGN_NAME="" GENRE="" GM="">'

_CHARACTERISTICS = '  <CHARACTERISTICS>\n    <STR XMLID="STR" ID="1674528649148" BASECOST="0.0" LEVELS="5" ALIAS="STR" POSITION="1" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </STR>\n    <DEX XMLID="DEX" ID="1674528648883" BASECOST="0.0" LEVELS="8" ALIAS="DEX" POSITION="2" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </DEX>\n    <CON XMLID="CON" ID="1674528648965" BASECOST="0.0" LEVELS="5" ALIAS="CON" POSITION="3" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </CON>\n    <INT XMLID="INT" ID="1674528648998" BASECOST="0.0" LEVELS="3" ALIAS="INT" POSITION="4" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </INT>\n    <EGO XMLID="EGO" ID="1674528648811" BASECOST="0.0" LEVELS="8" ALIAS="EGO" POSITION="5" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </EGO>\n    <PRE XMLID="PRE" ID="1674528648982" BASECOST="0.0" LEVELS="15" ALIAS="PRE" POSITION="6" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </PRE>\n    <OCV XMLID="OCV" ID="1674528649511" BASECOST="0.0" LEVELS="3" ALIAS="OCV" POSITION="7" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </OCV>\n    <DCV XMLID="DCV" ID="1674528648625" BASECOST="0.0" LEVELS="2" ALIAS="DCV" POSITION="8" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </DCV>\n    <OMCV XMLID="OMCV" ID="1674528649055" BASECOST="0.0" LEVELS="5" ALIAS="OMCV" POSITION="9" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </OMCV>\n    <DMCV XMLID="DMCV" ID="1674528648705" BASECOST="0.0" LEVELS="2" ALIAS="DMCV" POSITION="10" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </DMCV>\n    <SPD XMLID="SPD" ID="1674528649134" BASECOST="0.0" LEVELS="2" ALIAS="SPD" POSITION="11" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </SPD>\n    <PD XMLID="PD" ID="1674528648927" BASECOST="0.0" LEVELS="0" ALIAS="PD" POSITION="12" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </PD>\n    <ED XMLID="ED" ID="1674528649373" BASECOST="0.0" LEVELS="0" ALIAS="ED" POSITION="13" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </ED>\n    <REC XMLID="REC" ID="1674528649207" BASECOST="0.0" LEVELS="4" ALIAS="REC" POSITION="14" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </REC>\n    <END XMLID="END" ID="1674528649022" BASECOST="0.0" LEVELS="20" ALIAS="END" POSITION="15" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </END>\n    <BODY XMLID="BODY" ID="1674528649409" BASECOST="0.0" LEVELS="5" ALIAS="BODY" POSITION="16" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </BODY>\n    <STUN XMLID="STUN" ID="1674528649021" BASECOST="0.0" LEVELS="14" ALIAS="STUN" POSITION="17" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </STUN>\n    <RUNNING XMLID="RUNNING" ID="1674528649464" BASECOST="0.0" LEVELS="0" ALIAS="Running" POSITION="18" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </RUNNING>\n    <SWIMMING XMLID="SWIMMING" ID="1674528649027" BASECOST="0.0" LEVELS="0" ALIAS="Swimming" POSITION="19" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </SWIMMING>\n    <LEAPING XMLID="LEAPING" ID="1674528649234" BASECOST="0.0" LEVELS="0" ALIAS="Leaping" POSITION="20" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </LEAPING>\n  </CHARACTERISTICS>'
