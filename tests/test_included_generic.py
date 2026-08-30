"""The generic applicability rules, by name -- Modifier.java:763 onward.

The matrix (tests/test_included_matrix.py) proves the whole; these say which
rule each cell is about, so a regression names itself. Built from template
prototypes like the matrix.
"""
from kirby_cost.objects.modifier import Modifier

from tests.matrix_support import blank_hero_context, template_modifier, template_power


def setup_module(module):  # noqa: ARG001 -- pytest hook
    blank_hero_context()


def _bare(display: str) -> Modifier:
    """A plain base Modifier -- subclass included() overrides are Task 6."""
    mod = Modifier()
    mod.display = display
    return mod


def test_an_instant_only_modifier_refuses_a_constant_power():
    """Modifier.java:783-789. No modifier in Main6E carries DURATION, so the
    rule is exercised on a bare modifier rather than a template prototype."""
    mod = _bare("Instant Only")
    mod._duration = "INSTANT"
    assert mod.included(template_power("FLIGHT")) == \
        "Instant Only can only be applied to Instant Powers."
    assert mod.included(template_power("ENERGYBLAST")) == ""


def test_a_constant_only_modifier_refuses_an_instant_power():
    """Modifier.java:790-795."""
    mod = _bare("Constant Only")
    mod._duration = "CONSTANT"
    assert mod.included(template_power("ENERGYBLAST")) == \
        "Constant Only can only be applied to Constant Powers."


def test_a_framework_typed_modifier_on_a_list_names_the_framework():
    """Modifier.java:843-846. The framework branch is reached only when the
    modifier has no types OR the object is a List, so TYPE=VPP names the
    framework there (6E1 p.398, Power Frameworks)."""
    from kirby_cost.objects.list import List as HeroList
    mod = template_modifier("ZEROPHASE")        # TYPE=VPP
    assert mod.included(HeroList()) == \
        f"{mod.display} can only be applied to a Variable Power Pool."


def test_a_framework_typed_modifier_on_an_ordinary_power_falls_to_type_matching():
    """Modifier.java:832-873. On a non-List the same TYPE=VPP goes down the
    type-matching branch instead, and HD says 'of type vpp' -- the matrix
    fixture records exactly that for ZEROPHASE on Blast."""
    mod = template_modifier("ZEROPHASE")
    assert mod.included(template_power("ENERGYBLAST")) == \
        f"{mod.display} can only be applied to abilities of type vpp"


def test_type_matching_message_lists_types_with_or():
    """Modifier.java:854-865: ', ' between, 'or ' before the last, and NOTHING
    appended after the list -- HD's message has no trailing period."""
    mod = _bare("Three Types")
    mod._types = ["ATTACK", "MENTAL", "MOVEMENT"]
    power = template_power("FLIGHT")           # types: MOVEMENT -> allowed
    assert mod.included(power) == ""
    power._types = ["DEFENSE"]
    assert mod.included(power) == \
        f"{mod.display} can only be applied to abilities of type attack, mental, or movement"


def test_a_single_type_is_listed_without_or():
    """Modifier.java:857-862 -- 'or ' needs i > 0, so one type stands alone."""
    mod = template_modifier("ABLATIVE")        # TYPE=DEFENSE
    power = template_power("ENERGYBLAST")
    assert mod.included(power) == \
        f"{mod.display} can only be applied to abilities of type defense"


def test_an_untyped_power_refuses_a_typed_modifier():
    """Modifier.java:866-873: the message is built first and only a MATCHING
    power type clears it, so a power with no types at all keeps the refusal.
    (The obvious reading -- 'no types, so nothing to violate' -- is not HD's.)"""
    mod = template_modifier("ABLATIVE")
    power = template_power("ENERGYBLAST")
    power._types = []
    assert mod.included(power) == \
        f"{mod.display} can only be applied to abilities of type defense"


