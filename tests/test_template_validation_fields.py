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


def test_exclusive_defaults_true_when_the_attribute_is_absent():
    # GenericObject.java:3054 initialises `exclusive = true` before the
    # element is even read, and :3106-3111 clears it ONLY when EXCLUSIVE
    # starts with "N" -- an absent attribute means exclusive. NOKB carries
    # no EXCLUSIVE attribute at all.
    d = HDTTemplateProvider().get_template_data("NOKB", section="modifiers")
    assert d.attributes.get("EXCLUSIVE") is None
    assert d.exclusive is True


def test_exclusive_false_only_when_the_attribute_starts_with_n():
    d = HDTTemplateProvider().get_template_data("DOUBLEKB", section="modifiers")
    assert d.attributes.get("EXCLUSIVE") == "No"
    assert d.exclusive is False


def test_exclusive_true_when_the_attribute_says_yes():
    d = HDTTemplateProvider().get_template_data("HALFRANGEMODIFIER")
    assert d.exclusive is True


def test_modifiers_lists_only_the_modifiers_section_in_template_order():
    provider = HDTTemplateProvider()
    mods = provider.modifiers()
    assert len(mods) == 157
    assert all(isinstance(d.xmlid, str) and d.xmlid for d in mods)
    # Every entry actually resolves back to a "modifiers"-section row --
    # not, say, a skill-section entry such as COMBAT_LEVELS that merely
    # sounds like one.
    for d in mods:
        assert provider.get_template_data(d.xmlid, section="modifiers") is not None


def test_the_modifier_exclusive_split_main6e_states():
    # A regression fence: if a regenerated Main6E.hdt ever changes how many
    # modifiers say EXCLUSIVE="Yes" / "No" / say nothing, this notices.
    provider = HDTTemplateProvider()
    mods = provider.modifiers()
    yes = [d.xmlid for d in mods if d.attributes.get("EXCLUSIVE", "").upper().startswith("Y")]
    no = [d.xmlid for d in mods if d.attributes.get("EXCLUSIVE", "").upper().startswith("N")]
    absent = [d.xmlid for d in mods if "EXCLUSIVE" not in d.attributes]
    assert (len(yes), len(no), len(absent)) == (119, 8, 30)
    # Every one of the "No" modifiers must actually resolve exclusive=False,
    # and everything else (Yes or absent) must resolve exclusive=True.
    for d in mods:
        if d.xmlid in no:
            assert d.exclusive is False, d.xmlid
        else:
            assert d.exclusive is True, d.xmlid
