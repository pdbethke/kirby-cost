"""
Metadata round-trip test: verify all character info fields survive
load -> export -> reload cycle.
"""

import tempfile
import os
import pytest
from pathlib import Path
from lxml import etree

from kirby_cost.io.hdc_loader import HDCLoader, LoadedHero

# The .hdc files are the maintainer's own characters, bundled in
# ``tests/fixtures/authored/``. Bokor has a written background but no other
# prose, so the "populated biography" tests run on a temporary copy of Bokor
# whose personality / tactics / campaign-use / appearance text is filled in.
BOKOR_BIO = {
    "PERSONALITY": "Patient, courtly and quietly unforgiving of broken promises.",
    "TACTICS": "Lets the powders do the work and keeps the crowd between him and trouble.",
    "CAMPAIGN_USE": "A contact in the Port-au-Prince underworld, or an uneasy ally.",
    "APPEARANCE": "Very tall and very broad, bald, in a white linen suit and dark glasses.",
}


def _bokor_with_bio(tmp_path: Path) -> str:
    """A temporary copy of Bokor with the biography fields populated."""
    from tests.corpus import require_authored_hdc
    root = etree.parse(str(require_authored_hdc("Bokor"))).getroot()
    info = root.find("CHARACTER_INFO")
    for tag, text in BOKOR_BIO.items():
        info.find(tag).text = text
    out = tmp_path / "Bokor-bio.hdc"
    out.write_bytes(etree.tostring(root, xml_declaration=True, encoding="UTF-8"))
    return str(out)


def _ravel() -> str:
    from tests.corpus import require_authored_hdc
    return str(require_authored_hdc("Ravel"))


def _export_hero_xml(hero: LoadedHero) -> bytes:
    """Export a LoadedHero to HDC XML bytes."""
    root = etree.Element("CHARACTER")
    root.set("TEMPLATE", hero.template_name or "Main6E.hdt")
    root.set("version", "6.0")

    # Basic configuration
    basic_config = etree.SubElement(root, "BASIC_CONFIGURATION")
    basic_config.set("BASE_POINTS", str(hero.base_points))
    basic_config.set("DISAD_POINTS", str(hero.disad_points))
    basic_config.set("EXPERIENCE", str(hero.experience))
    basic_config.set("RULES", "Default")

    # Character info
    info = etree.SubElement(root, "CHARACTER_INFO")
    info.set("CHARACTER_NAME", hero.name or "")
    info.set("ALTERNATE_IDENTITIES", hero.alternate_identities or "")
    info.set("PLAYER_NAME", hero.player_name or "")
    info.set("HEIGHT", str(hero.height))
    info.set("WEIGHT", str(hero.weight))
    info.set("HAIR_COLOR", hero.hair_color or "")
    info.set("EYE_COLOR", hero.eye_color or "")
    info.set("CAMPAIGN_NAME", hero.campaign_name or "")
    info.set("GENRE", hero.genre or "")
    info.set("GM", hero.gm or "")

    for field in ("BACKGROUND", "PERSONALITY", "QUOTE", "TACTICS",
                  "CAMPAIGN_USE", "APPEARANCE",
                  "NOTES1", "NOTES2", "NOTES3", "NOTES4", "NOTES5"):
        child = etree.SubElement(info, field)
        val = getattr(hero, field.lower(), "")
        if val:
            child.text = val

    # Image
    if hero.image_data:
        image_elem = etree.SubElement(root, "IMAGE")
        image_elem.set("FILENAME", hero.image_filename or "")
        image_elem.text = hero.image_data

    # Rules
    rules_elem = etree.SubElement(root, "RULES")
    if hero.rules and hero.rules._language_similarities_used:
        rules_elem.set("LANGUAGESIMILARITIESUSED", "Yes")

    # Sections
    for tag, objects in [
        ("CHARACTERISTICS", hero.characteristics),
        ("POWERS", hero.powers),
        ("SKILLS", hero.skills),
        ("PERKS", hero.perks),
        ("TALENTS", hero.talents),
        ("DISADVANTAGES", hero.complications),
    ]:
        section = etree.SubElement(root, tag)
        for obj in objects:
            try:
                elem = obj.get_save_xml()
                if elem is not None:
                    section.append(elem)
            except Exception:
                pass

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)


def _roundtrip(hdc_path: str) -> tuple[LoadedHero, LoadedHero]:
    """Load, export, reload — return both heroes."""
    loader = HDCLoader()
    hero1 = loader.load_file(hdc_path)
    xml_bytes = _export_hero_xml(hero1)

    tmp = tempfile.NamedTemporaryFile(suffix=".hdc", delete=False, mode="wb")
    tmp.write(xml_bytes)
    tmp.close()

    try:
        loader2 = HDCLoader()
        hero2 = loader2.load_file(tmp.name)
    finally:
        os.unlink(tmp.name)

    return hero1, hero2


