"""A Compound Power's parts keep HERO Designer's own ids through the build doc.

HD writes an ``ID`` on every part of a Compound Power (Ravel's "Wrap 'em and
Nap 'em" holds an Entangle ``ID="1648349641892"``). The build doc emitted the
parts through ``to_build_dict``, which carries no id, so a build rebuilt from
its doc gave each part a load-order counter instead: a different number on
every load.

That broke combat (found 2026-11-09). kirby-combat names an attack by its
power's id, and kirby-api rebuilds every fight from the pinned build doc, so a
rebuilt fight could not find the attack that had been chosen. It also wrote a
different ``ID`` into each ``.hdc`` exported from the doc.
"""
from kirby_cost.io.build_json import build_from_json, to_build_json
from kirby_cost.io.hdc_loader import HDCLoader

RAVEL = "tests/fixtures/authored/Ravel.hdc"
WRAP_AND_NAP = "1648349598295"
WRAP_EM = 1648349641892


def _compound(powers, compound_id: str):
    return next(p for p in powers if str(p.id) == compound_id)


def test_the_doc_carries_each_compound_part_id() -> None:
    doc = to_build_json(HDCLoader().load_file(RAVEL))
    compound = next(p for p in doc["powers"] if p["id"] == WRAP_AND_NAP)
    assert all(part.get("id") for part in compound["sub_powers"])
    assert compound["sub_powers"][0]["id"] == str(WRAP_EM)


def test_a_rebuilt_compound_part_answers_to_the_file_id() -> None:
    doc = to_build_json(HDCLoader().load_file(RAVEL))
    rebuilt = _compound(build_from_json(doc).powers, WRAP_AND_NAP)
    assert rebuilt.powers[0].id == WRAP_EM


def test_two_rebuilds_agree_on_every_compound_part_id() -> None:
    doc = to_build_json(HDCLoader().load_file(RAVEL))
    first = _compound(build_from_json(doc).powers, WRAP_AND_NAP)
    second = _compound(build_from_json(doc).powers, WRAP_AND_NAP)
    assert [p.id for p in first.powers] == [p.id for p in second.powers]
