"""The most Damage Classes one attack can reach (workshop spec §5.2.1).

A DC ceiling measured purchase by purchase is beaten by stacking, and the book
names that abuse (6E2 101). So each attack is measured as the best a character
can make of it under the Adding Damage rules (6E2 101-104):

    base attack  +  at most one maneuver  +  the adders the GM counts
                 then the doubling check, when the GM applies it

Rules, by plan 1b's numbering (each cited where it is applied below):

R1  Base attack: an Attack Power or Killing Attack; a weapon paid for; STR
    Normal Damage, an HA counting as STR damage. Extra DCs are base damage
    unarmed; with a weapon, the weapon is the base (6E2 101).
R2  One maneuver: a Haymaker is a maneuver in itself, Strike excepted (6E2 71).
R3  Haymaker +4 DCs, HTH only (6E2 58, 71; Peter 2026-11-26).
R4  Move By (STR/2) + v/10; Move Through STR + v/6 (6E2 58).
R5  STR: +1 DC per full 5, whole DCs only; to an HKA, STR then the
    maneuver's bonus, never STR twice (6E2 101-102).
R6  A maneuver that adds dice adds +1 DC per +1 DC; a Killing / NND / Exert
    maneuver adds nothing to a weapon or other attack (6E2 101).
R7  Extra DCs add one each to every maneuver (6E2 94).
R8  2 CSLs = +1 DC to a HTH or Ranged attack the level reaches (6E2 101;
    6E1 72); none to a Mental attack.
R9  Velocity in whole 6m / 10m (6E2 101), at the best Noncombat velocity a
    Move Through may use (`engine.movement`).
R10 Added DCs count at their usual rate on an Advantaged attack (6E2 104).
R11 Doubling: no more than twice the base, when the GM applies it (6E2 101).
R12 Maneuvers work with a weapon only through a Weapon Element or a
    weapon-based style; a bare HKA takes them directly (6E2 94, 102).
R13 Deadly Blow: +3 DCs a level to Killing Attacks involving weapons, HKA or
    RKA as bought (6E1 115).
R14 Where the build's free text cannot say what a narrow CSL, a Weapon
    Element or a Deadly Blow reaches, it is reported, never guessed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from kirby_cost.engine.csl import Reach, reach_on
from kirby_cost.engine.damage import damage_classes_of, str_damage_classes


class AddedDamage(Enum):
    """The Adding Damage methods a DC ceiling may count (6E2 101's
    "primary methods", Martial Maneuvers and Extra DCs as one, plus Deadly
    Blow, 6E1 115). The GM names them; 6E2 285 does not."""

    STR = "str"
    MARTIAL = "martial"
    CSL = "csl"
    HAYMAKER = "haymaker"
    VELOCITY = "velocity"
    DEADLY_BLOW = "deadly_blow"


@dataclass(frozen=True)
class Reached:
    """One attack at its best: the base purchase's HD ID (None for STR),
    its DCs, and the parts that make them up."""

    hd_id: str | None
    label: str
    dcs: float
    parts: tuple[tuple[str, float], ...]

    def describe(self) -> str:
        if len(self.parts) == 1 and self.parts[0][0] in ("base", "STR"):
            return f"Damage Classes {self.dcs:g}"
        body = " + ".join(f"{name} {value:g}" for name, value in self.parts)
        return f"Damage Classes {self.dcs:g} ({self.label}: {body})"


@dataclass(frozen=True)
class Unmeasured:
    """A purchase whose reach the build's own words cannot settle (R14)."""

    hd_id: str | None
    detail: str


@dataclass
class _Base:
    hd_id: str | None
    label: str
    names: tuple[str, ...]
    dcs: float
    hth: bool
    ranged: bool
    killing: bool
    weapon: bool
    hka: bool
    #: STR or an HA: maneuvers add to it unarmed (R1).
    unarmed: bool
    #: Normal or Killing Damage against PD/ED (the template's DEFENSE
    #: "NORMAL"): what a Haymaker, STR or a dice-adding maneuver can add to
    #: (6E2 71, 101). A Transform, Drain, Flash or Mental Blast is not.
    physical: bool = True
    #: For an HA, its own DCs (STR's are added in the base).
    ha_dcs: float = 0.0


