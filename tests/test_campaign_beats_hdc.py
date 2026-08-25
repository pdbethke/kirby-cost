"""A house rule a character can be exempt from is not a rule.

apply_template applies HDC-stated values AFTER the template, guarded by a
`stated` set, so without this change a campaign value loses to anything the
character's own file happened to state. That is not hypothetical: the corpus
.hdc files state BASECOST 371 times.

CustomPower rather than KillingAttackRanged on purpose. `_stated_and_declared`
intersects what the SOURCE stated with what the CLASS declares in its
xml_schema, and KillingAttackRanged does not declare KILLING at all -- so the
`stated` set would be empty, the template would win unconditionally, and these
tests would pass without ever exercising the guard they exist to test.
"""
from __future__ import annotations

from kirby_cost.objects.powers.custom_power import CustomPower
from kirby_cost.template.dataclasses import TemplateData


def _power_that_states(attribute: str) -> CustomPower:
    """An object whose SOURCE stated *attribute*, as a loaded .hdc would."""
    power = CustomPower()
    power._source_attr_order = [attribute]
    power._source_attrs = frozenset([attribute])
    return power


def test_the_guard_is_actually_reachable():
    """Guards the guard. If CustomPower ever stopped declaring KILLING in its
    xml_schema, every test below would pass vacuously -- the template would
    win because `stated` was empty, not because precedence worked."""
    assert "KILLING" in {d.attr for d in CustomPower.xml_schema()}
    assert "KILLING" in _power_that_states("KILLING")._stated_and_declared()


def test_without_a_campaign_a_stated_value_still_wins():
    power = _power_that_states("KILLING")
    power.killing = True
    power.apply_template(TemplateData(xmlid="CUSTOMPOWER", killing=False))
    assert power.killing is True, "the document's own value must still win by default"


def test_a_campaign_forced_value_beats_the_stated_one():
    power = _power_that_states("KILLING")
    power.killing = True
    power.apply_template(TemplateData(
        xmlid="CUSTOMPOWER", killing=False, campaign_forced=frozenset({"killing"})))
    assert power.killing is False


def test_a_campaign_does_not_free_attributes_it_did_not_force():
    """Forcing `killing` must not also let the template overwrite a stated
    DEFENSE -- the exemption is per attribute, not per object."""
    power = _power_that_states("DEFENSE")
    power.defense = "MENTAL"
    power.apply_template(TemplateData(
        xmlid="CUSTOMPOWER", defense="NORMAL", killing=False,
        campaign_forced=frozenset({"killing"})))
    assert power.defense == "MENTAL"


def test_uses_end_is_forceable_despite_its_irregular_xml_name():
    """`uses_end` is gated on the XML name "END", not the derived "USESEND".
    CustomPower declares END in its schema (same trap as KILLING/DEFENSE
    above), so this reaches the real guard rather than passing vacuously.

    Unlike killing/defense, this field is only ever SET to True by
    apply_template (`if tmpl.uses_end and "END" not in stated: self.uses_end
    = True`) -- it never assigns False. So the document-wins scenario is a
    source that explicitly stated END="No" (uses_end False) with a template
    that says True: the "END" in stated guard normally protects that explicit
    "No" from the template. Forcing "uses_end" must let the campaign's
    template value win instead.

    Before _XML_NAME_OVERRIDES existed, forcing "uses_end" subtracted the
    derived "USESEND" -- a name never in `stated` -- so "END" survived in the
    guard and the document's stated "No" silently kept beating the campaign
    and the template's True."""
    assert "END" in {d.attr for d in CustomPower.xml_schema()}
    power = _power_that_states("END")
    power.uses_end = False
    power.apply_template(TemplateData(
        xmlid="CUSTOMPOWER", uses_end=True,
        campaign_forced=frozenset({"uses_end"})))
    assert power.uses_end is True


def test_a_forced_defense_beats_a_stated_one():
    """The `stated` subtraction alone is not enough. Each of DEFENSE, TARGET
    and RANGE carried a SECOND guard on the object's CURRENT value ("only if
    empty", "only if N/A", "only if blank"), and a document that stated
    MENTAL leaves `self.defense` non-empty -- so the forced NORMAL was
    dropped even with "DEFENSE" removed from `stated`. Measured before the
    fix: forced NORMAL over stated MENTAL came back MENTAL."""
    power = _power_that_states("DEFENSE")
    power.defense = "MENTAL"
    power.apply_template(TemplateData(
        xmlid="CUSTOMPOWER", defense="NORMAL",
        campaign_forced=frozenset({"defense"})))
    assert power.defense == "NORMAL"


def test_a_forced_target_beats_a_stated_one():
    """Same second guard as DEFENSE: `self.target in ("", "N/A")`. Measured
    before the fix: forced SELFONLY over stated DCV came back DCV."""
    power = _power_that_states("TARGET")
    power.target = "DCV"
    power.apply_template(TemplateData(
        xmlid="CUSTOMPOWER", target="SELFONLY",
        campaign_forced=frozenset({"target"})))
    assert power.target == "SELFONLY"


def test_a_forced_range_beats_a_stated_one():
    """Same second guard again: `not (self.range or "").strip()`. Measured
    before the fix: forced LOS over an existing 'No' came back 'No' -- a GM
    who makes a power ranged got nothing."""
    power = _power_that_states("RANGE")
    power.range = "No"
    power.apply_template(TemplateData(
        xmlid="CUSTOMPOWER", range="LOS",
        campaign_forced=frozenset({"range"})))
    assert power.range == "LOS"


def test_a_forced_uses_end_can_turn_endurance_OFF():
    """The True direction was already covered; the False direction was a
    guaranteed no-op, because the branch only ever assigned True
    (`if tmpl.uses_end and "END" not in stated: self.uses_end = True`). A GM
    who makes a power cost no END must get that, not silence."""
    power = _power_that_states("END")
    power.uses_end = True
    power.apply_template(TemplateData(
        xmlid="CUSTOMPOWER", uses_end=False,
        campaign_forced=frozenset({"uses_end"})))
    assert power.uses_end is False


def test_a_forced_uses_end_off_works_on_a_document_that_said_nothing():
    """Not only against a stated END: an object that never stated END at all
    must also honour a campaign that turns endurance off."""
    power = CustomPower()
    power.uses_end = True
    power.apply_template(TemplateData(
        xmlid="CUSTOMPOWER", uses_end=False,
        campaign_forced=frozenset({"uses_end"})))
    assert power.uses_end is False