# ── Metadata field lists for DRY assertions ─────────────────

_STR_ATTRS = [
    "name", "player_name", "alternate_identities", "campaign_name",
    "genre", "gm", "hair_color", "eye_color",
]
_TEXT_FIELDS = [
    "appearance", "background", "personality", "quote",
    "tactics", "campaign_use",
    "notes1", "notes2", "notes3", "notes4", "notes5",
]
_INT_ATTRS = ["base_points", "disad_points", "experience"]
_FLOAT_ATTRS = ["height", "weight"]


class TestLoadMetadata:
    """Verify metadata is parsed from HDC files."""

    @pytest.fixture
    def bokor(self, tmp_path):
        return HDCLoader().load_file(_bokor_with_bio(tmp_path))

    @pytest.fixture
    def ravel(self):
        return HDCLoader().load_file(_ravel())

    def test_name(self, bokor):
        assert bokor.name == "Bokor"

    def test_template_name(self, bokor):
        assert "Heroic6E" in bokor.template_name

    def test_base_points(self, bokor):
        assert bokor.base_points == 270

    def test_disad_points(self, bokor):
        assert bokor.disad_points == 40

    def test_experience(self, bokor):
        assert bokor.experience == 5

    def test_height_nonzero(self, bokor):
        assert bokor.height > 0.0

    def test_weight_nonzero(self, bokor):
        assert bokor.weight > 0.0

    def test_hair_color(self, bokor):
        assert bokor.hair_color == "Bald"

    def test_eye_color(self, bokor):
        assert bokor.eye_color == "Brown"

    def test_background_populated(self, bokor):
        assert "gonaives" in bokor.background.lower()

    def test_personality_populated(self, bokor):
        assert len(bokor.personality) > 10

    def test_tactics_populated(self, bokor):
        assert len(bokor.tactics) > 10

    def test_campaign_use_populated(self, bokor):
        assert len(bokor.campaign_use) > 10

    def test_appearance_populated(self, bokor):
        assert len(bokor.appearance) > 10

    def test_ravel_base_points(self, ravel):
        assert ravel.base_points == 400

    def test_ravel_experience(self, ravel):
        assert ravel.experience == 50

    def test_empty_fields_default(self, ravel):
        # These are empty in Ravel's HDC
        assert ravel.campaign_name == ""
        assert ravel.personality == ""
        assert ravel.background == ""


class TestMetadataRoundtrip:
    """Verify metadata survives load -> export -> reload."""

    @pytest.fixture
    def bokor_roundtrip(self, tmp_path):
        return _roundtrip(_bokor_with_bio(tmp_path))

    @pytest.fixture
    def ravel_roundtrip(self):
        return _roundtrip(_ravel())

    def test_str_attrs_roundtrip(self, bokor_roundtrip):
        hero1, hero2 = bokor_roundtrip
        for attr in _STR_ATTRS:
            assert getattr(hero2, attr) == getattr(hero1, attr), (
                f"{attr}: {getattr(hero2, attr)!r} != {getattr(hero1, attr)!r}"
            )

    def test_text_fields_roundtrip(self, bokor_roundtrip):
        hero1, hero2 = bokor_roundtrip
        for field in _TEXT_FIELDS:
            assert getattr(hero2, field) == getattr(hero1, field), (
                f"{field}: {getattr(hero2, field)!r} != {getattr(hero1, field)!r}"
            )

    def test_int_attrs_roundtrip(self, bokor_roundtrip):
        hero1, hero2 = bokor_roundtrip
        for attr in _INT_ATTRS:
            assert getattr(hero2, attr) == getattr(hero1, attr), (
                f"{attr}: {getattr(hero2, attr)} != {getattr(hero1, attr)}"
            )

    def test_float_attrs_roundtrip(self, bokor_roundtrip):
        hero1, hero2 = bokor_roundtrip
        for attr in _FLOAT_ATTRS:
            assert abs(getattr(hero2, attr) - getattr(hero1, attr)) < 0.01, (
                f"{attr}: {getattr(hero2, attr)} != {getattr(hero1, attr)}"
            )

    def test_ravel_str_attrs_roundtrip(self, ravel_roundtrip):
        hero1, hero2 = ravel_roundtrip
        for attr in _STR_ATTRS:
            assert getattr(hero2, attr) == getattr(hero1, attr), (
                f"{attr}: {getattr(hero2, attr)!r} != {getattr(hero1, attr)!r}"
            )

    def test_ravel_int_attrs_roundtrip(self, ravel_roundtrip):
        hero1, hero2 = ravel_roundtrip
        for attr in _INT_ATTRS:
            assert getattr(hero2, attr) == getattr(hero1, attr), (
                f"{attr}: {getattr(hero2, attr)} != {getattr(hero1, attr)}"
            )

    def test_template_name_roundtrip(self, bokor_roundtrip):
        hero1, hero2 = bokor_roundtrip
        assert hero2.template_name == hero1.template_name