_ADDS_DICE = ("[NORMALDC]", "[STRDC]", "[WEAPONDC]")
_DIFFERENTIATES = ("[NNDDC]", "[KILLINGDC]", "[FLASHDC]", "[WEAPONKILLINGDC]")
_VELOCITY = re.compile(r"v/(\d+)", re.IGNORECASE)


def _effect(m) -> str:
    return ((m.weapon_effect if m.use_weapon else m.effect) or "")


def _adds_dice(m) -> bool:
    """R6: a maneuver whose effect is Normal dice added to STR or a weapon."""
    text = _effect(m)
    return any(t in text for t in _ADDS_DICE) and not any(
        t in text for t in _DIFFERENTIATES)


def _deals_damage(m) -> bool:
    text = _effect(m)
    return m.does_damage or any(t in text for t in _ADDS_DICE + _DIFFERENTIATES)


def _velocity_divisor(m) -> int | None:
    found = _VELOCITY.search(_effect(m))
    return int(found.group(1)) if found else None


def _strength(hero) -> float:
    """HD's primary STR: what the character always has, in his Hero
    identity. Not HD's secondary figure, which also counts STR powers whose
    limitations may keep them from adding damage; an unlimited STR power is
    stacked on this by `_Reacher`, a limited one reported (R14)."""
    (ch,) = [c for c in hero.characteristics if c.xmlid == "STR"] or [None]
    if ch is None:
        return 0.0
    return float(ch.get_primary_value(hero))


def _is_ranged(obj) -> bool:
    return (getattr(obj, "range_value", 0) or 0) != 0 and not _is_mental(obj)


def _is_mental(obj) -> bool:
    return (getattr(obj, "defense", "") or "").upper() == "MENTAL" or \
        "MENTAL" in (getattr(obj, "types", None) or ())


def _is_physical(obj) -> bool:
    return (getattr(obj, "defense", "") or "").upper() == "NORMAL"


def _limits_use(obj) -> bool:
    """A STR power whose use is cut short by a limitation whose words say
    how (Limited Power, a required roll): whether it adds damage is in free
    text."""
    return any((getattr(m, "xmlid", "") or "").upper() in ("LIMITEDPOWER",)
               for m in (getattr(obj, "assigned_modifiers", None) or []))


def _framework_name(obj) -> str:
    parent = getattr(obj, "parent", None)
    return (getattr(parent, "name", None) or "") if parent is not None else ""


