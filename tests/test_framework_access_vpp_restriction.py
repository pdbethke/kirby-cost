"""VPP SFX-restriction text accessor.

The kirby-api category extractor reads this string to decide what a pool is
allowed to conjure. It is descriptive text only — no cost math lives here.
"""
from types import SimpleNamespace

from kirby_cost.io.framework_access import vpp_restriction_text


def _vpp(name="", input_="", mods=None):
    # Minimal duck-typed stand-in for a loaded VPP GenericObject.
    return SimpleNamespace(
        xmlid="GENERIC_OBJECT", alias="Variable Power Pool",
        name=name, input=input_, levels=80,
        assigned_modifiers=mods or [],
    )


def _lim(alias):
    return SimpleNamespace(xmlid="LIMITEDPOWER", alias=alias, input="", comments="")


def test_restriction_text_combines_input_name_and_limitation(monkeypatch):
    import kirby_cost.io.framework_access as fa
    monkeypatch.setattr(fa, "is_vpp", lambda f: True)
    fw = _vpp(name="Improved Thaumaturgy", input_="Magic Pool",
              mods=[_lim("Only Fire/Heat Powers")])
    text = vpp_restriction_text(fw)
    assert "Magic Pool" in text
    assert "Improved Thaumaturgy" in text
    assert "Only Fire/Heat Powers" in text


def test_restriction_text_empty_when_not_vpp(monkeypatch):
    import kirby_cost.io.framework_access as fa
    monkeypatch.setattr(fa, "is_vpp", lambda f: False)
    assert vpp_restriction_text(_vpp()) == ""


def test_restriction_text_empty_when_no_descriptive_text(monkeypatch):
    import kirby_cost.io.framework_access as fa
    monkeypatch.setattr(fa, "is_vpp", lambda f: True)
    assert vpp_restriction_text(_vpp()) == ""


def test_restriction_text_dedupes_repeated_parts(monkeypatch):
    import kirby_cost.io.framework_access as fa
    monkeypatch.setattr(fa, "is_vpp", lambda f: True)
    fw = _vpp(name="Magic Pool", input_="Magic Pool",
              mods=[_lim("Magic Pool")])
    assert vpp_restriction_text(fw) == "Magic Pool"


def test_restriction_text_ignores_non_limitedpower_modifiers(monkeypatch):
    import kirby_cost.io.framework_access as fa
    monkeypatch.setattr(fa, "is_vpp", lambda f: True)
    other = SimpleNamespace(xmlid="REQUIRESASKILLROLL", alias="Requires A Roll",
                            input="", comments="")
    fw = _vpp(input_="Magic Pool", mods=[other])
    assert vpp_restriction_text(fw) == "Magic Pool"
