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
    # for "non-exclusive". LIMITEDPOWER is one of Main6E's 8 MODIFIER
    # elements that state EXCLUSIVE="No" outright, and the matrix fixture
    # allows it on ENERGYBLAST.
    power = template_power("ENERGYBLAST")
    power._assigned_modifiers.append(template_modifier("LIMITEDPOWER"))
    assert exclusive_conflict("LIMITEDPOWER", power).allowed is True


def test_an_absent_exclusive_attribute_means_exclusive():
    # GenericObject.java:3054 initialises `exclusive = true` before reading
    # the element, and :3106-3111 clears it ONLY when EXCLUSIVE starts with
    # "N" -- an absent attribute (NOKB carries none) means exclusive, not
    # the reverse.
    power = template_power("ENERGYBLAST")
    assert exclusive_conflict("NOKB", power).allowed is True
    power._assigned_modifiers.append(template_modifier("NOKB"))
    v = exclusive_conflict("NOKB", power)
    assert v.allowed is False and "already" in v.reason


def test_verify_reports_a_refused_common_modifier_on_its_slot():
    """The framework door, checked against HD's own words: the sink's
    Multipower has AOE as a common modifier and a self-targeted Resistant
    Protection slot, and the fixture's `framework` row for that pair carries
    the message HD showed. verify() must return that message, on that slot."""
    from kirby_cost import verify
    from tests.matrix_support import sink_hero, stateful_cells
    mp = next(o for o in sink_hero().powers if o.name == "Multipower")
    row = next(c for c in stateful_cells()
               if c["tier"] == "framework" and c["modifier"] == "AOE"
               and c["parent_id"] == mp.hdc_id() and not c["allowed"])
    finding = next(f for f in verify(mp)
                   if f.modifier_xmlid == "AOE" and f.slot_id == row["object_id"])
    assert finding.verdict.reason == row["reason"]
    assert finding.verdict.allowed is False


def test_verify_is_empty_for_a_clean_power():
    from kirby_cost import verify
    from tests.matrix_support import sink_hero
    # NOT the brief's "Blast AOE": that power's MOBILE is one of the cells in
    # tests/fixtures/included_stateful_known_gaps.json (the engine refuses it,
    # HD allows it), so it is not clean until that gap closes. "Blast
    # Penetrating" carries PENETRATING and HD is content with it.
    blast = next(o for o in sink_hero().powers if o.name == "Blast Penetrating")
    assert verify(blast) == []


def test_verify_refuses_a_modifier_as_its_subject():
    """A modifier is not a purchasable object; three subclasses override the
    ``assigned_modifiers`` getter with no setter, so the walk would crash."""
    import pytest
    from kirby_cost import verify
    from tests.matrix_support import template_modifier
    with pytest.raises(TypeError, match="not a modifier"):
        verify(template_modifier("CONCENTRATION"))
