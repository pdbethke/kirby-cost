"""Tests for kirby_cost.template dataclasses and apply_template methods."""
import pytest

from kirby_cost.template.dataclasses import (
    AdderTemplate,
    OptionTemplate,
    TemplateData,
)
from kirby_cost.objects.adder import Adder


class TestOptionTemplate:
    def test_defaults(self):
        opt = OptionTemplate(xmlid="ENERGY")
        assert opt.xmlid == "ENERGY"
        assert opt.base_cost == 0.0
        assert opt.level_cost == 0.0
        assert opt.level_multiplier == 1

    def test_frozen(self):
        opt = OptionTemplate(xmlid="X")
        with pytest.raises(AttributeError):
            opt.xmlid = "Y"


class TestAdderTemplate:
    def test_with_types(self):
        a = AdderTemplate(xmlid="COMMONMELEE", types=("HTH",))
        assert a.types == ("HTH",)

    def test_defaults(self):
        a = AdderTemplate(xmlid="PLUSONEHALFDIE", display="+1/2 d6", base_cost=3.0)
        assert a.base_cost == 3.0
        assert a.types == ()


class TestTemplateData:
    def test_from_dict_simple(self):
        raw = {
            "display": "Acrobatics",
            "base_cost": 0.0,
            "level_cost": 2.0,
            "level_value": 1.0,
            "level_power": 1,
            "level_multiplier": 1,
            "minimum_cost": 1.0,
            "min_set": True,
            "max_cost": 0.0,
            "max_set": False,
            "uses_end": False,
            "duration": "CONSTANT",
            "target": "SELFONLY",
            "is_power": False,
            "options": {},
            "adders": {},
        }
        td = TemplateData.from_dict("ACROBATICS", raw)
        assert td.xmlid == "ACROBATICS"
        assert td.display == "Acrobatics"
        assert td.level_cost == 2.0
        assert td.minimum_cost == 1.0
        assert td.min_set is True
        assert td.adders == {}
        assert td.options == {}

    def test_from_dict_with_options(self):
        raw = {
            "display": "Absorption",
            "level_cost": 1.0,
            "level_value": 1.0,
            "min_set": True,
            "options": {
                "ENERGY": {
                    "display": "energy",
                    "level_cost": 1.0,
                    "level_value": 1.0,
                },
                "PHYSICAL": {
                    "display": "physical",
                    "level_cost": 1.0,
                    "level_value": 1.0,
                },
            },
            "adders": {},
        }
        td = TemplateData.from_dict("ABSORPTION", raw)
        assert len(td.options) == 2
        assert td.options["ENERGY"].display == "energy"
        assert isinstance(td.options["ENERGY"], OptionTemplate)

    def test_from_dict_with_adders(self):
        raw = {
            "display": "Aid",
            "level_cost": 6.0,
            "options": {},
            "adders": {
                "PLUSONEHALFDIE": {
                    "display": "+1/2 d6",
                    "base_cost": 3.0,
                    "level_cost": 0.0,
                    "level_value": -1.0,
                },
                "PLUSONEPIP": {
                    "display": "+1 pip",
                    "base_cost": 2.0,
                },
            },
        }
        td = TemplateData.from_dict("AID", raw)
        assert len(td.adders) == 2
        assert td.adders["PLUSONEHALFDIE"].base_cost == 3.0
        assert isinstance(td.adders["PLUSONEHALFDIE"], AdderTemplate)

    def test_from_dict_with_types_on_adder(self):
        raw = {
            "display": "Weapon Familiarity",
            "options": {},
            "adders": {
                "COMMONMELEE": {
                    "display": "Common Melee",
                    "base_cost": 1.0,
                    "types": ["HTH"],
                },
            },
        }
        td = TemplateData.from_dict("WEAPON_FAMILIARITY", raw)
        assert td.adders["COMMONMELEE"].types == ("HTH",)

    def test_from_dict_with_option_aliases(self):
        raw = {
            "display": "Enhanced Perception",
            "level_cost": 3.0,
            "options": {"ALL": {"display": "all", "level_cost": 3.0}},
            "adders": {},
            "option_aliases": {"*ALLSENSES": "ALL"},
        }
        td = TemplateData.from_dict("ENHANCEDPERCEPTION", raw)
        assert td.option_aliases == {"*ALLSENSES": "ALL"}

    def test_frozen(self):
        td = TemplateData(xmlid="X")
        with pytest.raises(AttributeError):
            td.xmlid = "Y"