def test_an_untyped_modifier_fits_anything():
    """Modifier.java:838-842 -- an empty TYPE list is no restriction."""
    mod = _bare("No Types")
    assert mod._types == []
    assert mod.included(template_power("FLIGHT")) == ""


def test_excludes_refuses_when_the_excluded_modifier_is_present():
    """Modifier.java:880-887, HD's own 'abilties' typo included."""
    power = template_power("ENERGYBLAST")
    los = template_modifier("LOS")
    power.assigned_modifiers.append(los)
    mod = _bare("Half Range Modifier")
    mod._excludes = ("LOS", "NORANGEMODIFIER")
    assert mod.included(power) == \
        f"{mod.display} cannot be applied to abilties which have {los.display}"


def test_excludes_refuses_the_power_itself_by_xmlid():
    """Modifier.java:888-891."""
    mod = _bare("Half Range Modifier")
    mod._excludes = ("ENERGYBLAST",)
    power = template_power("ENERGYBLAST")
    assert mod.included(power) == f"{mod.display} cannot be applied to {power.display}"


def test_requires_any_of_lists_the_options_and_is_met_by_one():
    """Modifier.java:900-960 -- MULTIPLESFX is Main6E's only REQUIRES, and it
    narrows on an option (XMLID.OPTIONID)."""
    mod = template_modifier("MULTIPLESFX")
    mod._types = []                             # TYPE=ADJUSTMENT, not the point here
    assert mod._requires == ("VARIABLEEFFECT.TWO", "VARIABLEEFFECT.FOUR",
                             "VARIABLEEFFECT.ALL")
    power = template_power("ENERGYBLAST")
    assert mod.included(power) == (
        f"{mod.display} requires at least one of the following: "
        "VARIABLEEFFECT.TWO, VARIABLEEFFECT.FOUR, or VARIABLEEFFECT.ALL")

    variable = template_modifier("VARIABLEEFFECT")
    option = type("Opt", (), {"xmlid": "FOUR"})()
    variable._selected_option = option
    power.assigned_modifiers.append(variable)
    assert mod.included(power) == ""


def test_force_allow_bypasses_everything():
    """Modifier.java:779-781 -- forceAllow() returns before every rule."""
    mod = template_modifier("ZEROPHASE")
    mod.force_allow = True
    assert mod.included(template_power("ENERGYBLAST")) == ""


def test_a_modifier_on_a_modifier_is_judged_against_the_progenitor():
    """Modifier.java:770-778 -- getProgenitor() walks up to the real ability."""
    power = template_power("ENERGYBLAST")
    carrier = template_modifier("LOS")
    carrier.parent = power
    mod = template_modifier("ABLATIVE")         # TYPE=DEFENSE, so refused
    assert mod.included(carrier) == \
        f"{mod.display} can only be applied to abilities of type defense"


def test_an_orphan_modifier_parent_is_allowed():
    """Modifier.java:775-777 -- a null progenitor short-circuits to allowed."""
    mod = template_modifier("ABLATIVE")
    assert mod.included(template_modifier("LOS")) == ""


def test_an_advantage_may_not_go_on_an_elemental_control():
    """Modifier.java:826-831. 6E1 p.23 removed Elemental Controls from the
    system; the rule survives in HD for 5E-era builds."""
    from kirby_cost.objects.frameworks.elemental_control import ElementalControl
    ec = ElementalControl()
    ec.xmlid = "ELEMENTAL_CONTROL"
    mod = _bare("An Advantage")                 # is_limitation False
    assert mod.included(ec) == (
        f"{mod.display} cannot be applied to an Elemental Control.  "
        "Advantages should be applied to each slot individually.")


# --- subclass included() overrides (Task 6) --------------------------------


def test_does_knockback_refuses_a_power_that_already_does_knockback():
    """DoesKB.java:37-54. `doesKnockback` is a field on GenericObject, not a
    method; the port called it. 6E1 p.335 -- HD agrees with the book, which
    describes Does Knockback as enabling Knockback on an Attack Power that
    normally does not do it, so a power that already does it has nothing to buy."""
    mod = template_modifier("DOESKB")
    assert mod.included(template_power("ENERGYBLAST")) == \
        f"{template_power('ENERGYBLAST').display} already does Knockback."


