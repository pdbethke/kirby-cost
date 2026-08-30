"""A modifier built from the template knows what the template says about it."""
from tests.matrix_support import template_modifier, template_power


def test_a_template_modifier_carries_its_types():
    assert template_modifier("ZEROPHASE")._types == ["VPP"]


def test_a_template_modifier_carries_its_excludes():
    assert template_modifier("HALFRANGEMODIFIER")._excludes == ("LOS", "NORANGEMODIFIER")


def test_a_template_power_carries_its_types():
    assert list(template_power("ENERGYBLAST").types) == ["STANDARD", "ATTACK"]


def test_the_hand_table_is_gone():
    import kirby_cost.io.hdc_loader as loader
    assert not hasattr(loader, "_MODIFIER_TYPES")


def test_the_template_types_nine_modifiers_as_framework_bound():
    """The loader's hand table listed three (HALFPHASE, NOSKILLROLL, ZEROPHASE)
    as VPP-typed. The template types nine. Cost parity did not move when the
    other six (COSMIC, LIMITED, NOCHOICE, NOCHOICEWHENORHOW,
    ONLYBETWEENADVENTURES, ONLYINGIVENCIRCUMSTANCE) became typed -- which
    means no corpus character exercises their VPP cost path, and their
    behaviour under that typing is oracle-unverified. A candidate for the
    kitchen-sink character, tests/kitchen_sink.py."""
    from kirby_cost.template.hdt_provider import HDTTemplateProvider
    p = HDTTemplateProvider()
    framework_typed = sorted(
        x for (section, x), d in p._by_section.items()
        if section == "modifiers" and set(d.types) & {"VPP", "MP", "EC", "LIST"})
    assert framework_typed == [
        "COSMIC", "HALFPHASE", "LIMITED", "NOCHOICE", "NOCHOICEWHENORHOW",
        "NOSKILLROLL", "ONLYBETWEENADVENTURES", "ONLYINGIVENCIRCUMSTANCE",
        "ZEROPHASE",
    ], framework_typed
