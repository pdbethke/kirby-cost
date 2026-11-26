"""Which attacks a Combat Skill Level reaches (6E1 72).

6E1 72 prices a level by its breadth -- with any single attack, a small group
of attacks, a large group, HTH Combat, Ranged Combat, All Attacks -- so the
breadth is the rule: counting a level without it spends the cheapest price at
the dearest reach.

HD stores no link from a narrow level (single / small group / large group) to
the attacks it was bought for. The words are in its NAME ("+1 With Punch,
Haymaker, and Throw") or its OPTION_ALIAS ("with Power Over Light And Heat
Multipower"). So a narrow level is matched by those words against the names an
attack goes by: its own, its framework's, a maneuver's.

LIFTED FROM kirby-combat (`hero_view._csl_named_attacks`, `_csl_breadth`,
`resolution/to_hit._csl_reaches`, 2026-11-26) so the builder's limits and the
fight read one rule. One difference, deliberate: where kirby-combat narrowed on
doubt (a level naming nothing reached nothing), this answers `Reach.UNKNOWN`.
A fight may narrow; a ceiling that narrows under-measures what the player paid
for. The caller decides what UNKNOWN means for it; nothing here guesses.
"""
from __future__ import annotations

from enum import Enum


class Breadth(Enum):
    """6E1 72's six breadths, by HD's OPTION XMLID."""

    SINGLE = "SINGLE"
    TIGHT = "TIGHT"
    BROAD = "BROAD"
    HTH = "HTH"
    RANGED = "RANGED"
    ALL = "ALL"


class Reach(Enum):
    YES = "yes"
    NO = "no"
    #: The build's own words cannot say: a narrow level naming nothing the
    #: build answers to, or an option that is none of the six.
    UNKNOWN = "unknown"


_NARROW = frozenset({Breadth.SINGLE, Breadth.TIGHT, Breadth.BROAD})

#: The template's own option wording: a level whose only text is this has
#: named nothing.
_GENERIC_ALIASES = frozenset({
    "with any single attack",
    "with a small group of attacks",
    "with a large group of attacks",
    "with hth combat",
    "with ranged combat",
    "with all attacks",
})

#: A label shorter than this cannot match: a power called "X", or an empty
#: name, would otherwise match every sentence in the build.
_MIN_LABEL = 3


def breadth_of(level) -> Breadth | None:
    """The breadth this level was bought at, or None when HD's option is
    none of the six. HD records the option as the resolved option object
    and as the raw OPTIONID; both are asked."""
    option = getattr(level, "_selected_option", None)
    for candidate in (getattr(option, "xmlid", None),
                      getattr(level, "option_id", None)):
        value = (candidate or "").strip().upper()
        if value in Breadth.__members__:
            return Breadth[value]
    return None


def named_text(level) -> str:
    """The free text saying which attacks a narrow level was bought for:
    HD's NAME and OPTION_ALIAS (and INPUT, which no real build has used),
    with the template's boilerplate dropped."""
    option = getattr(level, "_selected_option", None)
    parts: list[str] = []
    for value in (getattr(level, "name", None),
                  getattr(option, "alias", None),
                  getattr(level, "input", None)):
        text = (value or "").strip()
        if text and text.lower() not in _GENERIC_ALIASES:
            parts.append(text)
    return " | ".join(dict.fromkeys(parts))


def _named(text: str, labels) -> bool:
    for label in labels:
        label = (label or "").strip().lower()
        if len(label) >= _MIN_LABEL and label in text:
            return True
    return False


def reach_on(level, attacks) -> list[Reach]:
    """Whether ``level`` reaches each of ``attacks``, a list of
    ``(labels, ranged)``: the names one attack goes by and whether it is a
    Ranged attack. One answer per attack, in order.

    HTH / Ranged / All reach by range. A narrow level reaches the attacks
    its words name; when its words name nothing on the build at all -- none
    of the attacks given -- every answer is UNKNOWN, since the build cannot
    say what it was bought for. An unrecognised breadth is UNKNOWN too.
    """
    breadth = breadth_of(level)
    if breadth is None:
        return [Reach.UNKNOWN for _ in attacks]
    if breadth is Breadth.ALL:
        return [Reach.YES for _ in attacks]
    if breadth is Breadth.HTH:
        return [Reach.NO if ranged else Reach.YES for _, ranged in attacks]
    if breadth is Breadth.RANGED:
        return [Reach.YES if ranged else Reach.NO for _, ranged in attacks]
    text = named_text(level).lower()
    hits = [_named(text, labels) for labels, _ in attacks]
    if not text or not any(hits):
        return [Reach.UNKNOWN for _ in attacks]
    return [Reach.YES if hit else Reach.NO for hit in hits]


__all__ = ["Breadth", "Reach", "breadth_of", "named_text", "reach_on"]