def test_does_knockback_requires_a_power_targeted_on_others():
    """DoesKB.java:47-51 -- target must be DCV, ECV or HEX. HD rule, no page."""
    mod = template_modifier("DOESKB")
    assert mod.included(template_power("FLASH")) == ""


def test_no_knockback_requires_a_power_that_does_knockback():
    """NoKB.java:37-50. 6E1 p.145 (No Knockback, Limitation) -- HD agrees with
    the book: the Limitation removes Knockback, so there must be some to remove."""
    mod = template_modifier("NOKB")
    assert mod.included(template_power("FLASH")) == \
        f"{mod.display} can only be applied to abilities which do Knockback."
    assert mod.included(template_power("ENERGYBLAST")) == ""


def test_double_knockback_requires_a_power_that_does_knockback():
    """DoubleKB.java:75-88. 6E1 p.336 -- HD agrees with the book, which frames
    Double Knockback as multiplying the Knockback a power already does."""
    mod = template_modifier("DOUBLEKB")
    assert mod.included(template_power("FLASH")) == \
        f"{mod.display} can only be applied to abilities which do Knockback."
    assert mod.included(template_power("ENERGYBLAST")) == ""


def test_does_body_refuses_a_flash_and_a_power_that_already_does_body():
    """DoesBODY.java:37-56. 6E1 p.335 -- HD agrees with the book (the Advantage
    lets STUN-only attacks such as Mental Blast and AVAD also do BODY); the
    Flash exclusion is HD's own, no page."""
    mod = template_modifier("DOESBODY")
    assert mod.included(template_power("FLASH")) == \
        f"{mod.display} cannot be applied to a Flash Attack."
    assert mod.included(template_power("ENERGYBLAST")) == \
        f"{template_power('ENERGYBLAST').display} already does BODY Damage."


def test_cannot_escape_with_teleport_allows_only_barriers_and_entangles():
    """CannotEscapeWithTeleport.java:111-125. The port imported a module named
    `characteristics.def_`, which does not exist -- the class is
    `characteristics.def_char.DefChar` -- so every cell raised
    ModuleNotFoundError. 6E1 p.304 (also p.175 Barrier, p.220 Entangle): HD
    agrees with the book, which puts the Advantage on walls, Entangles and
    other barriers."""
    mod = template_modifier("NOTELEPORT")
    assert mod.included(template_power("ENTANGLE")) == ""
    assert mod.included(template_power("FORCEWALL")) == ""
    assert mod.included(template_power("ENERGYBLAST")) == (
        f"{mod.display} can only be applied to Entangles or Powers which are "
        "used to create walls or barriers.")


def test_hole_in_the_middle_needs_an_area_affecting_ability():
    """HoleInTheMiddle.java:77-90 -- the port was a `return ""` stub with the
    rule commented out. 6E1 p.337: the Advantage gives an area-affecting power
    a safe zone at its centre. HD deviates in reach: it tests the object's own
    TARGET=HEX, so a power made area-affecting by the Area Of Effect Advantage
    (whose base TARGET is still DCV) is refused."""
    mod = template_modifier("HOLEINTHEMIDDLE")
    assert mod.included(template_power("ENERGYBLAST")) == \
        f"{mod.display} can only be applied to abilities which affect an area."
    assert mod.included(template_power("DARKNESS")) == ""


# --- the effective duration (GenericObject.getDuration) --------------------


def test_a_blank_duration_reads_as_instant_under_a_6e_template():
    """GenericObject.java:1734-1736 -- in 6E, an object whose DURATION field is
    neither PERSISTENT, INHERENT nor CONSTANT, and which carries no duration
    modifier, reports INSTANT. HD rule, no page: it is the fall-through of
    getDuration(), not a book statement."""
    from kirby_cost.objects.list import List as HeroList
    obj = HeroList()
    assert obj.orig_duration == ""
    assert obj.duration == "INSTANT"


