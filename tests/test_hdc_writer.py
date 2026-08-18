"""Writing a LoadedHero back out as a .hdc — the fourth leg of the round trip.

The engine could always read an HDC and cost it, and every object could
serialize ITSELF (``SerializationMixin.get_save_xml``). What went missing was
the document: the code that assembles those elements into a CHARACTER an HD
installation will open. It used to live in ``kirby_cost/database/
character_exporter.py`` and was deleted in 1da1b54, "the engine has no
database" — the exporter was not part of the ORM, it merely lived next to it,
and went out with it.

For nine months the only assembler left was a helper inside
tests/test_metadata_roundtrip.py, which wrote six sections and no MARTIALARTS,
so a martial artist round-tripped into someone who had forgotten their art. It
also wrapped every object in ``except Exception: pass``, which turns a
serialization bug into a silently shorter character.

Hence both halves of what is asserted here: that the document carries every
section the loader reads, and that a failure to write an object is LOUD.
"""
import pytest
from lxml import etree

from kirby_cost.io.hdc_loader import HDCLoader, LoadedHero
from kirby_cost.io import hdc_writer
from tests.corpus import roundtrip_hdc


def _require_character():
    path = roundtrip_hdc()
    if path is None:
        pytest.skip("roundtrip character absent (set KIRBY_COST_ROUNDTRIP_HDC)")
    return str(path)


class TestDocumentShape:
    """The shape of the document, with no character needed."""

    def test_root_is_a_character(self):
        hero = LoadedHero()
        root = hdc_writer.hero_to_element(hero)
        assert root.tag == "CHARACTER"
        assert root.get("version") == "6.0"

    def test_template_is_carried_through(self):
        hero = LoadedHero()
        hero.template_name = "builtIn.Superheroic6E.hdt"
        root = hdc_writer.hero_to_element(hero)
        assert root.get("TEMPLATE") == "builtIn.Superheroic6E.hdt"

    def test_a_character_is_costed_against_the_template_it_declares(self):
        """So the writer must never silently substitute a default.

        An unresolvable name keeps the active template, as HD does — but
        writing the WRONG name would recost the character on reload.
        """
        hero = LoadedHero()
        hero.template_name = "builtIn.Vehicle6E.hdt"
        assert hdc_writer.hero_to_element(hero).get("TEMPLATE") == \
            "builtIn.Vehicle6E.hdt"

    def test_sections_are_in_hero_designers_own_order(self):
        """Mirrors the order HD itself writes, so a diff against a
        re-saved file stays readable."""
        root = hdc_writer.hero_to_element(LoadedHero())
        assert [c.tag for c in root] == list(hdc_writer.SECTION_ORDER)

    def test_every_section_the_loader_reads_is_written(self):
        """The MARTIALARTS regression, stated as a rule.

        Anything the loader parses must survive being written, or a load →
        write → load cycle quietly deletes part of the character.
        """
        written = set(hdc_writer.SECTION_ORDER)
        for section in ("CHARACTER_INFO", "BASIC_CONFIGURATION",
                        "CHARACTERISTICS", "SKILLS", "PERKS", "TALENTS",
                        "MARTIALARTS", "POWERS", "EQUIPMENT",
                        "DISADVANTAGES"):
            assert section in written, f"{section} would be dropped"

    def test_text_fields_are_children_of_character_info(self):
        hero = LoadedHero()
        hero.background = "a background"
        hero.campaign_use = "a campaign use"
        root = hdc_writer.hero_to_element(hero)
        info = root.find("CHARACTER_INFO")
        assert info.findtext("BACKGROUND") == "a background"
        assert info.findtext("CAMPAIGN_USE") == "a campaign use"

    def test_text_fields_survive_the_characters_xml_will_not_take_raw(self):
        """Ampersands and angle brackets are ordinary prose. lxml escapes
        them on write and unescapes on read; assert the pair, since a
        hand-rolled writer using string formatting would corrupt here."""
        hero = LoadedHero()
        hero.background = 'Ravel & "the <Tapestry>" -- 100% string'
        blob = hdc_writer.hero_to_bytes(hero)
        reparsed = etree.fromstring(blob.decode("utf-16").split("?>", 1)[1]
                                    .lstrip().encode("utf-8"))
        assert reparsed.find("CHARACTER_INFO").findtext("BACKGROUND") == \
            hero.background


