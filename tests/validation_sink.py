"""A synthetic 6E character that exercises every ``included()`` override.

**Why this exists.** kirby-hd-oracle's ``--included`` mode (Task 1) asks the
licensed Java engine what each object's ``included(GenericObject)`` override
would say about it -- allowed, or blocked with a message. 81 modifier classes
in ``com.hero.objects.modifiers`` override that method; the survey at
``kirby/docs/superpowers/notes/2026-08-30-included-overrides-state-survey.md``
walked all 81 and, for each, named the character states that would exercise
every branch it reads. This module builds ONE character carrying those
states, so the oracle can be run against it and its verdicts pinned as a
fixture, the way any other authored character's costs are pinned.

**Coverage is checked against the engine, not the survey.** The Java source
is licensed and private; kirby-cost's ``Modifier`` subclasses are the public
mirror kirby-cost ships. ``tests/test_validation_sink.py`` walks
``Modifier.__subclasses__()`` recursively for every class that defines its
own ``included``, and asserts every one of those names is claimed by at
least one ``State`` here. The two enumerations are NOT the same list: the
engine has 78 (three Java classes -- ``AVLD``, ``BasedOnECV``,
``RequiredHands`` and others that are 5E-only or that HD folds into a
sibling modifier's OPTION rather than a separate class -- were never
ported), and the engine independently overrides ``included`` on a handful of
classes the survey never covered (``Concentration``, ``DelayedEffect``,
``Focus``, ``Gestures``, ``Incantations``, ``OnlyOnAppropriateTerrain``,
``RequiresSkillRoll``, ``Restrainable``, ``SideEffects``, ``UsableOnOthers``,
``VariableAdvantage``, ``VariableEffect``, ``VariableLimitations``) because
their Python port added a trivial pass-through override where Java had
none. Every ``State.overrides`` entry below is a real engine class name,
checked with ``_engine_overrides()``'s own definition -- not a Java name
copied without verification. A few survey names could not be authored at
all; see the module-level ``NOT_AUTHORED`` note near the bottom of this
docstring's companion report for why.

**Why a generator and not a committed .hdc.** Same reasoning as
``tests/kitchen_sink.py``: this is nobody's real build, so it lives as code
that writes it rather than a redistributed file. ``build()`` is
deterministic -- fixed object IDs, no timestamps -- entirely because every
call that consumes an ID happens exactly once, at import time, building
static strings; ``build()`` itself does no further ID allocation, so calling
it any number of times in one process reproduces the same document.

Regenerate the oracle fixture with::

    venv/bin/python -c "from tests.validation_sink import write; print(write('/tmp/ValidationSink.hdc'))"
    (cd ../kirby-hd-oracle && ./hd6cli.sh /tmp/ValidationSink.hdc) > /tmp/vs-cost.json
    (cd ../kirby-hd-oracle && ./hd6cli.sh --included /tmp/ValidationSink.hdc) > tests/fixtures/authored/ValidationSink.included.json

The characteristics block, and the ``_STD``/``_MODSTD``/``modifier``/
``adder``/``power``/``write`` writers, are copied from ``kitchen_sink.py``
rather than imported -- the two sinks are independent documents, and
``kitchen_sink``'s ``_ID`` counter is module-global state that a shared
import would corrupt.
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

_ID = 20260830000000  # deterministic; incremented per object; distinct range from kitchen_sink's


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


def modifier_linked(alias, basecost, linked_id):
    """LINKED does not use OPTION/INPUT -- it carries a LINKED_ID attribute pointing at
    the ID of the power it is linked to. Confirmed against an authored PowerLad.hdc,
    which is how the brief's original ``option="FLIGHT" input_="Blast AOE"`` sketch
    was found to be wrong and corrected here."""
    return (f'<MODIFIER XMLID="LINKED" ID="{_next()}" BASECOST="{basecost}" LEVELS="0" '
            f'ALIAS="{alias}" {_STD.format(pos=-1)} NAME="" {_MODSTD} LINKED_ID="{linked_id}">\n<NOTES />\n</MODIFIER>')


def adder(xmlid, alias, basecost, levels=0):
    return (f'<ADDER XMLID="{xmlid}" ID="{_next()}" BASECOST="{basecost}" LEVELS="{levels}" '
            f'ALIAS="{alias}" {_STD.format(pos=-1)} NAME="" SHOWALIAS="Yes" PRIVATE="No" '
            f'REQUIRED="No" INCLUDEINBASE="No" DISPLAYINSTRING="Yes" GROUP="No" SELECTED="YES">\n<NOTES />\n</ADDER>')


def power(xmlid, alias, levels, pos, name="", option=None, option_alias=None, input_=None, children=(), extra="",
          id_=None):
    obj_id = id_ if id_ is not None else _next()
    opt = f' OPTION="{option}" OPTIONID="{option}" OPTION_ALIAS="{option_alias or option}"' if option else ""
    inp = f' INPUT="{input_}"' if input_ else ""
    body = "\n".join(children)
    return (f'<POWER XMLID="{xmlid}" ID="{obj_id}" BASECOST="0.0" LEVELS="{levels}" ALIAS="{alias}" '
            f'{_STD.format(pos=pos)}{opt}{inp} NAME="{name}" QUANTITY="1" AFFECTS_PRIMARY="No" '
            f'AFFECTS_TOTAL="Yes"{extra}>\n<NOTES />\n{body}\n</POWER>')


def _slot(xmlid, alias, levels, pos, parent_id, name="", children=(), extra=""):
    """A framework slot: a POWER sibling of the MULTIPOWER/ELEMENTALCONTROL/VPP element,
    carrying PARENTID + ULTRA_SLOT="Yes" -- the shape every authored .hdc uses (see Bokor's
    Multipower). Not registered with power()'s own ID counter offset trick; slots always get
    a fresh _next() id since nothing else needs to reference them."""
    body = "\n".join(children)
    return (f'<POWER XMLID="{xmlid}" ID="{_next()}" BASECOST="0.0" LEVELS="{levels}" ALIAS="{alias}" '
            f'{_STD.format(pos=pos)} NAME="{name}" QUANTITY="1" AFFECTS_PRIMARY="No" AFFECTS_TOTAL="Yes" '
            f'PARENTID="{parent_id}" ULTRA_SLOT="Yes"{extra}>\n<NOTES />\n{body}\n</POWER>')


def framework(tag, alias, name, pos, common, slots, extra=""):
    """A Multipower/Elemental Control/VPP: its own element (XMLID="GENERIC_OBJECT" per every
    authored framework in KIRBY_COST_AUTHORED; the loader dispatches on the TAG, not this
    attribute -- hdc_loader.py overwrites .xmlid to match the tag once loaded) holding its
    common MODIFIER children, reusing the framework's own generated ID as every slot's
    PARENTID. ``slots`` is a list of already-built slot XML strings from ``_slot()``."""
    fw_id = _next()
    common_xml = "\n".join(common)
    slot_xml = "\n".join(s(fw_id) for s in slots)
    fw = (f'<{tag} XMLID="GENERIC_OBJECT" ID="{fw_id}" BASECOST="0.0" LEVELS="0" ALIAS="{alias}" '
          f'{_STD.format(pos=pos)} NAME="{name}" QUANTITY="1"{extra}>\n<NOTES />\n{common_xml}\n</{tag}>')
    return fw + "\n" + slot_xml


class State(NamedTuple):
    name: str                   # unique; becomes the object's NAME attribute
    overrides: tuple[str, ...]  # engine Modifier subclasses this state exercises
    xml: str                    # the element(s) this state contributes


def _s(name, overrides, xml):
    return State(name, tuple(overrides), xml)


# The "Linked Flight" state below links to this power's ID -- reserved before STATES so the
# power that owns it (Blast NND) can be built with an explicit id_= and Linked Flight can
# reference the same integer via LINKED_ID.
_LINK_TARGET_ID = _next()

STATES = (
    # --- attack-shape states: does_damage / does_body / does_kb / defense ---
    # AVAD is exercised for free here too: the object is ATTACK-typed (ENERGYBLAST), which
    # is AVAD.included()'s success branch, and the object also carries an NND adder under
    # AVAD -- exercising ArmorPiercing's "assigned:NND" read at the same time.
    _s("Blast NND", ("ArmorPiercing", "DoesBODY", "Penetrating", "DoesKB", "NoKB", "DoubleKB", "Cumulative", "AVAD"),
       power("ENERGYBLAST", "Blast", 8, 0, name="Blast NND", id_=_LINK_TARGET_ID, children=[
           modifier("AVAD", "Attack Versus Alternate Defense", "0.5", option="VERYCOMMON",
                    option_alias="Very Common -> Common", adders=[adder("NND", "All Or Nothing", "-0.5")])])),
    _s("Blast STUN Only", ("DoesBODY", "DoesKB", "NoKB"),
       power("ENERGYBLAST", "Blast", 8, 1, name="Blast STUN Only", children=[
           modifier("STUNONLY", "STUN Only", "0.0")])),
    _s("Blast Penetrating", ("ArmorPiercing",),
       power("ENERGYBLAST", "Blast", 8, 2, name="Blast Penetrating", children=[
           modifier("PENETRATING", "Penetrating", "0.5", levels=1)])),
    # --- END states: end_usage as a function of Charges / Costs END / Reduced END ---
    _s("Flight Charges", ("CostsEND", "IncreasedEND", "ReducedEND", "CostsENDOnlyToActivate", "Persistent", "Inherent"),
       power("FLIGHT", "Flight", 10, 3, name="Flight Charges", children=[
           modifier("CHARGES", "Charges", "-0.25", option="EIGHT", option_alias="8")])),
    _s("Force Field Costs END", ("CostsENDToMaintain", "Persistent", "Nonpersistent", "ReducedEND"),
       power("FORCEFIELD", "Resistant Protection", 6, 4, name="Force Field Costs END", input_="PD", children=[
           modifier("COSTSEND", "Costs Endurance", "-0.5", option="EVERYPHASE", option_alias="Costs END Every Phase")])),
    # DoubleEnduranceCost NOT authored: kirby-cost has no such override class (grep -rli
    # "doubleend" kirby_cost/objects/modifiers/*.py finds nothing). HD's actual "Double
    # Endurance Cost" is the INCREASEDEND modifier's own "2X" OPTION (Main6E.hdt:17112),
    # not a distinct modifier/class -- so there is no separate included() to exercise.
    _s("Flight Reduced END", ("ReducedEND", "IncreasedEND"),
       power("FLIGHT", "Flight", 10, 5, name="Flight Reduced END", children=[
           modifier("REDUCEDEND", "Reduced Endurance", "0.25", option="HALFEND", option_alias="1/2 END")])),
    # --- duration states: duration rewritten by CONTINUOUS / PERSISTENT / UNCONTROLLED ---
    _s("Blast Continuous", ("Continuous", "Concentration", "Persistent", "Uncontrolled", "Instant", "TimeLimit", "CostsENDToMaintain"),
       power("ENERGYBLAST", "Blast", 8, 6, name="Blast Continuous", children=[
           modifier("CONTINUOUS", "Continuous", "1.0")])),
    _s("Force Field Persistent", ("Persistent", "Nonpersistent", "AlwaysOn", "Inherent", "DifficultToDispel"),
       power("FORCEFIELD", "Resistant Protection", 6, 7, name="Force Field Persistent", input_="PD", children=[
           modifier("PERSISTENT", "Persistent", "0.25")])),
    # --- range states: range_value as a function of LOS / NORANGE / RANGED ---
    # NormalRange added here (types=(MENTAL,)): once LOS drives range_value to -1, this
    # power is exactly the Line Of Sight power NormalRange's success branch needs.
    _s("Telepathy LOS", ("NoRangeModifier", "HalfRangeModifier", "Ranged", "LineOfSight", "Megascale", "Indirect", "NormalRange"),
       power("TELEPATHY", "Telepathy", 4, 8, name="Telepathy LOS", children=[
           modifier("LOS", "Line Of Sight", "0.5"),
           modifier("NORMALRANGE", "Normal Range", "-0.25")])),
    _s("Blast No Range", ("NoRange", "Ranged", "NoRangeModifier", "HalfRangeModifier", "AreaEffect"),
       power("ENERGYBLAST", "Blast", 8, 9, name="Blast No Range", children=[
           modifier("NORANGE", "No Range", "-0.5")])),
    _s("HKA Ranged", ("Ranged", "NoRange", "Indirect"),
       power("HKA", "Killing Attack - Hand-To-Hand", 1, 10, name="HKA Ranged", input_="ED", children=[
           modifier("RANGED", "Ranged", "0.5")])),
    # --- area states (Mobile piggybacks: AOE already drives this power's target to HEX) ---
    _s("Blast AOE", ("AreaEffect", "Explosion", "Transdimensional", "Indirect", "HoleInTheMiddle", "Mobile"),
       power("ENERGYBLAST", "Blast", 8, 11, name="Blast AOE", children=[
           modifier("AOE", "Area Of Effect", "0.5", levels=8, option="RADIUS", option_alias="Radius"),
           modifier("MOBILE", "Mobile", "0.5")])),
    # --- perceivability ---
    # OPTIONID is INOBVIOUSINVISIBLEONE, not INOBVIOUSONE -- the template's real option list
    # (KIRBY_COST_HDT ... get_template_data("INVISIBLE", section="modifiers").options) is
    # ['OBVIOUSINOBVIOUSONE', 'OBVIOUSINOBVIOUSTWO', 'OBVIOUSINVISIBLEONE',
    # 'OBVIOUSINVISIBLETWO', 'OBVIOUSINVISIBLE', 'INOBVIOUSINVISIBLEONE',
    # 'INOBVIOUSINVISIBLETWO', 'INOBVIOUSINVISIBLE']; the brief's sketch had no match.
    _s("Blast Invisible", ("Invisible", "Visible"),
       power("ENERGYBLAST", "Blast", 8, 12, name="Blast Invisible", children=[
           modifier("INVISIBLE", "Invisible Power Effects", "0.25", option="INOBVIOUSINVISIBLEONE",
                    option_alias="Inobvious, Invisible to One Sense Group")])),
    # --- hero-level states: the six overrides that read the active hero ---
    _s("Desolidification", ("AffectsPhysicalWorld",),
       power("DESOLIDIFICATION", "Desolidification", 0, 13, name="Desolidification")),
    _s("Blast Affects Physical World", ("AffectsPhysicalWorld",),
       power("ENERGYBLAST", "Blast", 8, 14, name="Blast Affects Physical World", children=[
           modifier("AFFECTSPHYSICALWORLD", "Affects Physical World", "2.0")])),
    # ENDReserveOrEND and DoubleEnduranceCost NOT authored on this state either -- same
    # reason as Flight Reduced END above; ENDReserveOrEND has no engine class at all
    # (grep -rli "reserveorend" kirby_cost/objects/modifiers/*.py finds nothing).
    _s("END Reserve", ("ReducedEND",),
       power("ENDURANCERESERVE", "Endurance Reserve", 40, 15, name="END Reserve", children=[
           power("ENDURANCERESERVEREC", "Recovery", 6, -1)])),
    _s("Mind Link", ("NotThroughMindLink",),
       power("MINDLINK", "Mind Link", 0, 16, name="Mind Link", option="ONE", option_alias="One Specific Mind")),
    _s("Telepathy Not Through Mind Link", ("NotThroughMindLink",),
       power("TELEPATHY", "Telepathy", 4, 17, name="Telepathy Not Through Mind Link", children=[
           modifier("NOTTHROUGHMINDLINK", "Cannot Be Used Through Mind Link", "-0.25")])),
    # Linked uses LINKED_ID (an authored-power ID), not OPTION/INPUT -- see modifier_linked().
    _s("Linked Flight", ("Linked",),
       power("FLIGHT", "Flight", 10, 18, name="Linked Flight", children=[
           modifier_linked("Linked", "-0.5", linked_id=_LINK_TARGET_ID)])),
    # --- frameworks: one of each, two slots each -- one accepting the common modifier, one
    # refusing a locally-attached one (AOE on a SELFONLY-target FORCEFIELD slot). Multipower's
    # third slot is a CompoundPower with two nested constituent powers (Bokor's shape),
    # exercising the compound-power walk Task 1 ported. FOCUS is the Multipower/EC common
    # modifier (every slot accepts a framework-level Focus); VPP's is RequiresASkillRoll,
    # matching how VPPs use it in the corpus (see Ravel.hdc).
    # NND is the framework's SECOND common modifier, deliberately: it is allowed on the Blast
    # slot (target DCV, defense NORMAL) and REFUSED on the Force Field slot (target SELFONLY)
    # -- this is what actually produces a refused row in the oracle's "framework" tier.
    # (AOE, attached locally to the Force Field slot below, does NOT produce a refused row:
    # AreaEffect.included()'s target check special-cases "AOE already assigned" as satisfying
    # itself, so a self-check of an already-attached AOE always passes -- confirmed by running
    # the oracle and finding it allowed. That local AOE is kept anyway; it is what makes the
    # Force Field's own target HEX-eligible for Mobile et al. elsewhere, and drives the state's
    # own AreaEffect override coverage.)
    _s("Multipower", ("Modifier", "HalfRangeModifier", "OnlyToActivate", "Visible", "Focus", "NND"),
       framework("MULTIPOWER", "Multipower", "Multipower", 19,
                 common=[modifier("FOCUS", "Focus", "-1.0", option="OAF", option_alias="OAF"),
                         modifier("NND", "No Normal Defense", "1.0", option="STANDARD", option_alias="Standard")],
                 slots=[
                     lambda pid: _slot("ENERGYBLAST", "Blast", 8, 0, pid, name="MP Blast Slot"),
                     lambda pid: _slot("FORCEFIELD", "Resistant Protection", 6, 1, pid,
                                       name="MP Force Field Slot",
                                       children=[modifier("AOE", "Area Of Effect", "0.5", levels=4,
                                                          option="RADIUS", option_alias="Radius")]),
                     lambda pid: (
                         f'<POWER XMLID="COMPOUNDPOWER" ID="{_next()}" BASECOST="0.0" LEVELS="0" '
                         f'ALIAS="Compound Power" {_STD.format(pos=2)} NAME="MP Compound Power Slot" '
                         f'QUANTITY="1" AFFECTS_PRIMARY="No" AFFECTS_TOTAL="Yes" PARENTID="{pid}" '
                         f'ULTRA_SLOT="Yes">\n<NOTES />\n'
                         + _slot("LIFESUPPORT", "Life Support", 0, 0, pid, name="")
                         + "\n"
                         + _slot("DOESNOTBLEED", "Does Not Bleed", 0, 1, pid, name="")
                         + '\n</POWER>'
                     ),
                 ])),
    _s("Elemental Control", ("Modifier", "HalfRangeModifier"),
       framework("ELEMENTALCONTROL", "Elemental Control", "Elemental Control", 20,
                 common=[modifier("FOCUS", "Focus", "-1.0", option="OAF", option_alias="OAF")],
                 slots=[
                     lambda pid: _slot("ENERGYBLAST", "Blast", 8, 0, pid, name="EC Blast Slot"),
                     lambda pid: _slot("FORCEFIELD", "Resistant Protection", 6, 1, pid,
                                       name="EC Force Field Slot",
                                       children=[modifier("AOE", "Area Of Effect", "0.5", levels=4,
                                                          option="RADIUS", option_alias="Radius")]),
                 ])),
    _s("VPP", ("Modifier", "RequiresSkillRoll"),
       framework("VPP", "Variable Power Pool", "VPP", 21,
                 common=[modifier("REQUIRESASKILLROLL", "Requires A Roll", "-0.5", option="11", option_alias="11-")],
                 slots=[
                     lambda pid: _slot("ENERGYBLAST", "Blast", 8, 0, pid, name="VPP Blast Slot"),
                     lambda pid: _slot("FORCEFIELD", "Resistant Protection", 6, 1, pid,
                                       name="VPP Force Field Slot",
                                       children=[modifier("AOE", "Area Of Effect", "0.5", levels=4,
                                                          option="RADIUS", option_alias="Radius")]),
                 ])),
    # --- the verifyModifiers branches ---
    _s("Naked Advantage", ("AffectsDesolid", "AffectsPhysicalWorld", "Modifier", "CannotEscapeWithTeleport"),
       power("NAKEDMODIFIER", "Naked Advantage", 20, 30, name="Naked Advantage", input_="Blast", children=[
           modifier("AOE", "Area Of Effect", "0.5", levels=8, option="RADIUS", option_alias="Radius"),
           modifier("NOTELEPORT", "Cannot Escape With Teleportation", "-0.25")])),
    # --- the six prototype-END cells, now with state ---
    _s("Custom Power With END", ("CostsEND", "CostsENDToMaintain", "IncreasedEND", "Inherent", "Persistent"),
       power("CUSTOMPOWER", "Custom Power", 5, 31, name="Custom Power With END",
             extra=' DURATION="CONSTANT" TARGET="DCV" RANGE="STANDARD" ENDCOLUMNOUTPUT="" DOESBODY="No" DOESDAMAGE="No" DOESKNOCKBACK="No" KILLING="No" DEFENSE="NONE" COSTPERLEVEL="1.0" LEVELVALUE="1.0" DESCRIPTION="A custom power that costs END" USESEND="Yes"')),
    _s("Shape Shift", ("ReducedEND",),
       power("SHAPESHIFT", "Shape Shift", 0, 32, name="Shape Shift", option="SIGHTGROUP", option_alias="Sight Group")),
    # --- everything the survey missed and the fixed states above didn't already cover ---
    _s("Blast Alternate Combat Value", ("AlternateCombatValue",),
       power("ENERGYBLAST", "Blast", 8, 33, name="Blast Alternate Combat Value", children=[
           modifier("ACV", "Alternate Combat Value", "0.25", option="NONMENTALOMCV",
                    option_alias="Based on OMCV")])),
    _s("Blast Autofire", ("Autofire",),
       power("ENERGYBLAST", "Blast", 8, 34, name="Blast Autofire", children=[
           modifier("AUTOFIRE", "Autofire", "0.5", option="TWO", option_alias="2 Shots")])),
    _s("Blast Beam", ("Beam",),
       power("ENERGYBLAST", "Blast", 8, 35, name="Blast Beam", children=[
           modifier("BEAM", "Beam", "0.0")])),
    _s("Telepathy Can Be Missile Deflected", ("CanBeMissileDeflected",),
       power("TELEPATHY", "Telepathy", 4, 36, name="Telepathy Can Be Missile Deflected", children=[
           modifier("CANBEMISSILEDEFLECTED", "Can Be Missile Deflected", "0.25")])),
    _s("Blast Damage Over Time", ("DamageOverTime",),
       power("ENERGYBLAST", "Blast", 8, 37, name="Blast Damage Over Time", children=[
           modifier("DAMAGEOVERTIME", "Damage Over Time", "1.0")])),
    _s("Blast Delayed Effect", ("DelayedEffect",),
       power("ENERGYBLAST", "Blast", 8, 38, name="Blast Delayed Effect", children=[
           modifier("DELAYEDEFFECT", "Delayed Effect", "0.25", levels=1)])),
    # DelayedReturnRate (types=(ADJUSTMENT,), success = non-Healing) and OnlyToStarting
    # (types=(ADJUSTMENT,), success = non-Healing) both land cleanly on the same DRAIN.
    _s("Slow Drain", ("DelayedReturnRate", "OnlyToStarting"),
       power("DRAIN", "Drain", 2, 39, name="Slow Drain", input_="STR", children=[
           modifier("DELAYEDRETURNRATE", "Delayed Return Rate", "0.25", option="HOUR", option_alias="1 Hour"),
           modifier("ONLYTOSTARTING", "Only Restores To Starting Values", "-0.5")])),
    _s("Flight Extra Time", ("ExtraTime",),
       power("FLIGHT", "Flight", 10, 40, name="Flight Extra Time", children=[
           modifier("EXTRATIME", "Extra Time", "-0.25", option="PHASE", option_alias="Extra Phase")])),
    # Gestures and Incantations are both trivial pass-through overrides in the engine
    # (Java has no equivalent -- neither appears in the 81-row survey); one power carries
    # both since neither excludes the other.
    _s("Blast Gestures And Incantations", ("Gestures", "Incantations"),
       power("ENERGYBLAST", "Blast", 8, 41, name="Blast Gestures And Incantations", children=[
           modifier("GESTURES", "Gestures", "-0.25"),
           modifier("INCANTATIONS", "Incantations", "-0.25")])),
    # Hardened (types=(DEFENSE,), FORCEFIELD qualifies) and PhysicalManifestation (needs
    # duration CONSTANT -- a plain Force Field with no Persistent/etc modifier is Constant)
    # share a fresh, otherwise-unmodified Force Field so neither state above's Persistent
    # changes its duration out from under this one.
    _s("Force Field Hardened", ("Hardened", "PhysicalManifestation"),
       power("FORCEFIELD", "Resistant Protection", 6, 42, name="Force Field Hardened", input_="ED", children=[
           modifier("HARDENED", "Hardened", "0.25", levels=1),
           modifier("PHYSICALMANIFESTATION", "Physical Manifestation", "-0.25")])),
    _s("Blast Increased Max Range", ("IncreasedMaxRange",),
       power("ENERGYBLAST", "Blast", 8, 43, name="Blast Increased Max Range", children=[
           modifier("INCREASEDMAXRANGE", "Increased Maximum Range", "0.1", levels=1)])),
    _s("Blast Limited Range", ("LimitedRange",),
       power("ENERGYBLAST", "Blast", 8, 44, name="Blast Limited Range", children=[
           modifier("LIMITEDRANGE", "Limited Range", "-0.25")])),
    _s("Blast NND Standalone", ("NND",),
       power("ENERGYBLAST", "Blast", 8, 45, name="Blast NND Standalone", children=[
           modifier("NND", "No Normal Defense", "1.0", option="STANDARD", option_alias="Standard")])),
    _s("Blast Personal Immunity", ("PersonalImmunity",),
       power("ENERGYBLAST", "Blast", 8, 46, name="Blast Personal Immunity", children=[
           modifier("PERSONALIMMUNITY", "Personal Immunity", "0.25")])),
    # RangeBasedOnSTR and ReducedByRange neither excludes the other -- both fit one Blast.
    _s("Blast Range Based On STR", ("RangeBasedOnSTR", "ReducedByRange"),
       power("ENERGYBLAST", "Blast", 8, 47, name="Blast Range Based On STR", children=[
           modifier("RANGEBASEDONSTR", "Range Based On Strength", "-0.5"),
           modifier("REDUCEDBYRANGE", "Reduced By Range", "0.25")])),
    _s("Blast Restrainable", ("Restrainable",),
       power("ENERGYBLAST", "Blast", 8, 48, name="Blast Restrainable", children=[
           modifier("RESTRAINABLE", "Restrainable", "-0.5")])),
    # SelfOnly (types=(ADJUSTMENT,), success = target != SELFONLY -- DRAIN defaults to DCV)
    # and VariableEffect (types=(ADJUSTMENT,), trivial) share a second, distinct DRAIN.
    _s("Adjustable Drain", ("SelfOnly", "VariableEffect"),
       power("DRAIN", "Drain", 2, 49, name="Adjustable Drain", input_="CON", children=[
           modifier("SELFONLY", "Self Only", "-0.5"),
           modifier("VARIABLEEFFECT", "Variable Effect", "0.5")])),
    _s("Blast Side Effects", ("SideEffects",),
       power("ENERGYBLAST", "Blast", 8, 50, name="Blast Side Effects", children=[
           modifier("SIDEEFFECTS", "Side Effects", "-0.25", option="MINOR", option_alias="Minor")])),
    _s("Blast Sticky", ("Sticky",),
       power("ENERGYBLAST", "Blast", 8, 51, name="Blast Sticky", children=[
           modifier("STICKY", "Sticky", "0.5", option="STANDARD", option_alias="Standard")])),
    _s("Blast Subject To Range Modifier", ("SubjectToRangeModifier",),
       power("ENERGYBLAST", "Blast", 8, 52, name="Blast Subject To Range Modifier", children=[
           modifier("SUBJECTTORANGEMODIFIER", "Subject To Range Modifier", "-0.25")])),
    _s("Flight Turn Mode", ("TurnMode",),
       power("FLIGHT", "Flight", 10, 53, name="Flight Turn Mode", children=[
           modifier("TURNMODE", "Turn Mode", "-0.25")])),
    _s("Blast Usable On Others", ("UsableOnOthers",),
       power("ENERGYBLAST", "Blast", 8, 54, name="Blast Usable On Others", children=[
           modifier("UOO", "Usable By Other", "0.25", option="UBO", option_alias="Usable By Other")])),
    # VariableAdvantage and VariableLimitations are both trivial engine-only overrides;
    # one Blast carries both.
    _s("Blast Variable Advantage And Limitations", ("VariableAdvantage", "VariableLimitations"),
       power("ENERGYBLAST", "Blast", 8, 55, name="Blast Variable Advantage And Limitations", children=[
           modifier("VARIABLEADVANTAGE", "Variable Advantage", "0.5"),
           modifier("VARIABLELIMITATIONS", "Variable Limitations", "-0.25")])),
    # LimitedArcOfFire and PartialCoverage: authored to satisfy the Python coverage test (both
    # are real engine classes with their own included() override), but XMLIDs LIMITEDARCOFFIRE
    # and PARTIALCOVERAGE are NOT in Main6E.hdt -- Base6E.hdt/Vehicle6E.hdt only (grep -in
    # confirmed). HD is expected to DROP these two objects when validated against Main6E.hdt;
    # see NOT_AUTHORED below and the task-2-report.md for what step 5 actually found.
    _s("Blast Limited Arc Of Fire", ("LimitedArcOfFire",),
       power("ENERGYBLAST", "Blast", 8, 56, name="Blast Limited Arc Of Fire", children=[
           modifier("LIMITEDARCOFFIRE", "Limited Arc Of Fire", "-0.25", option="180DEGREES",
                    option_alias="180 degrees")])),
    _s("Force Field Partial Coverage", ("PartialCoverage",),
       power("FORCEFIELD", "Resistant Protection", 6, 57, name="Force Field Partial Coverage", input_="PD",
             children=[modifier("PARTIALCOVERAGE", "Partial Coverage", "-0.25", levels=1)])),
)

# NOT_AUTHORED: overrides the survey named that this generator could not exercise, and why.
# See the coverage test's own count and the task-2-report.md for the full accounting.
#   - LimitedArcOfFire, PartialCoverage ARE authored above (the Python coverage test requires
#     every real engine override to have a state), but their XMLIDs do not resolve against
#     Main6E.hdt -- see the comment on those two states. Whether HD actually accepts them is
#     reported by step 5, not assumed here.
#   - DoubleEnduranceCost, ENDReserveOrEND: named at length in the survey (both read
#     HeroDesigner.getActiveHero() to scan for an EnduranceReserve power), but kirby-cost has
#     no class of either name. HD's Double Endurance Cost is INCREASEDEND's own "2X" OPTION,
#     not a separate modifier; ENDReserveOrEND appears not to have been ported at all.
#   - AVLD, BasedOnECV, DamageShield, DelayedEND, DoesNotProvideMentalAwareness, Dropped,
#     Lingering, OthersOnly, RealWeapon, RequiredHands, SemiArmorPiercing, Transparent,
#     VariableTarget: surveyed Java overrides with no engine Modifier subclass at all
#     (kirby-cost's registry does not define these classes) -- outside this generator's
#     reach because there is no included() override to run.


def _terrain_characteristic() -> str:
    """ONLYONAPPROPRIATETERRAIN is defined inside RUNNING in Main6E.hdt; it goes on the
    characteristic, following the same regex substitution kitchen_sink.py uses. RUNNING's
    own NAME="" is also set to the state's name here, so it is traceable in HD's cost dump
    the same way every other state's object is (step 5 of the brief)."""
    import re
    terrain = modifier("ONLYONAPPROPRIATETERRAIN", "Only On Appropriate Terrain", "-0.5")
    named = re.sub(r'(<RUNNING [^>]*?)NAME=""', r'\1NAME="Running Only On Terrain"', _CHARACTERISTICS, count=1)
    return re.sub(r'(<RUNNING [^>]*>\s*<NOTES />)', r'\1\n' + terrain.replace('\\', '\\\\'), named,
                  count=1)