def test_continuous_makes_an_instant_power_constant():
    """GenericObject.java:1723-1725. 6E1 p.336 (Duration Advantages): the
    Constant Advantage makes an Instant Power Constant. HD agrees; the engine
    used to return the raw DURATION field and never saw the change."""
    power = template_power("ENERGYBLAST")
    assert power.duration == "INSTANT"
    power.assigned_modifiers.append(template_modifier("CONTINUOUS"))
    assert power.duration == "CONSTANT"
    assert power.orig_duration == "INSTANT"


def test_a_persistent_power_that_costs_end_reports_constant():
    """GenericObject.java:1685-1698. 6E1 p.336: a Persistent Power must be 0
    END; HD enforces that by reporting a Persistent power that still costs END
    as Constant unless it takes Costs END To Maintain.

    This asserts the TEMPLATE PROTOTYPE's state -- HD's own, built from the
    template entry (Hero.java:2803-2807, GenericObject.java:3131-3133), which
    is what the harness reproduces; the engine's loader instead lets a
    constructor-hardcoded duration stand (force_field.py:38), a loader defect
    filed as a follow-up outside this plan.
    """
    power = template_power("FORCEFIELD")        # PERSISTENT in Main6E
    power.uses_end = True
    assert power.orig_duration == "PERSISTENT"
    assert power.duration == "CONSTANT"
    power.assigned_modifiers.append(template_modifier("COSTSENDTOMAINTAIN"))
    assert power.duration == "PERSISTENT"


def test_time_limit_refuses_a_power_whose_duration_is_neither_persistent_constant_nor_instant():
    """TimeLimit.java:85-90 -- the port was a `return ""` stub. 6E1 p.348: Time
    Limit is for inherently Persistent Powers, for Instant Powers that create
    lingering effects, and (as an Advantage) for Constant Powers. HD agrees."""
    mod = template_modifier("TIMELIMIT")
    assert mod.included(template_power("AUTOMATON")) == \
        f"{mod.display} can only be applied to Persistent, Constant, or Instant Powers"


def test_time_limit_refuses_a_non_instant_power_that_costs_end():
    """TimeLimit.java:91-104. 6E1 p.348 -- HD agrees with the book: as an
    Advantage, Time Limit is for Constant Powers 'that cost 0 END or that only
    cost END to activate'. COSTSENDONLYTOACTIVATE, or COSTSEND with option
    ACTIVATE or ONLYTOCHANGE, clears it."""
    mod = template_modifier("TIMELIMIT")
    power = template_power("FLIGHT")            # CONSTANT, uses END
    assert mod.included(power) == (
        f"{mod.display} can only be applied to abilities which cost 0 END or "
        "which cost END only to activate")
    power.assigned_modifiers.append(template_modifier("COSTSENDONLYTOACTIVATE"))
    assert mod.included(power) == ""


def test_invisible_power_effects_does_not_refuse_a_6e_power_as_already_invisible():
    """Invisible.java:280-300. The "X is already invisible." refusal is guarded
    on `!getActiveTemplate().is6E()`; the port's `_is_6e_template()` returned a
    hardcoded False, so it fired for every 6E power. 6E1 p.340 (Invisible Power
    Effects) states no such restriction -- HD's rule is 5E-era and, correctly
    gated, does not apply here. The VISIBLE-Limitation refusal is HD's own,
    ungated by edition; no page."""
    mod = template_modifier("INVISIBLE")
    assert mod.included(template_power("ABSORPTION")) == ""
    power = template_power("ENERGYBLAST")
    power.assigned_modifiers.append(template_modifier("VISIBLE"))
    assert mod.included(power) == (
        f"{mod.display} cannot be applied to a Power/ability with the Visible "
        "Limitation on it.")