class TestApplyTemplate:
    """Test GenericObject.apply_template and Adder.apply_adder_template."""

    def test_apply_template_basic(self):
        a = Adder()
        td = TemplateData(
            xmlid="TEST", level_cost=2.0, level_value=1.0,
            min_set=True, minimum_cost=1.0,
            duration="CONSTANT", target="SELFONLY",
        )
        a.apply_template(td)
        assert a.level_cost == 2.0
        assert a.level_value == 1.0
        assert a.min_set is True
        assert a.minimum_cost == 1.0
        assert a.duration == "CONSTANT"
        assert a.target == "SELFONLY"

    def test_apply_template_option_overrides(self):
        a = Adder()
        td = TemplateData(
            xmlid="TEST", level_cost=3.0,
            options={
                "SINGLE": OptionTemplate(xmlid="SINGLE", level_cost=1.0, level_value=1.0),
            },
        )
        a.apply_template(td, option_id="SINGLE")
        assert a.level_cost == 1.0  # option wins

    def test_apply_template_option_alias(self):
        a = Adder()
        td = TemplateData(
            xmlid="TEST", level_cost=3.0,
            options={
                "ALL": OptionTemplate(xmlid="ALL", level_cost=3.0),
            },
            option_aliases={"*ALLSENSES": "ALL"},
        )
        a.apply_template(td, option_id="FOOALLSENSES")
        assert a.level_cost == 3.0  # resolved via wildcard alias

    def test_apply_template_option_overrides_level_multiplier(self):
        """Option with level_multiplier=1 must override base template level_multiplier=2."""
        a = Adder()
        td = TemplateData(
            xmlid="AOE", level_multiplier=2, level_power=2,
            options={
                "SURFACE": OptionTemplate(xmlid="SURFACE", level_cost=0.25,
                                          level_value=1.0, level_power=2,
                                          level_multiplier=1),
            },
        )
        a.apply_template(td, option_id="SURFACE")
        assert a.level_multiplier == 1  # option wins, not base template's 2
        assert a.level_power == 2

    def test_apply_template_xml_base_cost_preserved(self):
        a = Adder()
        a.orig_base_cost = 5.0  # simulate XML-set base cost
        td = TemplateData(
            xmlid="TEST",
            options={
                "OPT": OptionTemplate(xmlid="OPT", base_cost=10.0),
            },
        )
        a.apply_template(td, option_id="OPT")
        assert a.base_cost == 0.0  # orig_base_cost != 0, so option base_cost is ignored

    def test_apply_template_no_min_set_clears(self):
        a = Adder()
        a.min_set = True
        a.minimum_cost = 5.0
        td = TemplateData(xmlid="TEST", min_set=False)
        a.apply_template(td)
        assert a.min_set is False
        assert a.minimum_cost == 0.0

    def test_apply_template_uses_end(self):
        a = Adder()
        td = TemplateData(xmlid="TEST", uses_end=True)
        a.apply_template(td)
        assert a.uses_end is True

    def test_apply_adder_template_basic(self):
        a = Adder()
        at = AdderTemplate(xmlid="PLUSONEHALFDIE", base_cost=3.0, types=("RANGED",))
        a.apply_adder_template(at)
        assert a.base_cost == 3.0
        assert a.types == ["RANGED"]

    def test_apply_adder_template_preserves_xml(self):
        a = Adder()
        a._base_cost_from_xml = True
        a.base_cost = 5.0
        at = AdderTemplate(xmlid="X", base_cost=10.0)
        a.apply_adder_template(at)
        assert a.base_cost == 5.0  # XML value preserved

    def test_apply_adder_template_level_fields(self):
        a = Adder()
        at = AdderTemplate(xmlid="X", level_cost=2.0, level_value=3.0, level_power=2, level_multiplier=5)
        a.apply_adder_template(at)
        assert a.level_cost == 2.0
        assert a.level_value == 3.0
        assert a.level_power == 2
        assert a.level_multiplier == 5


    def test_from_a_real_template_file(self):
        """Smoke test: every entry of a real ``.hdt`` becomes a TemplateData.

        Reads the template the suite is configured with rather than a bundled
        one -- the package ships no template data.
        """
        import os

        from kirby_cost.template.hdt_provider import HDTTemplateProvider

        if not os.environ.get(HDTTemplateProvider.ENV_VAR):
            pytest.skip(f"no template configured ({HDTTemplateProvider.ENV_VAR})")

        provider = HDTTemplateProvider()
        assert len(provider) > 100  # sanity: a real template is a catalogue
        for xmlid in list(provider._index):
            td = provider.get_template_data(xmlid)
            assert td is not None
            assert td.xmlid == xmlid
