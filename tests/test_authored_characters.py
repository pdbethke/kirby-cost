"""The three authored characters, against the oracle, on every number and string.

The 655 fixtures are published bestiary and villain-pack entries, and they are
stylistically narrow: flat power lists, few nested frameworks. Characters built
by hand for play are shaped differently, and that difference keeps finding real
bugs. Testing kirby-cost against characters of this kind has now found:

- ``main_power`` never assigned, so sub-powers of a Compound Power inside a
  Multipower were costed with no framework limitations at all
- private modifiers leaking into slot costs (Heartbeat, 4 points light)
- ``literacy_free`` defaulting True (Stone Cold, 1 point light)
- ``Linked.is_limitation`` written but orphaned inside a module-level function,
  so Linked sorted with the advantages (Power Lad)
- ``TimeLimit.column2_output`` never ported, so every Time Limit printed
  "(+1/4)" without saying how long (Bokor)
- no fallback to the template's first option, so a modifier that states a cost
  and no OPTION printed no option at all (Bokor)

**Only these three characters are fair game** (PeterB, 2026-08-21). The rest
of the maintainer's character store is personal campaign material: not test
corpus, not to be read here, committed as a fixture, or named in output.

Point ``KIRBY_COST_AUTHORED`` at a directory holding the three files, by those
names. Symlinks are fine — they need not live together on disk.

| | Points | Template | Frameworks |
|---|---|---|---|
| Ravel | 450 | Superheroic6E | Multipower, VPP, 2x CompoundPower, martial arts |
| Bokor | 276 | Heroic6E | Multipower, CompoundPower |
| Power Lad | 399.5 | Superheroic6E | Multipower, CompoundPower |

Between them they declare two different templates, which the 655 fixtures
exercise only incidentally and which this engine got wrong for four months.

The expectations are committed as JSON dumps of the oracle's own output, so
this runs without the Java oracle present. Regenerate with::

    ./hd6cli.sh <character.hdc> > tests/fixtures/authored/<Name>.json

**real_cost is compared PRE-LIST.** The oracle dumps
``getRealCostPreList()`` for that field (CostCalculatorCLI.java:394), not
``getRealCost()``. They differ wherever a parent list has a say -- a VPP slot's
real cost is 0 and its pre-list cost is its own -- and comparing the wrong one
reports five phantom failures on Power Lad's multipower.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from kirby_cost.io.hdc_loader import HDCLoader
from tests.corpus import authored_hdc
from tests.test_display_fidelity import _engine_index, _oracle_index

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "authored"

#: The characters, by name. The .hdc files themselves are NOT redistributed —
#: they are found through KIRBY_COST_AUTHORED, like every other machine-bound
#: input (see tests/corpus.py). Only the oracle's JSON dumps ship, and those
#: carry costs and display strings: no player or GM name, no campaign name, no
#: background, quote or tactics, and no path into anyone's home directory.
NAMES = ("Ravel", "Bokor", "PowerLad")

#: oracle field -> the engine attribute that answers it.
COST_FIELDS = {
    "total_cost": "total_cost",
    "active_cost": "active_cost",
    "real_cost": "real_cost_pre_list",
}


def _cases():
    for name in NAMES:
        fixture = FIXTURE_DIR / f"{name}.json"
        hdc = authored_hdc(name)
        yield pytest.param(
            name, hdc, fixture,
            marks=pytest.mark.skipif(
                not (fixture.exists() and hdc is not None),
                reason="KIRBY_COST_AUTHORED unset, or the character is not in it",
            ),
        )
    # The kitchen sink is nobody's build -- it is generated, so it never
    # skips and needs no environment. It carries every registered 6E rule
    # that no corpus character takes (see tests/kitchen_sink.py), and its
    # fixture is the oracle's verdict on all of them.
    import tempfile
    from tests.kitchen_sink import write
    yield pytest.param(
        "KitchenSink",
        write(Path(tempfile.gettempdir()) / "kirby-cost-KitchenSink.hdc"),
        FIXTURE_DIR / "KitchenSink.json",
    )


def _load(name, hdc, fixture):
    return json.loads(fixture.read_text()), HDCLoader().load_file(str(hdc))


@pytest.mark.parametrize("name,hdc,fixture", list(_cases()))
def test_every_cost_matches(name, hdc, fixture):
    oracle, hero = _load(name, hdc, fixture)
    engine = _engine_index(hero)
    wrong, compared = [], 0

    def walk(objects):
        nonlocal compared
        for obj in objects:
            mine = engine.get(str(obj.get("id")))
            if mine is not None:
                for field, attr in COST_FIELDS.items():
                    if obj.get(field) is None:
                        continue
                    compared += 1
                    got = float(getattr(mine, attr))
                    if abs(got - float(obj[field])) > 1e-9:
                        wrong.append(
                            f"{obj.get('name') or obj.get('xmlid')}.{field}: "
                            f"{got} != {obj[field]}")
            walk(obj.get("sub_powers") or [])

    for section in ("characteristics", "skills", "powers", "perks", "talents",
                    "complications", "martial_arts"):
        walk(oracle.get(section) or [])

    assert compared > 0, f"{name}: nothing compared — the index is not joining"
    assert not wrong, f"{name}: {len(wrong)} of {compared} costs wrong:\n" + "\n".join(wrong[:10])


@pytest.mark.parametrize("name,hdc,fixture", list(_cases()))
def test_every_display_string_matches(name, hdc, fixture):
    oracle, hero = _load(name, hdc, fixture)
    engine = _engine_index(hero)
    wrong, compared = [], 0

    for ident, wanted in _oracle_index(oracle).items():
        mine = engine.get(ident)
        if mine is None:
            continue
        for field, expected in wanted.items():
            if expected is None:
                continue
            compared += 1
            # No getattr default: a crash inside the property must surface as
            # a failure, not be swallowed into "a string we do not produce".
            got = str(getattr(mine, field))
            if got != expected:
                wrong.append(f"{type(mine).__name__}.{field}\n"
                             f"    PY: {got}\n    HD: {expected}")

    assert compared > 0, f"{name}: nothing compared — the index is not joining"
    assert not wrong, f"{name}: {len(wrong)} of {compared} strings wrong:\n" + "\n\n".join(wrong[:5])


@pytest.mark.parametrize("name,hdc,fixture", list(_cases()))
def test_the_character_totals_match(name, hdc, fixture):
    """The release gate. A character can have every object right and still
    total wrong — that is how the framework bugs above stayed hidden."""
    oracle, hero = _load(name, hdc, fixture)
    assert hero.total_points == oracle["total_points"]
    assert hero.available_points == oracle["available_points"]


@pytest.mark.parametrize("name,hdc,fixture", list(_cases()))
def test_base_value_is_right_before_anything_else_is_touched(name, hdc, fixture):
    """`base_value` must not depend on what was read first.

    It used to be a plain attribute initialised to 0.0 and filled only by
    `_calc_base_value`, so reading it on a freshly loaded character answered
    0.0 — not an error, just a wrong number. A consumer downstream trusted it,
    got zero, and derived the base from other values to compensate, inventing
    a second source of truth for something this engine already knew.

    This reads it FIRST, before any other accessor runs, which is the only
    ordering that could catch a lazily-filled field.
    """
    _, hero = _load(name, hdc, fixture)
    for char in hero.characteristics:
        first_read = char.base_value
        assert first_read == char.get_base_value(), (
            f"{name} {char.xmlid}: base_value read first gave {first_read}, "
            f"get_base_value() gives {char.get_base_value()}")