class TestEncoding:
    """HD writes UTF-16 with a declaration. So do we."""

    def test_bytes_are_utf16_with_a_byte_order_mark(self):
        blob = hdc_writer.hero_to_bytes(LoadedHero())
        assert blob[:2] in (b"\xff\xfe", b"\xfe\xff")

    def test_the_declaration_names_the_encoding(self):
        blob = hdc_writer.hero_to_bytes(LoadedHero())
        assert 'encoding="UTF-16"' in blob.decode("utf-16")[:80]

    def test_the_loader_can_read_what_the_writer_produced(self, tmp_path):
        """The only encoding assertion that finally matters."""
        hero = LoadedHero()
        hero.name = "Round Trip"
        path = tmp_path / "out.hdc"
        hdc_writer.write_hdc(hero, path)
        assert HDCLoader().load_file(str(path)).name == "Round Trip"

    def test_utf8_is_available_for_callers_that_want_it(self, tmp_path):
        hero = LoadedHero()
        hero.name = "Round Trip"
        path = tmp_path / "out8.hdc"
        hdc_writer.write_hdc(hero, path, encoding="utf-8")
        assert path.read_bytes()[:2] not in (b"\xff\xfe", b"\xfe\xff")
        assert HDCLoader().load_file(str(path)).name == "Round Trip"

    def test_the_source_encoding_is_reused_by_default(self, tmp_path):
        """A file read as UTF-16 is written back as UTF-16, unasked."""
        hero = LoadedHero()
        hero.source_encoding = "utf-8"
        path = tmp_path / "src.hdc"
        hdc_writer.write_hdc(hero, path)
        assert path.read_bytes()[:2] not in (b"\xff\xfe", b"\xfe\xff")


class TestFailureIsLoud:
    """An object that cannot be written must not simply vanish."""

    def test_a_serialization_failure_raises(self):
        class Broken:
            xmlid = "BROKEN"

            def get_save_xml(self):
                raise ValueError("no")

        hero = LoadedHero()
        hero.powers = [Broken()]
        with pytest.raises(hdc_writer.HDCWriteError) as exc:
            hdc_writer.hero_to_element(hero)
        assert "BROKEN" in str(exc.value)

    def test_an_object_returning_nothing_raises(self):
        class Silent:
            xmlid = "SILENT"

            def get_save_xml(self):
                return None

        hero = LoadedHero()
        hero.skills = [Silent()]
        with pytest.raises(hdc_writer.HDCWriteError):
            hdc_writer.hero_to_element(hero)


class TestRealCharacterRoundTrip:
    """Load → write → load, on a character with every container class."""

    @pytest.fixture
    def pair(self, tmp_path_factory):
        path = _require_character()
        first = HDCLoader().load_file(path)
        out = tmp_path_factory.mktemp("rt") / "again.hdc"
        hdc_writer.write_hdc(first, out)
        second = HDCLoader().load_file(str(out))
        return first, second

    def test_the_point_total_is_unchanged(self, pair):
        first, second = pair
        assert second.total_points == first.total_points

    def test_every_section_keeps_its_population(self, pair):
        first, second = pair
        for section in ("characteristics", "powers", "skills", "perks",
                        "talents", "complications", "martial_arts"):
            assert len(getattr(second, section)) == len(getattr(first, section)), \
                f"{section} changed size across the round trip"

    def test_the_martial_arts_survive(self, pair):
        """The specific thing the old test-local exporter dropped."""
        first, second = pair
        assert [m.display for m in second.martial_arts] == \
               [m.display for m in first.martial_arts]

    def test_every_object_keeps_its_cost(self, pair):
        first, second = pair
        for section in ("characteristics", "powers", "skills", "perks",
                        "talents", "complications"):
            for a, b in zip(getattr(first, section), getattr(second, section)):
                assert b.real_cost == a.real_cost, \
                    f"{section} {a.xmlid}: real_cost moved"
                assert b.active_cost == a.active_cost, \
                    f"{section} {a.xmlid}: active_cost moved"

    def test_frameworks_keep_their_slots(self, pair):
        """A Multipower, a VPP and two CompoundPowers, still holding
        their children — the binding is the part a naive writer loses."""
        first, second = pair

        def containers(hero):
            return {type(p).__name__: p for p in hero.powers
                    if type(p).__name__ in ("Multipower", "VariablePowerPool",
                                            "CompoundPower")}

        before, after = containers(first), containers(second)
        assert set(after) == set(before)
        for name, obj in before.items():
            assert after[name].real_cost == obj.real_cost