STATES = STATES + (
    _s("Running Only On Terrain", ("Modifier", "OnlyOnAppropriateTerrain"), ""),
)

OBJECT_NAMES: dict[str, str] = {s.name: s.name for s in STATES}


def build() -> str:
    """Assemble the document. No ID allocation happens here -- STATES and
    _CHARACTERISTICS_WITH_TERRAIN are already fully-built strings from import time -- so this
    function is pure formatting and returns the same bytes on every call."""
    powers = [s.xml for s in STATES if s.xml]
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
{_CHARACTERISTICS_WITH_TERRAIN}
<SKILLS />
<PERKS />
<TALENTS />
<MARTIALARTS />
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


_INFO = '<CHARACTER_INFO CHARACTER_NAME="Validation Sink" ALTERNATE_IDENTITIES="" PLAYER_NAME="" HEIGHT="180.0" WEIGHT="80.0" HAIR_COLOR="" EYE_COLOR="" CAMPAIGN_NAME="" GENRE="" GM="">'

_CHARACTERISTICS = '  <CHARACTERISTICS>\n    <STR XMLID="STR" ID="1674528649148" BASECOST="0.0" LEVELS="5" ALIAS="STR" POSITION="1" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </STR>\n    <DEX XMLID="DEX" ID="1674528648883" BASECOST="0.0" LEVELS="8" ALIAS="DEX" POSITION="2" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </DEX>\n    <CON XMLID="CON" ID="1674528648965" BASECOST="0.0" LEVELS="5" ALIAS="CON" POSITION="3" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </CON>\n    <INT XMLID="INT" ID="1674528648998" BASECOST="0.0" LEVELS="3" ALIAS="INT" POSITION="4" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </INT>\n    <EGO XMLID="EGO" ID="1674528648811" BASECOST="0.0" LEVELS="8" ALIAS="EGO" POSITION="5" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </EGO>\n    <PRE XMLID="PRE" ID="1674528648982" BASECOST="0.0" LEVELS="15" ALIAS="PRE" POSITION="6" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </PRE>\n    <OCV XMLID="OCV" ID="1674528649511" BASECOST="0.0" LEVELS="3" ALIAS="OCV" POSITION="7" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </OCV>\n    <DCV XMLID="DCV" ID="1674528648625" BASECOST="0.0" LEVELS="2" ALIAS="DCV" POSITION="8" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </DCV>\n    <OMCV XMLID="OMCV" ID="1674528649055" BASECOST="0.0" LEVELS="5" ALIAS="OMCV" POSITION="9" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </OMCV>\n    <DMCV XMLID="DMCV" ID="1674528648705" BASECOST="0.0" LEVELS="2" ALIAS="DMCV" POSITION="10" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </DMCV>\n    <SPD XMLID="SPD" ID="1674528649134" BASECOST="0.0" LEVELS="2" ALIAS="SPD" POSITION="11" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </SPD>\n    <PD XMLID="PD" ID="1674528648927" BASECOST="0.0" LEVELS="0" ALIAS="PD" POSITION="12" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </PD>\n    <ED XMLID="ED" ID="1674528649373" BASECOST="0.0" LEVELS="0" ALIAS="ED" POSITION="13" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </ED>\n    <REC XMLID="REC" ID="1674528649207" BASECOST="0.0" LEVELS="4" ALIAS="REC" POSITION="14" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </REC>\n    <END XMLID="END" ID="1674528649022" BASECOST="0.0" LEVELS="20" ALIAS="END" POSITION="15" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </END>\n    <BODY XMLID="BODY" ID="1674528649409" BASECOST="0.0" LEVELS="5" ALIAS="BODY" POSITION="16" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </BODY>\n    <STUN XMLID="STUN" ID="1674528649021" BASECOST="0.0" LEVELS="14" ALIAS="STUN" POSITION="17" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </STUN>\n    <RUNNING XMLID="RUNNING" ID="1674528649464" BASECOST="0.0" LEVELS="0" ALIAS="Running" POSITION="18" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </RUNNING>\n    <SWIMMING XMLID="SWIMMING" ID="1674528649027" BASECOST="0.0" LEVELS="0" ALIAS="Swimming" POSITION="19" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </SWIMMING>\n    <LEAPING XMLID="LEAPING" ID="1674528649234" BASECOST="0.0" LEVELS="0" ALIAS="Leaping" POSITION="20" MULTIPLIER="1.0" GRAPHIC="Burst" COLOR="255 255 255" SFX="Default" SHOW_ACTIVE_COST="Yes" INCLUDE_NOTES_IN_PRINTOUT="Yes" NAME="" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">\n      <NOTES />\n    </LEAPING>\n  </CHARACTERISTICS>'


# The terrain characteristic block is built once, at import time (like STATES), so build()
# never allocates another ID and stays deterministic across repeated calls in one process.
_CHARACTERISTICS_WITH_TERRAIN = _terrain_characteristic()