class TestSyntheticRoundtrip:
    """Round-trip with a fully-populated synthetic HDC to cover all fields."""

    def test_all_fields_survive(self):
        xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<CHARACTER version="6.0" TEMPLATE="builtIn.Superheroic6E.hdt">
  <BASIC_CONFIGURATION BASE_POINTS="350" DISAD_POINTS="60" EXPERIENCE="42" RULES="Default" />
  <CHARACTER_INFO CHARACTER_NAME="Test Hero" ALTERNATE_IDENTITIES="Secret ID"
                  PLAYER_NAME="Jane Doe" HEIGHT="66.5" WEIGHT="130.0"
                  HAIR_COLOR="Red" EYE_COLOR="Green"
                  CAMPAIGN_NAME="Test Campaign" GENRE="Superhero" GM="John GM">
    <BACKGROUND>Raised by wolves.</BACKGROUND>
    <PERSONALITY>Brave and stubborn.</PERSONALITY>
    <QUOTE>Never give up!</QUOTE>
    <TACTICS>Hit them hard.</TACTICS>
    <CAMPAIGN_USE>Good NPC villain.</CAMPAIGN_USE>
    <APPEARANCE>Tall with red hair.</APPEARANCE>
    <NOTES1>Note one.</NOTES1>
    <NOTES2>Note two.</NOTES2>
    <NOTES3>Note three.</NOTES3>
    <NOTES4>Note four.</NOTES4>
    <NOTES5>Note five.</NOTES5>
  </CHARACTER_INFO>
  <IMAGE FILENAME="hero.jpg">aGVsbG8=</IMAGE>
  <CHARACTERISTICS />
  <POWERS />
  <SKILLS />
  <PERKS />
  <TALENTS />
  <DISADVANTAGES />
</CHARACTER>"""
        tmp = tempfile.NamedTemporaryFile(suffix=".hdc", delete=False, mode="wb")
        tmp.write(xml)
        tmp.close()

        try:
            loader = HDCLoader()
            hero = loader.load_file(tmp.name)
        finally:
            os.unlink(tmp.name)

        # Verify all fields loaded
        assert hero.name == "Test Hero"
        assert hero.player_name == "Jane Doe"
        assert hero.alternate_identities == "Secret ID"
        assert hero.campaign_name == "Test Campaign"
        assert hero.genre == "Superhero"
        assert hero.gm == "John GM"
        assert hero.base_points == 350
        assert hero.disad_points == 60
        assert hero.experience == 42
        assert abs(hero.height - 66.5) < 0.01
        assert abs(hero.weight - 130.0) < 0.01
        assert hero.hair_color == "Red"
        assert hero.eye_color == "Green"
        assert hero.background == "Raised by wolves."
        assert hero.personality == "Brave and stubborn."
        assert hero.quote == "Never give up!"
        assert hero.tactics == "Hit them hard."
        assert hero.campaign_use == "Good NPC villain."
        assert hero.appearance == "Tall with red hair."
        assert hero.notes1 == "Note one."
        assert hero.notes2 == "Note two."
        assert hero.notes3 == "Note three."
        assert hero.notes4 == "Note four."
        assert hero.notes5 == "Note five."
        assert hero.image_data == "aGVsbG8="
        assert hero.image_filename == "hero.jpg"

        # Now round-trip
        xml_bytes = _export_hero_xml(hero)
        tmp2 = tempfile.NamedTemporaryFile(suffix=".hdc", delete=False, mode="wb")
        tmp2.write(xml_bytes)
        tmp2.close()

        try:
            hero2 = HDCLoader().load_file(tmp2.name)
        finally:
            os.unlink(tmp2.name)

        # All fields survived
        for attr in _STR_ATTRS:
            assert getattr(hero2, attr) == getattr(hero, attr), attr
        for field in _TEXT_FIELDS:
            assert getattr(hero2, field) == getattr(hero, field), field
        for attr in _INT_ATTRS:
            assert getattr(hero2, attr) == getattr(hero, attr), attr
        for attr in _FLOAT_ATTRS:
            assert abs(getattr(hero2, attr) - getattr(hero, attr)) < 0.01, attr
        assert hero2.image_data == hero.image_data
        assert hero2.image_filename == hero.image_filename
