"""A build doc rebuilt through the engine comes back as the same doc.

`to_build_json(build_from_json(doc)) == doc`, for every authored character.
A store keeps the doc and rebuilds from it (kirby-build-store, kirby-api), so
a doc that is not a fixed point is a character that changes the first time it
is stored. Found 2026-11-25 by kirby-build-store's round trip:

* ``affects_primary`` was written only when False, "because True is the
  class default". It is not for a Power (`Power.__init__` sets False), so a
  power HD marks AFFECTS_PRIMARY="Yes" lost it: Bokor's and PowerLad's
  Resistant Protection came back no longer raising their defences.
* ``alias`` was written only when non-empty, so a stated ALIAS="" became the
  class's own alias on rebuild (Bokor's two Knowledge Skills became "KS").

* a Knowledge Skill's TYPE was never written, and HD decides from TYPE
  whether a stated alias stands.

HD writes ALIAS, AFFECTS_PRIMARY and AFFECTS_TOTAL on every element; the doc
now states them on every object, so no rebuild depends on a default.

STILL OPEN (strict xfail below): a stated ALIAS="" is read as absent on the
curated path. `GenericObject` honours a blank ALIAS only when the attribute
is in ``_source_attrs``, which comes from `BuildNode.stated`, and
`build_json._obj_node` leaves ``stated`` None (setting it naively freezes
template-derived costs into an export: the MINCOST="1.0" defect). Bokor's two
blank-alias Knowledge Skills come back "KS". Display only: no cost moves.
"""
from __future__ import annotations

import pytest

from kirby_cost.io.build_json import build_from_json, to_build_json
from kirby_cost.io.hdc_loader import HDCLoader
from tests.corpus import require_authored_hdc


@pytest.mark.parametrize("name", [
    "Ravel",
    pytest.param("Bokor", marks=pytest.mark.xfail(
        strict=True, reason="a stated ALIAS='' is read as absent on the curated "
                            "path (module docstring)")),
    "PowerLad",
])
def test_a_rebuilt_doc_is_the_same_doc(name):
    doc = to_build_json(HDCLoader().load_file(str(require_authored_hdc(name))))
    assert to_build_json(build_from_json(doc)) == doc


@pytest.mark.parametrize("name", ["Bokor", "PowerLad"])
def test_resistant_protection_still_raises_the_defences(name):
    hero = HDCLoader().load_file(str(require_authored_hdc(name)))
    (rp, *_) = [p for p in hero.powers if p.xmlid == "FORCEFIELD"]
    assert rp.affects_primary is True                      # as the .hdc states
    again = build_from_json(to_build_json(hero))
    (same, *_) = [p for p in again.powers if p.xmlid == "FORCEFIELD"]
    assert same.affects_primary is True
