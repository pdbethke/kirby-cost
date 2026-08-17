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

Nothing here raises. A missing corpus is the normal case for anyone who is not
the maintainer, and the suite is expected to pass without it: 590 passed /
45 skipped on a clean clone, against 1289 with a full corpus.
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
