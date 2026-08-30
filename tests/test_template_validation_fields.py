"""The template states applicability as data; the model has to carry it.

Main6E.hdt says <EXCLUDES>LOS</EXCLUDES> under HALFRANGEMODIFIER and
<REQUIRES>RIDINGANIMALS</REQUIRES> under the CARTSANDCARRIAGES adder. The
parser already yields both as child_elements; the provider dropped them.
"""
from kirby_cost.template.hdt_provider import HDTTemplateProvider


def test_excludes_is_read_from_the_template():
    d = HDTTemplateProvider().get_template_data("HALFRANGEMODIFIER")
    assert d.excludes == ("LOS", "NORANGEMODIFIER")


def test_subject_to_range_modifier_excludes():
    # The plan's original expectation listed only the first two; the template
    # actually carries four <EXCLUDES> children, in this order.
    d = HDTTemplateProvider().get_template_data("SUBJECTTORANGEMODIFIER")
    assert d.excludes == ("NORANGE", "LIMITEDRANGE", "REDUCEDBYRANGE", "RANGEBASEDONSTR")


def test_a_modifier_with_no_excludes_has_an_empty_tuple():
    d = HDTTemplateProvider().get_template_data("ARMORPIERCING")
    assert d.excludes == ()
    assert d.requires == ()
    assert d.requires_all is False


def test_exclusive_is_reachable_through_attributes():
    d = HDTTemplateProvider().get_template_data("HALFRANGEMODIFIER")
    assert d.attributes.get("EXCLUSIVE") == "Yes"
