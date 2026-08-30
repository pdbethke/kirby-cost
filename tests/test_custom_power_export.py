"""CustomPower's exported DOESBODY/DOESKNOCKBACK/DURATION are the FIELDS,
not the computed properties.

CustomPower.java:280-289 (``getSaveXML``) writes ``doesBODY``,
``doesKnockback`` and ``duration`` -- the raw fields -- unconditionally,
never ``getDuration()``/``doesBODY()`` (the methods other objects consult,
which NND, AVAD, STUN Only and friends rewrite). This branch turned
``GenericObject.duration``/``does_body``/``does_knockback`` into computed
properties over ``orig_duration``/``orig_does_body``/``orig_does_knockback``,
which silently switched CustomPower's exporter onto the wrong half of that
split: a custom NND blast bought as DOESBODY="Yes" started re-exporting
DOESBODY="No", because ``does_body`` (the property) answers "does an NND
attack do BODY", not "what did the document say".
"""
from kirby_cost.objects.modifiers.nnd import NND
from kirby_cost.objects.powers.custom_power import CustomPower


def _custom_power() -> CustomPower:
    power = CustomPower()
    power.levels = 1
    return power


def test_export_reports_the_document_fields_not_the_computed_ones():
    power = _custom_power()
    power.orig_duration = "PERSISTENT"
    power.orig_does_body = True
    power.orig_does_knockback = True
    power.uses_end = True
    power._assigned_modifiers.append(NND())

    # An NND attack computes does_body/does_knockback False regardless of
    # what was stated -- that is the whole point of the modifier.
    assert power.does_body is False
    assert power.does_knockback is False
    # And PERSISTENT + usesEND with no COSTSENDTOMAINTAIN reports CONSTANT.
    assert power.duration == "CONSTANT"

    element = power.get_save_xml()
    assert element.get("DURATION") == "PERSISTENT"
    assert element.get("DOESBODY") == "Yes"
    assert element.get("DOESKNOCKBACK") == "Yes"


def test_a_blank_duration_does_not_export_as_instant():
    # A power whose document-stated duration was cleared to "" -- distinct
    # from CustomPower's own constructor default of "INSTANT" (Power.__init__
    # / CustomPower.java's init() both set it explicitly). The COMPUTED
    # `duration` property answers "INSTANT" for a blank field (base.py's
    # `return "INSTANT"` fallthrough); the exported attribute must not, or
    # every custom power with a genuinely empty duration re-saves lying
    # about what the document said.
    power = _custom_power()
    power.orig_duration = ""
    assert power.duration == "INSTANT"  # the computed property, unaffected
    element = power.get_save_xml()
    assert element.get("DURATION") != "INSTANT"
