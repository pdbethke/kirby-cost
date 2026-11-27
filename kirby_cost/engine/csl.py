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


def reaches(breadth: Breadth | None, named: str, labels, ranged: bool) -> Reach:
    """Whether a level of ``breadth`` whose words are ``named`` (`named_text`)
    reaches one attack: ``labels``, the names it goes by (its own, its
    framework's, a maneuver's), and whether it is ``ranged``.

    For a caller that keeps a level as data rather than the build object,
    such as a fight's recorded state. HTH / Ranged / All reach by range; a
    narrow level reaches what its words name, and is UNKNOWN when it has no
    words; an unrecognised breadth (None) is UNKNOWN.
    """
    if breadth is None:
        return Reach.UNKNOWN
    if breadth is Breadth.ALL:
        return Reach.YES
    if breadth is Breadth.HTH:
        return Reach.NO if ranged else Reach.YES
    if breadth is Breadth.RANGED:
        return Reach.YES if ranged else Reach.NO
    text = (named or "").lower()
    if not text:
        return Reach.UNKNOWN
    return Reach.YES if _named(text, labels) else Reach.NO


def reach_on(level, attacks) -> list[Reach]:
    """Whether ``level`` reaches each of ``attacks``, a list of
    ``(labels, ranged)``: the names one attack goes by and whether it is a
    Ranged attack. One answer per attack, in order, by `reaches`.

    Across a whole build a narrow level whose words name none of the
    attacks given has named nothing the build answers to, so every answer
    is UNKNOWN, not NO.
    """
    breadth, named = breadth_of(level), named_text(level)
    answers = [reaches(breadth, named, labels, ranged) for labels, ranged in attacks]
    if breadth in _NARROW and Reach.YES not in answers:
        return [Reach.UNKNOWN for _ in attacks]
    return answers


__all__ = ["Breadth", "Reach", "breadth_of", "named_text", "reach_on", "reaches"]