class _Reacher:
    def __init__(self, hero, limit):
        from kirby_cost.builder.limits import _parts
        from kirby_cost.engine.movement import best_move_through_velocity
        from kirby_cost.engine.weapons import is_weapon
        from kirby_cost.objects.martial_arts.extra_damage_classes import ExtraDamageClasses
        from kirby_cost.objects.martial_arts.maneuver import Maneuver
        from kirby_cost.objects.martial_arts.ranged_damage_classes import RangedDamageClasses

        self.hero, self.limit = hero, limit
        self.adders = set(limit.adders)
        self.unmeasured: dict[str | None, Unmeasured] = {}
        self.strength = _strength(hero)
        self.str_dcs = str_damage_classes(int(self.strength))
        self.maneuvers = [m for m in hero.maneuvers if isinstance(m, Maneuver)]
        self.extra_hth = sum(int(m.levels) for m in hero.maneuvers
                             if isinstance(m, ExtraDamageClasses))
        self.extra_ranged = sum(int(m.levels) for m in hero.maneuvers
                                if isinstance(m, RangedDamageClasses))
        velocity = best_move_through_velocity(hero, in_hero_id=True)
        self.velocity = velocity.meters if velocity is not None else 0.0
        self.csls = [obj for section in ("skills", "powers", "talents", "perks")
                     for obj in (getattr(hero, section, None) or [])
                     if (getattr(obj, "xmlid", "") or "").upper() == "COMBAT_LEVELS"]
        self.deadly = [t for t in (getattr(hero, "talents", None) or [])
                       if (getattr(t, "xmlid", "") or "").upper() == "DEADLYBLOW"]
        self.bases: list[_Base] = []
        if self.strength > 0:
            self.bases.append(_Base(None, "STR", ("Strike",),
                                    float(self.str_dcs), True, False, False,
                                    False, False, True))
        for section in ("powers", "equipment"):
            for obj in _measured_purchases_in(hero, section):
                for part in _parts(obj):
                    if not getattr(part, "does_damage", False):
                        continue
                    xmlid = (part.xmlid or "").upper()
                    dcs = damage_classes_of(part, limit.counts)
                    names = tuple(n for n in (part.name, _framework_name(part),
                                              _framework_name(obj)) if n)
                    ha = xmlid == "HANDTOHANDATTACK"
                    strength = xmlid == "STR"
                    ranged, mental = _is_ranged(part), _is_mental(part)
                    if strength and _limits_use(part):
                        self._note(str(part.id), (
                            f"STR power {part.name or xmlid!r} carries Limited Power, so "
                            "whether it adds damage is in its own words; the Damage "
                            "Classes limit measures it alone and does not stack it on STR"))
                        strength = False
                    # An HA counts as STR damage (6E2 101); an unlimited STR
                    # power adds its STR to the character's. One that affects
                    # HD's primary figure is already inside `self.strength`,
                    # so only what it adds beyond its STR (an Advantage,
                    # say) is its own: its levels / 5 come off (STR is a
                    # point a point, 6E1 137).
                    stacks_on_str = ha or strength
                    if strength and getattr(part, "affects_primary", False):
                        dcs -= float(part.levels) / 5.0
                    self.bases.append(_Base(
                        str(part.id), part.name or xmlid, names,
                        dcs + (self.str_dcs if stacks_on_str else 0), not ranged and not mental,
                        ranged, xmlid in ("HKA", "RKA") or getattr(part, "killing", False) is True,
                        is_weapon(part, section=section) or is_weapon(obj, section=section),
                        xmlid == "HKA", stacks_on_str, _is_physical(part),
                        dcs if stacks_on_str else 0.0))
        # Maneuvers that differentiate rather than add (Killing / NND
        # strikes, R6) are attacks of their own.
        for m in self.maneuvers:
            if _deals_damage(m) and not _adds_dice(m):
                own = float(m.total_dc_no_str) + (self.str_dcs if m.add_str else 0)
                self.bases.append(_Base(str(m.id), m.display or "maneuver",
                                        (m.display or "",), own, m.category.upper() != "RANGED",
                                        m.category.upper() == "RANGED", False, False,
                                        False, False))

    # -- adders ------------------------------------------------------------

    def _note(self, hd_id, detail):
        self.unmeasured.setdefault(hd_id, Unmeasured(hd_id, detail))

    def _csl_dcs(self, base: _Base, labels: tuple[str, ...]) -> float:
        """R8: 2 levels a DC, over every level that reaches this attack."""
        if AddedDamage.CSL not in self.adders or not (base.hth or base.ranged):
            return 0.0
        every = [(b.names, b.ranged) for b in self.bases] + [
            ((m.display or "",), m.category.upper() == "RANGED") for m in self.maneuvers] + [
            (("Haymaker",), False), (("Move By",), False), (("Move Through",), False)]
        levels = 0
        for csl in self.csls:
            answers = reach_on(csl, every + [(labels, base.ranged)])
            mine = answers[-1]
            if mine is Reach.YES:
                levels += int(csl.levels)
            elif mine is Reach.UNKNOWN:
                self._note(str(csl.id), (
                    f"Combat Skill Levels {csl.name or csl.alias!r} name no attack "
                    "on this build, so the Damage Classes limit cannot count them "
                    "(6E1 72: a level reaches only what it was bought for)"))
        return float(levels // 2)

    def _deadly_dcs(self, base: _Base) -> float:
        """R13: +3 DCs a level, Killing Attacks with weapons, HKA or RKA."""
        if AddedDamage.DEADLY_BLOW not in self.adders or not (base.killing and base.weapon):
            return 0.0
        total = 0.0
        for talent in self.deadly:
            text = " ".join(filter(None, (talent.name, getattr(talent, "alias", None),
                                          getattr(talent, "input", None)))).upper()
            says_hka = bool(re.search(r"\bHKA\b|HAND[- ]TO[- ]HAND", text))
            says_rka = bool(re.search(r"\bRKA\b|RANGED", text))
            if says_hka == says_rka:
                self._note(str(talent.id), (
                    f"Deadly Blow {talent.name or talent.alias!r} does not say whether "
                    "it is bought for HKAs or RKAs (6E1 115), so the Damage Classes "
                    "limit cannot count it"))
                continue
            if says_rka == base.ranged:
                total += 3.0 * int(talent.levels)
        return total

    def _maneuver_fits(self, base: _Base, m) -> bool:
        """R12: a maneuver with this base. Unarmed bases and a bare HKA take
        it directly; a weapon needs an Element (or a weapon-based style)."""
        from kirby_cost.engine.weapons import element_reach

        if (m.category.upper() == "RANGED") != base.ranged:
            return False
        if base.unarmed:
            return not m.use_weapon
        if not base.weapon:
            return base.hka and not m.use_weapon
        if m.use_weapon:
            return True
        reach = element_reach(self.hero, base.names)
        if reach is Reach.UNKNOWN:
            self._note(base.hd_id, (
                f"{base.label!r} is a weapon, but no Weapon Element on this build can "
                "be told to cover it (6E2 94), so the Damage Classes limit cannot say "
                "whether Martial Maneuvers add to it"))
        return reach is Reach.YES

    # -- one attack ----------------------------------------------------------

    def best(self, base: _Base) -> Reached:
        options: list[Reached] = []
        vel = self.velocity if AddedDamage.VELOCITY in self.adders else 0.0
        str_adds = (AddedDamage.STR in self.adders and base.hth and base.physical
                    and not base.unarmed and (base.hka or base.weapon))
        str_part = float(self.str_dcs) if str_adds else 0.0

        def option(label, parts, base_dcs, maneuver_name):
            labels = base.names + ((maneuver_name,) if maneuver_name else ())
            csl = self._csl_dcs(base, labels)
            deadly = self._deadly_dcs(base)
            parts = list(parts)
            if csl:
                parts.append(("CSLs", csl))
            if deadly:
                parts.append(("Deadly Blow", deadly))
            total = sum(v for _, v in parts)
            if self.limit.doubling:
                total = min(total, 2 * base_dcs)
            options.append(Reached(base.hd_id, label, total, tuple(parts)))

        base_part = ("STR", float(self.str_dcs)) if base.hd_id is None else ("base", base.dcs)
        plain = [base_part] + ([("STR", str_part)] if str_part else [])
        option(base.label, plain, base.dcs, None)
        if base.hth and not base.ranged and base.physical:
            if AddedDamage.HAYMAKER in self.adders:
                option(f"Haymaker with {base.label}", plain + [("Haymaker", 4.0)],
                       base.dcs, "Haymaker")
            if vel:
                if base.unarmed:
                    half = float(str_damage_classes(int(self.strength / 2)))
                    by = [("STR/2", half)] + ([("HA", base.ha_dcs)] if base.ha_dcs else [])
                else:
                    by = [base_part] + ([("STR/2", float(str_damage_classes(int(self.strength / 2))))]
                                        if str_part else [])
                option(f"Move By with {base.label}", by + [("v/10", float(int(vel // 10)))],
                       base.dcs, "Move By")
                option(f"Move Through with {base.label}", plain + [("v/6", float(int(vel // 6)))],
                       base.dcs, "Move Through")
        if AddedDamage.MARTIAL in self.adders and base.physical:
            extra = self.extra_ranged if base.ranged else self.extra_hth
            for m in self.maneuvers:
                if not _adds_dice(m) or not self._maneuver_fits(base, m):
                    continue
                parts = list(plain)
                if base.unarmed and m.add_str is False:
                    parts = [p for p in parts if p[0] != "STR"]
                parts.append((m.display, float(m.dcs)))
                if extra:
                    parts.append(("Extra DCs", float(extra)))
                div = _velocity_divisor(m)
                if div and vel:
                    parts.append((f"v/{div}", float(int(vel // div))))
                doubling_base = base.dcs + (extra if base.unarmed else 0)
                option(f"{m.display} with {base.label}", parts, doubling_base, m.display)
        return max(options, key=lambda r: r.dcs)


def _measured_purchases_in(hero, section):
    """`limits._measured_purchases`, one section at a time (a weapon is
    told by its section)."""
    from kirby_cost.objects.list import List

    for obj in getattr(hero, section, None) or []:
        if not isinstance(obj, List):
            yield obj


def reach(hero, limit) -> tuple[list[Reached], list[Unmeasured]]:
    """Every attack on ``hero`` at its best under ``limit``'s adders, and
    what the build's words could not settle."""
    from kirby_cost.engine.allocation import _bought_on

    with _bought_on(hero):
        r = _Reacher(hero, limit)
        reached = [r.best(b) for b in r.bases]
    return reached, list(r.unmeasured.values())


__all__ = ["AddedDamage", "Reached", "Unmeasured", "reach"]
