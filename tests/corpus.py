"""Where the machine-bound HERO character corpus lives, if it lives anywhere.

kirby-cost ships no Hero Games content — not templates, not the oracle fixture
corpus, and not the character files those are built from. Tests that cost real
published characters therefore need somewhere to find them, and must skip
cleanly when they cannot.

Two roots, both overridable, both optional:

``KIRBY_COST_CORPUS``
    A directory of ``.hdc`` files, laid out in whatever subdirectories you
    like. Unset by default: there is no sensible guess to make, and guessing
    at a sibling checkout only worked on one machine.

``KIRBY_COST_HERO_DOCS``
    A HERO Designer document store — the sort of folder HD saves into, holding
    purchased character packs. No default; set it or the tests that need it
    skip.

``KIRBY_COST_ROUNDTRIP_HDC``
    One structurally awkward character, the hardest roundtrip case in the
    suite: a Multipower, a Variable Power Pool, two CompoundPowers and a pair
    of maneuvers, which between them exercise every container path — slot
    binding, a pool's control cost, sub-power summation — that no standalone
    power reaches. Any sufficiently gnarly .hdc of your own will do; there is
    nothing to look for and no default worth writing.

Nothing here raises. A missing corpus is the normal case for anyone who is not
the maintainer, and the suite is expected to pass without it. Measured
2026-08-18, from a clean checkout, against four configurations:

==================================  ======  =======
configuration                       passed  skipped
==================================  ======  =======
nothing set                            394      167
template only                          435      126
all five variables, no fixtures        618       47
every input, fixtures generated       1319        0
==================================  ======  =======

The template is the single biggest lever, and the generated fixtures are the
second: ``tests/fixtures/oracle/`` holds the 655 oracle dumps that the whole
parity claim rests on, and it is gitignored derived Hero Games content, so a
fresh clone has none of it (see ``GENERATED``).

**Skipping is the failure mode to watch for here, because it is green.** A
stale path does not fail, it silently subtracts coverage — the oracle fixtures
skipped for months that way after the Kirby rename, and the whole-character
roundtrip skipped from the moment its hardcoded path was scrubbed for
publication until 2026-08-18. So once every input IS configured, ``conftest.py`` fails the run on
any skip at all; see ``missing_inputs``.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def _from_env(var: str) -> Optional[Path]:
    raw = os.environ.get(var)
    if not raw:
        return None
    p = Path(raw).expanduser()
    return p if p.exists() else None


def corpus_root() -> Optional[Path]:
    """The `resources/` tree of .hdc packs, or None."""
    return _from_env("KIRBY_COST_CORPUS")


def hd6cli() -> Optional[Path]:
    """The HERO Designer comparison CLI, or None.

    ``KIRBY_COST_HD6CLI`` points at the wrapper script for a headless build of
    HERO Designer, used to compare this engine's numbers against HD's own. That
    harness wraps licensed source and is not public, so the tests that drive it
    skip for everyone but the maintainer.
    """
    return _from_env("KIRBY_COST_HD6CLI")


def hero_docs_root() -> Optional[Path]:
    """A HERO Designer document store holding character packs, or None."""
    return _from_env("KIRBY_COST_HERO_DOCS")


def corpus_file(*parts: str) -> Optional[Path]:
    """A path under `corpus_root()`, or None if the corpus or file is absent."""
    root = corpus_root()
    if root is None:
        return None
    p = root.joinpath(*parts)
    return p if p.exists() else None


def hero_doc(*parts: str) -> Optional[Path]:
    """A path under `hero_docs_root()`, or None if absent."""
    root = hero_docs_root()
    if root is None:
        return None
    p = root.joinpath(*parts)
    return p if p.exists() else None


def roundtrip_hdc() -> Optional[Path]:
    """The structurally complex roundtrip character, or None.

    Deliberately not named after any one character. The variable this replaced
    was named for the single file it pointed at — a player's PC from a home
    campaign, carrying their name and home directory paths, and so never
    shippable. What the test needs is not that file but any build awkward
    enough to exercise frameworks and containers.
    """
    return _from_env("KIRBY_COST_ROUNDTRIP_HDC")


#: Every input the suite can be pointed at: variable -> what it should name.
#: `conftest.py` reads this twice — to report what a run is configured with,
#: and to decide whether a skip is acceptable or a defect.
INPUTS = {
    "KIRBY_COST_HDT": "a HERO Designer .hdt template",
    "KIRBY_COST_CORPUS": "a directory of .hdc character packs",
    "KIRBY_COST_HERO_DOCS": "a HERO Designer document store",
    "KIRBY_COST_HD6CLI": "the headless HERO Designer comparison CLI",
    "KIRBY_COST_ROUNDTRIP_HDC": "a structurally complex .hdc to roundtrip",
}

_FIXTURES = Path(__file__).resolve().parent / "fixtures"

#: Inputs that are not environment variables but generated files, kept out of
#: the repository by .gitignore because they are derived Hero Games content —
#: JSON dumps of HD's own costs for characters from packs you own. You produce
#: them from your own corpus; there is nothing to configure and nothing to
#: point at, so they are named by path rather than by variable.
GENERATED = {
    "tests/fixtures/oracle/": "the 655 oracle cost fixtures",
    "tests/fixtures/roundtrip_hd6_costs.json": "one character's stored oracle costs",
    "tests/fixtures/*.hdc": "the two CV1 character files read directly",
}


def _generated_present(name: str) -> bool:
    if name.endswith("/"):
        d = _FIXTURES / name.split("/")[-2]
        return d.is_dir() and any(d.glob("*.json"))
    if "*" in name:
        return any(_FIXTURES.glob(name.rsplit("/", 1)[-1]))
    return (_FIXTURES / name.rsplit("/", 1)[-1]).exists()


def missing_inputs() -> "list[str]":
    """Which inputs are absent — unset, mispointed, or never generated.

    Unset and mispointed are deliberately the same answer. A variable that
    names a path which no longer exists is the more dangerous of the two —
    it reads as configured and behaves as absent.

    `GENERATED` is folded in for one reason: `conftest.py` fails a run that
    skips while nothing is missing, and without these a fresh clone with all
    five variables set would still skip 45 tests and be told its coverage had
    gone missing, when in truth it had never generated the fixtures.
    """
    return (
        [var for var in INPUTS if _from_env(var) is None]
        + [name for name in GENERATED if not _generated_present(name)]
    )
