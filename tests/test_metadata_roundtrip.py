"""
Metadata round-trip test: verify all character info fields survive
load -> export -> reload cycle.
"""

import json
import tempfile
import os
import pytest
from pathlib import Path
from lxml import etree

from kirby_cost.io.hdc_loader import HDCLoader, LoadedHero

# The .hdc files live outside this repo — they are published Hero Games
# content, never vendored. Their location is already recorded once, in the
# oracle fixtures' ``hdc_path``, which ``scripts/generate_oracle_fixtures.py``
# derives from the workspace root. Read it from there rather than walking for
# an ancestor directory by name: this file looked for one called "Champions
# Campaign Manager", the workspace was renamed to Kirby, and the walk ran off
# the top and produced "/the character-pack checkout/..." — 24 tests erroring
# at setup on a path anchored at the filesystem root.
_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "oracle"


def _hdc_from_fixture(fixture_name: str) -> str:
    """The .hdc path an oracle fixture was generated from, or "" if unknown."""
    f = _FIXTURES / f"{fixture_name}.json"
    if not f.exists():
        return ""
    return json.loads(f.read_text()).get("hdc_path") or ""


# Scorpion Man — has populated biography fields.
SCORPION_MAN = _hdc_from_fixture(
    "bestiary__HERO_System_Bestiary_6th_Edition_Character_Pack__"
    "HSB HD Files__CHAPTER_2__SCORPION_MAN__SCORPION_MAN_HSB"
)

# Doctor Destroyer — superheroic template, high experience.
DOCTOR_DESTROYER = _hdc_from_fixture(
    "villains__CV1HDFiles__CV1 HD Files \u0192__DOCTOR_DESTROYER__"
    "DOCTOR_DESTROYER-CV1"
)

_MISSING = "the .hdc this test reads is not on this machine"


def _require(path: str) -> str:
    """Skip rather than error when the licensed .hdc is absent."""
    if not path or not Path(path).exists():
        pytest.skip(_MISSING)
    return path


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
    def scorpion(self):
        loader = HDCLoader()
        return loader.load_file(_require(SCORPION_MAN))

    @pytest.fixture
    def destroyer(self):
        loader = HDCLoader()
        return loader.load_file(_require(DOCTOR_DESTROYER))

    def test_name(self, scorpion):
        assert scorpion.name == "Scorpion Man"

    def test_template_name(self, scorpion):
        assert "Heroic6E" in scorpion.template_name

    def test_base_points(self, scorpion):
        assert scorpion.base_points == 175

    def test_disad_points(self, scorpion):
        assert scorpion.disad_points == 50

    def test_experience(self, scorpion):
        assert scorpion.experience == 72

    def test_height_nonzero(self, scorpion):
        assert scorpion.height > 0.0

    def test_weight_nonzero(self, scorpion):
        assert scorpion.weight > 0.0

    def test_hair_color(self, scorpion):
        assert scorpion.hair_color == "Brown"

    def test_eye_color(self, scorpion):
        assert scorpion.eye_color == "Brown"

    def test_background_populated(self, scorpion):
        assert "scorpion-men" in scorpion.background.lower()

    def test_personality_populated(self, scorpion):
        assert len(scorpion.personality) > 10

    def test_tactics_populated(self, scorpion):
        assert len(scorpion.tactics) > 10

    def test_campaign_use_populated(self, scorpion):
        assert len(scorpion.campaign_use) > 10

    def test_appearance_populated(self, scorpion):
        assert len(scorpion.appearance) > 10

    def test_destroyer_base_points(self, destroyer):
        assert destroyer.base_points == 400

    def test_destroyer_experience(self, destroyer):
        assert destroyer.experience == 3214

    def test_empty_fields_default(self, destroyer):
        # These are empty in Doctor Destroyer's HDC
        assert destroyer.player_name == ""
        assert destroyer.campaign_name == ""


class TestMetadataRoundtrip:
    """Verify metadata survives load -> export -> reload."""

    @pytest.fixture
    def scorpion_roundtrip(self):
        return _roundtrip(_require(SCORPION_MAN))

    @pytest.fixture
    def destroyer_roundtrip(self):
        return _roundtrip(_require(DOCTOR_DESTROYER))

    def test_str_attrs_roundtrip(self, scorpion_roundtrip):
        hero1, hero2 = scorpion_roundtrip
        for attr in _STR_ATTRS:
            assert getattr(hero2, attr) == getattr(hero1, attr), (
                f"{attr}: {getattr(hero2, attr)!r} != {getattr(hero1, attr)!r}"
            )

    def test_text_fields_roundtrip(self, scorpion_roundtrip):
        hero1, hero2 = scorpion_roundtrip
        for field in _TEXT_FIELDS:
            assert getattr(hero2, field) == getattr(hero1, field), (
                f"{field}: {getattr(hero2, field)!r} != {getattr(hero1, field)!r}"
            )

    def test_int_attrs_roundtrip(self, scorpion_roundtrip):
        hero1, hero2 = scorpion_roundtrip
        for attr in _INT_ATTRS:
            assert getattr(hero2, attr) == getattr(hero1, attr), (
                f"{attr}: {getattr(hero2, attr)} != {getattr(hero1, attr)}"
            )

    def test_float_attrs_roundtrip(self, scorpion_roundtrip):
        hero1, hero2 = scorpion_roundtrip
        for attr in _FLOAT_ATTRS:
            assert abs(getattr(hero2, attr) - getattr(hero1, attr)) < 0.01, (
                f"{attr}: {getattr(hero2, attr)} != {getattr(hero1, attr)}"
            )

    def test_destroyer_str_attrs_roundtrip(self, destroyer_roundtrip):
        hero1, hero2 = destroyer_roundtrip
        for attr in _STR_ATTRS:
            assert getattr(hero2, attr) == getattr(hero1, attr), (
                f"{attr}: {getattr(hero2, attr)!r} != {getattr(hero1, attr)!r}"
            )

    def test_destroyer_int_attrs_roundtrip(self, destroyer_roundtrip):
        hero1, hero2 = destroyer_roundtrip
        for attr in _INT_ATTRS:
            assert getattr(hero2, attr) == getattr(hero1, attr), (
                f"{attr}: {getattr(hero2, attr)} != {getattr(hero1, attr)}"
            )

    def test_template_name_roundtrip(self, scorpion_roundtrip):
        hero1, hero2 = scorpion_roundtrip
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