def test_persistent_asks_the_template_edition_and_the_duration_field():
    """Persistent.java:37-77. The port read EngineContext.active_template(),
    which is None everywhere, so every 6E branch took its 5E form and refused
    any power costing END outright. It also collapsed the last two checks into
    an unreachable tangle; Java tests the effective duration OR the DURATION
    field (getOrigDuration). 6E1 p.334 (Persistent): a Persistent Power must
    not cost END to activate; HD agrees, and in 6E allows Costs END To
    Maintain."""
    mod = template_modifier("PERSISTENT")
    power = template_power("FORCEFIELD")            # PERSISTENT field
    assert mod.included(power) == f"{power.display} is already Persistent."


def test_ranged_refuses_reflection_and_allows_missile_deflection():
    """Ranged.java:102-132 -- the port had these two inverted: it returned ""
    for Reflection and had no Missile Deflection branch at all. 6E1 p.344
    (Ranged): HD rule, no page, for which powers are excluded."""
    mod = template_modifier("RANGED")
    assert mod.included(template_power("REFLECTION")) == \
        f"{mod.display} cannot be applied to Reflection."
    assert mod.included(template_power("MISSILEDEFLECTION")) == ""


def test_megascale_needs_an_area_movement_or_ranged_power():
    """Megascale.java:184-210 -- the port returned "" with a comment claiming
    Java has no override; it has one. 6E1 p.342 lists the powers MegaScale may
    be bought for; HD's proxy for that list is TARGET=HEX, a MOVEMENT type that
    is not FTL or Extradimensional Movement, a positive range value, Mind Scan,
    or a Sense with a built-in RANGE adder. HD deviates in reach -- it derives
    "works at Range" from getRangeValue(), which is a function of the power's
    cost, not from the book's list."""
    mod = template_modifier("MEGASCALE")
    assert mod.included(template_power("FLIGHT")) == ""          # MOVEMENT
    assert mod.included(template_power("ENERGYBLAST")) == ""      # ranged
    assert mod.included(template_power("FTL")) == (
        f"{mod.display} can only be applied to Powers which already affect an "
        "area, Movement Powers (except Extradimensional Movement and FTL "
        "Travel), and Powers which work at Range.")


def test_costs_end_to_maintain_is_a_method_not_a_field():
    """GenericObject.java:3011-3036 -- the engine had only the field, so
    Persistent.included() raised TypeError calling it. HD rule, no page: it is
    a bookkeeping predicate, not a rule from the book."""
    power = template_power("FLIGHT")                    # CONSTANT, costs END
    assert power.costs_end_to_maintain() is True
    power.assigned_modifiers.append(template_modifier("COSTSENDONLYTOACTIVATE"))
    assert power.costs_end_to_maintain() is False
    assert template_power("ENERGYBLAST").costs_end_to_maintain() is False  # INSTANT


def test_the_matrix_prototype_carries_the_templates_cost():
    """HD computes the matrix against prototypes built FROM the template, so
    they carry its BASECOST and LEVELSTART and therefore have a cost --
    getRangeValue() derives a ranged power's reach from it (GenericObject.java
    :2389-2398). The engine's loader leaves both at zero for an object no .hdc
    stated, so every ranged prototype used to read as reaching 0m."""
    blast = template_power("ENERGYBLAST")               # LEVELSTART=1, LVLCOST=5
    assert blast.levels == 1
    assert blast.range_value > 0
    deflection = template_power("MISSILEDEFLECTION")    # BASECOST=20
    assert deflection.base_cost == 20


# --- getOrigDuration vs getDuration at the call sites ----------------------


