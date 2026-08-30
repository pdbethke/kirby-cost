"""The three doors a builder walks through -- the same three HD has."""
from kirby_cost import allowed_modifiers, check, exclusive_conflict
from tests.matrix_support import template_modifier, template_power


def test_check_refuses_with_hd_message():
    # Literal from tests/fixtures/included_matrix.json's ZEROPHASE-on-
    # ENERGYBLAST cell -- HD's actual message, not the brief's paraphrase.
    v = check("ZEROPHASE", template_power("ENERGYBLAST"))
    assert v.allowed is False
    assert v.reason == (
        "Powers Can Be Changed As A Zero-Phase Action can only be applied "
        "to abilities of type vpp"
    )


def test_check_allows_with_empty_reason():
    v = check("ARMORPIERCING", template_power("ENERGYBLAST"))
    assert v.allowed is True and v.reason == ""


def test_check_unknown_modifier_is_a_refusal_not_an_exception():
    v = check("NO_SUCH_MODIFIER", template_power("ENERGYBLAST"))
    assert v.allowed is False and "unknown modifier" in v.reason


def test_allowed_modifiers_lists_every_template_modifier_with_a_verdict():
    rows = allowed_modifiers(template_power("ENERGYBLAST"))
    assert len(rows) > 50
    by = {t.xmlid: v for t, v in rows}
    assert by["ARMORPIERCING"].allowed is True
    assert by["ZEROPHASE"].allowed is False


def test_exclusive_conflict_refuses_a_second_instance():
    power = template_power("ENERGYBLAST")
    assert exclusive_conflict("HALFRANGEMODIFIER", power).allowed is True
    power._assigned_modifiers.append(template_modifier("HALFRANGEMODIFIER"))
    v = exclusive_conflict("HALFRANGEMODIFIER", power)
    assert v.allowed is False and "already" in v.reason


def test_a_non_exclusive_modifier_may_repeat():
    # ARMORPIERCING is itself EXCLUSIVE="Yes" in Main6E, so it can't stand in
    # for "non-exclusive" -- NOKB (No Knockback) is not EXCLUSIVE and is
    # allowed on ENERGYBLAST per the matrix fixture.
    power = template_power("ENERGYBLAST")
    power._assigned_modifiers.append(template_modifier("NOKB"))
    assert exclusive_conflict("NOKB", power).allowed is True