class TestModifyThenWrite:
    """The actual use case: load, change something, generate a new HDC."""

    def test_a_text_field_set_in_python_lands_in_the_file(self, tmp_path):
        path = _require_character()
        hero = HDCLoader().load_file(path)
        hero.background = "Set from Python, not from HERO Designer."
        out = tmp_path / "modified.hdc"
        hdc_writer.write_hdc(hero, out)
        assert HDCLoader().load_file(str(out)).background == hero.background

    def test_modifying_prose_does_not_move_a_single_cost(self, tmp_path):
        """Editing the background must be free. If this fails, the writer is
        losing build data on the way out, not the prose."""
        path = _require_character()
        hero = HDCLoader().load_file(path)
        before = hero.total_points
        hero.background = "x" * 5000
        hero.personality = "y" * 5000
        out = tmp_path / "prose.hdc"
        hdc_writer.write_hdc(hero, out)
        assert HDCLoader().load_file(str(out)).total_points == before


class TestDocumentFidelity:
    """Load → write reproduces the document, element for element.

    The census these assert used to read: 21 attributes dropped, 12 changed,
    5 invented, across 223 elements. Each was its own small betrayal of the
    same rule — the object must carry the whole document, and the writer must
    state what the document stated and nothing else.
    """

    @staticmethod
    def _index(path):
        from lxml import etree
        raw = open(path, "rb").read()
        text = (raw.decode("utf-16")
                if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8"))
        root = etree.fromstring(
            text[text.index("?>") + 2:].lstrip().encode("utf-8"))
        return root, {e.get("ID"): e for e in root.iter() if e.get("ID")}

    @pytest.fixture
    def rewritten(self, tmp_path):
        source = _require_character()
        hero = HDCLoader().load_file(source)
        out = tmp_path / "rewritten.hdc"
        hdc_writer.write_hdc(hero, out)
        return source, str(out)

    def test_every_element_survives(self, rewritten):
        source, out = rewritten
        _, before = self._index(source)
        _, after = self._index(out)
        assert set(after) == set(before)

    def test_no_attribute_is_dropped_changed_or_invented(self, rewritten):
        source, out = rewritten
        _, before = self._index(source)
        _, after = self._index(out)
        problems = []
        for ident, original in before.items():
            written = after[ident]
            for key, value in original.attrib.items():
                if key not in written.attrib:
                    problems.append(f"{ident} dropped {key}={value!r}")
                elif written.get(key) != value:
                    problems.append(
                        f"{ident} changed {key}: {value!r} -> {written.get(key)!r}")
            for key in written.attrib:
                if key not in original.attrib:
                    problems.append(f"{ident} invented {key}")
        assert not problems, "\n".join(problems[:20])

    def test_attributes_keep_the_documents_order(self, rewritten):
        """lxml writes attributes in the order they were set, so a set-based
        record of "which attributes existed" is not enough."""
        source, out = rewritten
        _, before = self._index(source)
        _, after = self._index(out)
        for ident, original in before.items():
            assert list(after[ident].attrib) == list(original.attrib), ident

    def test_sections_keep_the_documents_order(self, rewritten):
        source, out = rewritten
        a, _ = self._index(source)
        b, _ = self._index(out)
        assert [c.tag for c in b] == [c.tag for c in a]


class TestModifyAndRemove:
    """The point of the exercise: change it, and have the change be the only
    difference."""

    def test_editing_prose_changes_only_the_prose(self, tmp_path):
        source = _require_character()
        hero = HDCLoader().load_file(source)
        hero.background = "A background written from Python."
        out = tmp_path / "edited.hdc"
        hdc_writer.write_hdc(hero, out)
        again = HDCLoader().load_file(str(out))
        assert again.background == hero.background
        assert again.total_points == hero.total_points

    def test_renaming_a_power_keeps_its_cost(self, tmp_path):
        source = _require_character()
        hero = HDCLoader().load_file(source)
        power = hero.powers[0]
        before = power.real_cost
        power.name = "Renamed From Python"
        out = tmp_path / "renamed.hdc"
        hdc_writer.write_hdc(hero, out)
        again = HDCLoader().load_file(str(out))
        assert again.powers[0].name == "Renamed From Python"
        assert again.powers[0].real_cost == before

    def test_removing_a_power_removes_its_points(self, tmp_path):
        """Removal has to work as well as modification, and the total must
        follow — the cost is recomputed from the objects, never stored."""
        source = _require_character()
        hero = HDCLoader().load_file(source)
        standalone = next(p for p in hero.powers
                          if not p.parent_id and p.real_cost > 0
                          and type(p).__name__ not in (
                              "Multipower", "VariablePowerPool", "CompoundPower"))
        cost, before = standalone.real_cost, hero.total_points
        hero.powers.remove(standalone)
        out = tmp_path / "removed.hdc"
        hdc_writer.write_hdc(hero, out)
        again = HDCLoader().load_file(str(out))
        assert len(again.powers) == len(hero.powers)
        assert again.total_points == before - cost