def test_continuous_reads_the_duration_field_not_the_effective_duration():
    """Continuous.java:47,51,54,61,64 all read getOrigDuration(). A Persistent
    power that still costs END reports CONSTANT for getDuration()
    (GenericObject.java:1685-1698) and PERSISTENT for the field, so reading the
    wrong one calls it "already Constant". 6E1 p.336 (Duration Advantages):
    Constant cannot be applied to a power that is already Persistent -- HD
    agrees with the book, and judges it on what the power was written as."""
    power = template_power("FORCEFIELD")        # DURATION="PERSISTENT"
    power.uses_end = True                       # ... but bought costing END
    assert power.orig_duration == "PERSISTENT"
    assert power.duration == "CONSTANT"
    mod = template_modifier("CONTINUOUS")
    assert mod.included(power) == \
        f"{power.display} is already Persistent in duration."


def test_costs_end_to_maintain_asks_both_durations():
    """CostsENDToMaintain.java:63 reads getDuration(), :68 reads
    getOrigDuration(); the port read getDuration() for both, so :68 was a dead
    duplicate of :63. HD rule, no page.

    Pinned here on a Constant power made Instant: :63 sees INSTANT and refuses,
    which it could not do if it read the DURATION field (still CONSTANT).

    :68 stays unobservable on this engine, and not because of this fix -- it
    needs `duration != INSTANT` while `orig_duration == INSTANT` and
    `continuing_effect` False, and every modifier that rewrites the effective
    duration also turns `continuing_effect` on. Java's `continuingEffect()` is
    a plain FIELD read (GenericObject.java:3003-3005) where this engine infers
    it from the duration modifiers (base.py:1097-1110); porting that is a
    separate follow-up.
    """
    power = template_power("FLIGHT")            # DURATION="CONSTANT", costs END
    power.assigned_modifiers.append(template_modifier("INSTANT"))
    assert power.orig_duration == "CONSTANT"
    assert power.duration == "INSTANT"
    assert power.continuing_effect is False
    mod = template_modifier("COSTSENDTOMAINTAIN")
    assert mod.included(power) == (
        f"{mod.display} can only be applied to abilities which are Constant "
        "in duration.")


# --- doesBODY() / doesKnockback() are methods, not fields ------------------


def test_nnd_turns_off_does_body_without_touching_the_field():
    """GenericObject.doesBODY (GenericObject.java:868-895). AVAD, NND, AVLD,
    Based On ECV and STUN Only all switch it off; Does BODY switches it back
    on. 6E1 p.328 (AVAD/NND): such attacks do STUN only unless the Does BODY
    Advantage is bought -- HD agrees with the book."""
    power = template_power("ENERGYBLAST")       # DOESBODY="Yes"
    assert power.does_body is True
    power.assigned_modifiers.append(template_modifier("NND"))
    assert power.does_body is False
    assert power.orig_does_body is True         # the field is untouched
    power.assigned_modifiers.append(template_modifier("DOESBODY"))
    assert power.does_body is True


def test_nnd_turns_off_does_knockback_and_nokb_wins_over_doeskb():
    """GenericObject.doesKnockback (GenericObject.java:914-942). STUN Only,
    NND, AVLD and Based On ECV switch it off; Does BODY and Does Knockback
    switch it on; No Knockback is re-checked LAST, so it beats Does Knockback.
    6E1 p.145 (No Knockback) and p.335 (Does Knockback); HD agrees, and the
    precedence is HD's own ordering, no page."""
    power = template_power("ENERGYBLAST")       # DOESKNOCKBACK="Yes"
    assert power.does_knockback is True
    power.assigned_modifiers.append(template_modifier("NND"))
    assert power.does_knockback is False
    assert power.orig_does_knockback is True    # the field is untouched
    power.assigned_modifiers.append(template_modifier("DOESKB"))
    assert power.does_knockback is True
    power.assigned_modifiers.append(template_modifier("NOKB"))
    assert power.does_knockback is False


# --- Round 2: the residue the matrix still names --------------------------


