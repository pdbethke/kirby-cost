"""Where the machine-bound HERO character corpus lives, if it lives anywhere.

kirby-cost ships no Hero Games content — not templates, not the oracle fixture
corpus, and not the character files those are built from. Tests that cost real
published characters therefore need somewhere to find them, and must skip
cleanly when they cannot.

One exception, added 2026-09-01: ``tests/fixtures/authored/`` holds three
.hdc files — ``Ravel.hdc``, ``Bokor.hdc`` and ``PowerLad.hdc``. They are the
maintainer's OWN characters, built on stock templates, cleared for
publication. They are the only .hdc files in the repository, and they are here
so that the canonical load path — ``HDCLoader`` on a real HD-saved file — runs
by default rather than only on the one machine with a variable set. See
``authored_hdc``.

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


#: The authored characters that ship WITH the repository: Ravel, Bokor and
#: PowerLad, the maintainer's own creations, built on stock templates and
#: cleared by him for publication — so the canonical load path has real
#: HD-saved .hdc files to run against on every machine, with nothing to
#: configure. Nothing else from his document store may join them: the rest of
#: that directory is licensed third-party material, and so are the variant
#: files (background sheets, equipment kits) sitting beside these three.
BUNDLED_AUTHORED = Path(__file__).resolve().parent / "fixtures" / "authored"


def authored_root() -> Optional[Path]:
    """A directory holding the authored characters, or None.

    The three characters the maintainer has cleared for use as corpus, by
    name: ``Ravel.hdc``, ``Bokor.hdc``, ``PowerLad.hdc``. All three are now
    bundled (see ``BUNDLED_AUTHORED``), so this variable is an override rather
    than the only way to find them.

    A directory rather than three variables, and no default, for the reason
    ``roundtrip_hdc`` records: a path into a maintainer's home is not
    shippable, and a variable that names one reads as configured while
    behaving as absent on every other machine.
    """
    return _from_env("KIRBY_COST_AUTHORED")


def authored_hdc(name: str) -> Optional[Path]:
    """The authored character's .hdc: the configured store first, then bundled.

    The environment variable still wins, so a maintainer pointing at his own
    document store gets his working copies, and anyone can point it at a
    directory of their own. What changed is the floor: ``tests/fixtures/
    authored/`` is searched when the variable names nothing useful, so the
    bundled characters are found by default and the canonical load path is
    exercised on every machine.

    Why that matters is worth stating plainly. ``HDCLoader`` is this project's
    canon — an HD-saved .hdc carries fields the oracle's JSON dump drops, and
    a test that asserts against the dump is asserting against a lossy copy.
    Gating the canonical test on an unset variable meant the lossy tests ran
    and the faithful one did not; two "regressions" were reported in one
    evening that existed only in the dump. Canonical implies default.
    """
    root = authored_root()
    if root is not None:
        configured = root / f"{name}.hdc"
        if configured.exists():
            return configured
    bundled = BUNDLED_AUTHORED / f"{name}.hdc"
    return bundled if bundled.exists() else None


def require_authored_hdc(name: str) -> Path:
    """``authored_hdc(name)``, or raise.

    For a bundled character, absence is not "unrunnable on this machine" — it
    is a tracked file someone deleted, and the run should say so in red. Tests
    on the canonical path call this instead of carrying a skip guard.
    """
    found = authored_hdc(name)
    if found is None:
        raise FileNotFoundError(
            f"{name}.hdc was not found in KIRBY_COST_AUTHORED nor bundled at "
            f"{BUNDLED_AUTHORED}. If {name} is one of the bundled three, the "
            f"tracked fixture has gone missing; restore it rather than "
            f"skipping the canonical load path."
        )
    return found


#: Every input the suite can be pointed at: variable -> what it should name.
#: `conftest.py` reads this twice — to report what a run is configured with,
#: and to decide whether a skip is acceptable or a defect.
INPUTS = {
    "KIRBY_COST_HDT": "a HERO Designer .hdt template",
    "KIRBY_COST_CORPUS": "a directory of .hdc character packs",
    "KIRBY_COST_HERO_DOCS": "a HERO Designer document store",
    "KIRBY_COST_HD6CLI": "the headless HERO Designer comparison CLI",
    "KIRBY_COST_ROUNDTRIP_HDC": "a structurally complex .hdc to roundtrip",
    # Still an input, and still honoured: it overrides the bundled copies for
    # anyone working against their own document store. It is deliberately NOT
    # removed from this table — `conftest.py` reads INPUTS both to report what
    # a run was configured with and to decide whether a skip is a defect, and
    # an input that is satisfiable two ways is still an input.
    "KIRBY_COST_AUTHORED": "a directory of the three authored .hdc characters",
}

#: The 6E templates HD ships in its own template/ directory. KIRBY_COST_HDT
#: names ONE .hdt, but a template resolves its `extends` chain through its
#: SIBLINGS, and the corpus declares templates other than the one named --
#: HSEG equipment packs among them. So a directory holding Main6E.hdt but not
#: its siblings is configured and broken at the same time: costing silently
#: falls back, and the fidelity tests then report display-string mismatches
#: that look like engine defects. Measured 2026-08-27: pointing the variable
#: at a 4-template partial copy failed 5 tests across test_display_fidelity,
#: test_export_fidelity, test_oracle_fixtures and test_template_extends_chain;
#: pointing it at the full 17-template directory passed all 1512.
#:
#: Reported rather than enforced. These tests SHOULD fail on a partial
#: directory -- their results really are wrong -- so this names the cause in
#: the run header instead of converting a real failure into a silent skip.
REQUIRED_SIBLING_TEMPLATES = (
    "Main6E.hdt", "Base6E.hdt", "Heroic6E.hdt", "Superheroic6E.hdt",
    "Vehicle6E.hdt", "Automaton6E.hdt", "AI6E.hdt", "Computer6E.hdt",
)


def missing_sibling_templates() -> "list[str]":
    """Which 6E templates are absent from KIRBY_COST_HDT's own directory.

    Empty when the variable is unset -- that case is already reported as a
    missing input, and saying it twice would read as two separate problems.
    """
    hdt = _from_env("KIRBY_COST_HDT")
    if hdt is None:
        return []
    d = Path(hdt).parent
    return [t for t in REQUIRED_SIBLING_TEMPLATES if not (d / t).is_file()]


_FIXTURES = BUNDLED_AUTHORED.parent

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


#: Names an input can be satisfied by without any environment variable,
#: because the repository now carries what it points at. Only
#: KIRBY_COST_AUTHORED qualifies: its three characters are bundled.
#:
#: This is not a bypass of the skip guard, it is the reason the guard can
#: tighten. An input that is present is not missing, and `conftest.py` fails a
#: run that skips while nothing is missing -- so a machine with no
#: KIRBY_COST_AUTHORED set is now HELD to running the authored-character
#: tests, instead of being excused from them.
_BUNDLE_SATISFIES = {
    "KIRBY_COST_AUTHORED": lambda: all(
        (BUNDLED_AUTHORED / f"{name}.hdc").is_file()
        for name in ("Ravel", "Bokor", "PowerLad")
    ),
}


def _satisfied_by_bundle(var: str) -> bool:
    check = _BUNDLE_SATISFIES.get(var)
    return bool(check and check())


def missing_inputs() -> "list[str]":
    """Which inputs are absent — unset, mispointed, or never generated.

    Unset and mispointed are deliberately the same answer. A variable that
    names a path which no longer exists is the more dangerous of the two —
    it reads as configured and behaves as absent.

    An input the repository itself now satisfies does not count as missing —
    see `_BUNDLE_SATISFIES`. The variable still overrides it; what it no
    longer does is decide whether those tests run at all.

    `GENERATED` is folded in for one reason: `conftest.py` fails a run that
    skips while nothing is missing, and without these a fresh clone with all
    five variables set would still skip 45 tests and be told its coverage had
    gone missing, when in truth it had never generated the fixtures.
    """
    return (
        [var for var in INPUTS
         if _from_env(var) is None and not _satisfied_by_bundle(var)]
        + [name for name in GENERATED if not _generated_present(name)]
    )
