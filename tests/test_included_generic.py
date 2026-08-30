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