def test_transdimensional_needs_a_power_aimed_at_someone_else():
    """Transdimensional.java:111-128 -- the port was a `return ""` whose
    comment falsely claimed Java has no override. Stretching is allowed
    outright; otherwise the object's TARGET must be DCV, ECV or HEX. 6E1 p.350:
    the Advantage lets a power "affect targets in other dimensions", so a power
    that targets nobody has nothing to reach -- HD agrees with the book, and
    TARGET is its proxy for "affects others"."""
    mod = template_modifier("TRANSDIMENSIONAL")
    assert mod.included(template_power("ENERGYBLAST")) == ""     # DCV
    assert mod.included(template_power("STRETCHING")) == ""      # allowed outright
    assert mod.included(template_power("FLIGHT")) == (
        f"{mod.display} can only be applied to Powers which affect/are "
        "targeted on others.")


def test_a_refusal_names_the_modifier_with_its_levels_substituted():
    """Modifier.included()'s messages interpolate Java's getDisplay()
    (GenericObject.java:1631-1656), which substitutes a `[LVL]` placeholder
    with the level count -- the port interpolated the raw DISPLAY field. Main6E
    declares Expanded Effect as `DISPLAY="Expanded Effect (x[LVL] ...)"
    LEVELSTART="2"`, so HD writes "x2" and the engine wrote "x[LVL]". HD rule,
    no page: the placeholder is a template mechanism, not a book statement.

    Needs BOTH halves -- the substituting `display` AND the prototype carrying
    LEVELSTART; with either alone the message reads "x[LVL]" or "x0"."""
    mod = template_modifier("EXPANDEDEFFECT")   # TYPE=ADJUSTMENT
    assert mod.levels == 2
    assert mod.display == "Expanded Effect (x2 Characteristics or Powers simultaneously)"
    assert mod.included(template_power("ENERGYBLAST")) == \
        f"{mod.display} can only be applied to abilities of type adjustment"


def test_costs_end_to_maintain_accepts_a_continuing_effect_instant_power():
    """CostsENDToMaintain.java:63 refuses an INSTANT power only when it is not
    a continuing effect. Main6E states CONTINUINGEFFECT="Yes" on Entangle,
    Barrier, Summon and 20 others; the template pipeline parsed every other
    attribute of those elements and dropped this one, so the prototype said
    False and HD's own answer was refused. 6E1 p.155 (Costs Endurance To
    Maintain): the Limitation is for a "continuing-effect" power -- HD agrees
    with the book, and an Entangle is exactly that."""
    power = template_power("ENTANGLE")          # INSTANT, CONTINUINGEFFECT=Yes
    assert power.orig_duration == "INSTANT"
    assert power.continuing_effect is True
    assert template_modifier("COSTSENDTOMAINTAIN").included(power) == ""


def test_the_movement_characteristics_are_self_only():
    """RUNNING, LEAPING and SWIMMING are CHARACTERISTICS in Main6E, not powers,
    so the loader's power dispatch missed them and the matrix built a
    _FallbackObject with TARGET "N/A". HD's object is the Characteristic, whose
    init sets TARGET="SELFONLY" (Characteristic.java:1826-1844). 6E1 p.344
    (Ranged): the Advantage gives a power range, and a character's own Running
    is not something he aims at anybody -- HD agrees, and TARGET is its proxy.
    """
    for xmlid in ("RUNNING", "LEAPING", "SWIMMING"):
        power = template_power(xmlid)
        assert power.target == "SELFONLY", xmlid
        mod = template_modifier("RANGED")
        assert mod.included(power) == \
            f"{mod.display} cannot be applied to Self-Only Powers.", xmlid


def test_difficult_to_dispel_reproduces_hds_double_space():
    """DifficultToDispel.java:95-97. HD writes two spaces between the two
    sentences; the port wrote one. HD rule, no page -- 6E1 p.135 (Dispel) says
    nothing about Inherent, the refusal is HD's own."""
    mod = template_modifier("DIFFICULTTODISPEL")
    power = template_power("AUTOMATON")          # INHERENT in Main6E
    assert power.duration == "INHERENT"
    assert mod.included(power) == (
        f"{mod.display} cannot be applied to an Inherent ability.  "
        "Inherent abilities cannot be Dispelled.")
