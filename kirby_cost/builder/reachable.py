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
R15 Slots of one framework stack only as far as its points allow: a
    Multipower's slots on together fit its reserve (a Fixed slot at its
    Active Points, a Variable one at any share up to them), allocated once a
    Phase, so for the whole attack; a VPP's powers fit its Pool in Real
    Points (6E1 401, 404-405, 410, 411, 413; `engine.allocation`). A VPP
    can build any power up to its Control Cost, so it is reported.
"""
from __future__ import annotations

import itertools
import re
from dataclasses import dataclass
from enum import Enum

from kirby_cost.engine.allocation import fits, pool_of, shares
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
    its DCs, the parts that make them up, and the framework points it needs
    when that is news to a reader: a framework holding a slot other than
    the attack, two slots, or a Variable slot below its full share (R15). Each entry is
    (framework name, its reserve or Pool, ((slot name, points), ...))."""

    hd_id: str | None
    label: str
    dcs: float
    parts: tuple[tuple[str, float], ...]
    reserve: tuple[tuple[str, int, tuple[tuple[str, int], ...]], ...]

    def describe(self) -> str:
        if len(self.parts) == 1 and self.parts[0][0] in ("base", "STR") and not self.reserve:
            return f"Damage Classes {self.dcs:g}"
        body = " + ".join(f"{name} {value:g}" for name, value in self.parts)
        for fw, pool, slots in self.reserve:
            body += f"; {fw} {pool}: " + " + ".join(f"{n} {p}" for n, p in slots)
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
    #: The attack's own DCs, STR not included.
    own: float
    #: STR Normal Damage underneath (STR itself, an HA, a STR power, a
    #: maneuver that adds STR): the character's STR is part of the base (R1).
    adds_str: bool
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
    physical: bool
    #: The framework share the attack is on at (R15); () in no framework.
    shares: tuple


@dataclass(frozen=True)
class _Strength:
    """The character's STR with the framework slots that feed it on."""

    value: float
    shares: tuple


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


def _primary_strength(hero) -> float:
    """HD's primary STR: what the character always has, in his Hero
    identity. Not HD's secondary figure, which also counts STR powers whose
    limitations may keep them from adding damage. `_Reacher` adds every
    unlimited STR power to it, reports a limited one (R14), and takes a
    framework slot out unless its share is on (R15)."""
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


def _slot_name(obj) -> str:
    return (getattr(obj, "name", None) or getattr(obj, "xmlid", "") or "").strip()


def _reserve(on, attack) -> tuple:
    """The frameworks worth naming in a result (`Reached.reserve`): any
    holding a slot other than the attack's own (``attack``, its shares), a
    slot below its full share, or two slots."""
    by_fw: dict[int, list] = {}
    for share in on:
        group = by_fw.setdefault(id(share.framework), [])
        if all(s.slot is not share.slot for s in group):
            group.append(share)
    out = []
    for group in by_fw.values():
        own = {id(a.slot) for a in attack}
        if len(group) < 2 and all(s.power is s.slot and id(s.slot) in own for s in group):
            continue
        fw = group[0].framework
        out.append(((getattr(fw, "name", None) or fw.xmlid).strip(), pool_of(group[0].slot),
                    tuple((_slot_name(s.slot), s.points) for s in group)))
    return tuple(out)


class _Reacher:
    def __init__(self, hero, limit):
        from kirby_cost.builder.limits import _parts
        from kirby_cost.engine.movement import move_through_velocities
        from kirby_cost.engine.weapons import is_weapon
        from kirby_cost.objects.frameworks.vpp import VariablePowerPool
        from kirby_cost.objects.martial_arts.extra_damage_classes import ExtraDamageClasses
        from kirby_cost.objects.martial_arts.maneuver import Maneuver
        from kirby_cost.objects.martial_arts.ranged_damage_classes import RangedDamageClasses

        self.hero, self.limit = hero, limit
        self.adders = set(limit.adders)
        self.unmeasured: dict[str | None, Unmeasured] = {}
        self.maneuvers = [m for m in hero.maneuvers if isinstance(m, Maneuver)]
        self.extra_hth = sum(int(m.levels) for m in hero.maneuvers
                             if isinstance(m, ExtraDamageClasses))
        self.extra_ranged = sum(int(m.levels) for m in hero.maneuvers
                                if isinstance(m, RangedDamageClasses))
        self.velocities = (move_through_velocities(hero, in_hero_id=True)
                           if AddedDamage.VELOCITY in self.adders else [])
        # Either may be bought as a framework slot, in Powers (R15).
        every = [obj for section in ("skills", "powers", "talents", "perks")
                 for obj in (getattr(hero, section, None) or [])]
        self.csls = [o for o in every if (getattr(o, "xmlid", "") or "").upper() == "COMBAT_LEVELS"]
        self.deadly = [o for o in every if (getattr(o, "xmlid", "") or "").upper() == "DEADLYBLOW"]
        # STR: HD's primary figure, plus every unlimited STR power (STR is
        # STR, 6E2 101, whether HD folds it into the primary figure or not),
        # framework slots only in the sets their frameworks hold at once
        # (R15; 6E1 404: no number limit, only the points).
        primary = _primary_strength(hero)
        bare, slotted = primary, []
        for p in hero.powers:
            if (p.xmlid or "").upper() != "STR":
                continue
            folded = bool(getattr(p, "affects_primary", False))
            if _limits_use(p):
                # Reported, never stacked (R14): out of the primary figure
                # too when HD folds it in.
                bare -= float(p.levels) if folded else 0.0
                continue
            held = shares(p, hero=hero)
            if held:
                bare -= float(p.levels) if folded else 0.0
                slotted.append(held)
            elif not folded:
                bare += float(p.levels)
        self.strengths = []
        for pick in itertools.product(*[[None] + held for held in slotted]):
            on = tuple(s for s in pick if s is not None)
            if fits(on):
                self.strengths.append(
                    _Strength(bare + sum(float(s.power.levels) for s in on), on))
        self.bases: list[_Base] = []
        if any(st.value > 0 for st in self.strengths):
            self.bases.append(_Base(None, "STR", ("Strike",), 0.0, True, True, False,
                                    False, False, False, True, True, ()))
        for section in ("powers", "equipment"):
            for obj in _measured_purchases_in(hero, section):
                held = shares(obj, hero=hero)
                if isinstance(getattr(obj, "parent", None), VariablePowerPool):
                    vpp = obj.parent
                    for part in _parts(obj):
                        if getattr(part, "does_damage", False):
                            self._note(str(vpp.id), (
                                f"Variable Power Pool {_slot_name(vpp)!r} can build any power "
                                "up to its Control Cost (6E1 411), so the Damage Classes limit "
                                "measures the powers it holds now"))
                for part in _parts(obj):
                    if not getattr(part, "does_damage", False):
                        continue
                    # A slot on at each of its shares (R15); a compound's
                    # parts only as bought.
                    ways = ([(s.power, (s,)) for s in reversed(held)] if part is obj and held
                            else [(part, held[-1:])])
                    for power, on in ways:
                        self._add_base(power, part, obj, section, on, is_weapon)
        # Maneuvers that differentiate rather than add (Killing / NND
        # strikes, R6) are attacks of their own.
        for m in self.maneuvers:
            if _deals_damage(m) and not _adds_dice(m):
                self.bases.append(_Base(str(m.id), m.display or "maneuver",
                                        (m.display or "",), float(m.total_dc_no_str),
                                        bool(m.add_str), m.category.upper() != "RANGED",
                                        m.category.upper() == "RANGED", False, False,
                                        False, False, True, ()))

    def _add_base(self, power, part, obj, section, on, is_weapon):
        xmlid = (part.xmlid or "").upper()
        dcs = damage_classes_of(power, self.limit.counts)
        names = tuple(n for n in (part.name, _framework_name(part), _framework_name(obj)) if n)
        ha = xmlid == "HANDTOHANDATTACK"
        strength = xmlid == "STR"
        ranged, mental = _is_ranged(part), _is_mental(part)
        if strength and _limits_use(part):
            self._note(str(part.id), (
                f"STR power {part.name or xmlid!r} carries Limited Power, so "
                "whether it adds damage is in its own words; the Damage "
                "Classes limit measures it alone and does not stack it on STR"))
            strength = False
        # An HA counts as STR damage (6E2 101); an unlimited STR power's STR
        # is in the character's (`self.strengths`), so only what it adds
        # beyond its STR (an Advantage, say) is its own: its levels / 5 come
        # off (STR is a point a point, 6E1 137).
        if strength:
            dcs -= float(power.levels) / 5.0
        stacks_on_str = ha or strength
        self.bases.append(_Base(
            str(part.id), part.name or xmlid, names, dcs, stacks_on_str,
            not ranged and not mental, ranged,
            xmlid in ("HKA", "RKA") or getattr(part, "killing", False) is True,
            is_weapon(part, section=section) or is_weapon(obj, section=section),
            xmlid == "HKA", stacks_on_str, _is_physical(part), tuple(on)))

    # -- adders ------------------------------------------------------------

    def _note(self, hd_id, detail):
        self.unmeasured.setdefault(hd_id, Unmeasured(hd_id, detail))

    def _csl_levels(self, csl, base: _Base, labels: tuple[str, ...]) -> int:
        """R8: the levels of one CSL that reach this attack."""
        if AddedDamage.CSL not in self.adders or not (base.hth or base.ranged):
            return 0
        every = [(b.names, b.ranged) for b in self.bases] + [
            ((m.display or "",), m.category.upper() == "RANGED") for m in self.maneuvers] + [
            (("Haymaker",), False), (("Move By",), False), (("Move Through",), False)]
        mine = reach_on(csl, every + [(labels, base.ranged)])[-1]
        if mine is Reach.UNKNOWN:
            self._note(str(csl.id), (
                f"Combat Skill Levels {csl.name or csl.alias!r} name no attack "
                "on this build, so the Damage Classes limit cannot count them "
                "(6E1 72: a level reaches only what it was bought for)"))
        return int(csl.levels) if mine is Reach.YES else 0

    def _deadly_dcs(self, talent, base: _Base) -> float:
        """R13: +3 DCs a level to Killing Attacks involving weapons, HKA or
        RKA as bought (6E1 115). One defined for Normal Damage weapons
        instead is reported (R14)."""
        if AddedDamage.DEADLY_BLOW not in self.adders:
            return 0.0
        text = " ".join(filter(None, (talent.name, getattr(talent, "alias", None),
                                      getattr(talent, "input", None)))).upper()
        if re.search(r"\bNORMAL\b", text):
            self._note(str(talent.id), (
                f"Deadly Blow {talent.name or talent.alias!r} reads as bought for Normal "
                "Damage weapons (6E1 115), and which ones is in its words, so the Damage "
                "Classes limit cannot count it"))
            return 0.0
        if not (base.killing and base.weapon):
            return 0.0
        says_hka = bool(re.search(r"\bHKA\b|HAND[- ]TO[- ]HAND", text))
        says_rka = bool(re.search(r"\bRKA\b|RANGED", text))
        if says_hka == says_rka:
            self._note(str(talent.id), (
                f"Deadly Blow {talent.name or talent.alias!r} does not say whether "
                "it is bought for HKAs or RKAs (6E1 115), so the Damage Classes "
                "limit cannot count it"))
            return 0.0
        return 3.0 * int(talent.levels) if says_rka == base.ranged else 0.0

    def _extras(self, base: _Base, labels, on: tuple):
        """CSLs (R8) and Deadly Blow (R13) on this attack, beside ``on``:
        every one in no framework, and the best set of slotted ones that
        fits (R15). Returns (CSL DCs, Deadly Blow DCs, shares added)."""
        free_levels, free_deadly, slotted = 0, 0.0, []
        for csl in self.csls:
            levels = self._csl_levels(csl, base, labels)
            if levels:
                held = shares(csl, hero=self.hero)
                if held:
                    slotted.append([(levels, 0.0, s) for s in held])
                else:
                    free_levels += levels
        for talent in self.deadly:
            dcs = self._deadly_dcs(talent, base)
            if dcs:
                held = shares(talent, hero=self.hero)
                if held:
                    slotted.append([(0, dcs, s) for s in held])
                else:
                    free_deadly += dcs
        best = (float(free_levels // 2), free_deadly, ())
        for pick in itertools.product(*[[None] + ways for ways in slotted]):
            chosen = [p for p in pick if p is not None]
            if not chosen or not fits(on + tuple(p[2] for p in chosen)):
                continue
            levels = free_levels + sum(p[0] for p in chosen)
            got = (float(levels // 2), free_deadly + sum(p[1] for p in chosen),
                   tuple(p[2] for p in chosen))
            if got[0] + got[1] > best[0] + best[1]:
                best = got
        return best

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

    def best(self, base: _Base) -> Reached | None:
        """The most this attack reaches, over every STR the character can
        have on beside it; None when no STR it needs fits (R15)."""
        found = [r for st in self.strengths if fits(base.shares + st.shares)
                 for r in self._options(base, st)]
        return max(found, key=lambda r: r.dcs) if found else None

    def _options(self, base: _Base, st: _Strength) -> list[Reached]:
        options: list[Reached] = []
        str_dcs = float(str_damage_classes(int(st.value)))
        half_str = float(str_damage_classes(int(st.value / 2)))
        base_dcs = base.own + (str_dcs if base.adds_str else 0.0)
        str_adds = (AddedDamage.STR in self.adders and base.hth and base.physical
                    and not base.unarmed and (base.hka or base.weapon))
        str_part = str_dcs if str_adds else 0.0
        # The STR this option is measured at, with any slot that feeds it.
        on_str = base.shares + st.shares

        def option(label, parts, doubling_base, maneuver_name, on):
            labels = base.names + ((maneuver_name,) if maneuver_name else ())
            csl, deadly, extra_on = self._extras(base, labels, on)
            parts = list(parts)
            if csl:
                parts.append(("CSLs", csl))
            if deadly:
                parts.append(("Deadly Blow", deadly))
            total = sum(v for _, v in parts)
            if self.limit.doubling:
                total = min(total, 2 * doubling_base)
            options.append(Reached(base.hd_id, label, total, tuple(parts),
                                   _reserve(on + extra_on, base.shares)))

        def moving(on):
            """Each velocity whose slots fit beside ``on`` (R9, R15)."""
            return [v for v in self.velocities if fits(on + v.shares)]

        base_part = ("STR", str_dcs) if base.hd_id is None else ("base", base_dcs)
        plain = [base_part] + ([("STR", str_part)] if str_part else [])
        option(base.label, plain, base_dcs, None, on_str)
        if base.hth and not base.ranged and base.physical:
            if AddedDamage.HAYMAKER in self.adders:
                option(f"Haymaker with {base.label}", plain + [("Haymaker", 4.0)],
                       base_dcs, "Haymaker", on_str)
            for v in moving(on_str):
                on = on_str + v.shares
                if base.unarmed:
                    by = [("STR/2", half_str)] + ([("HA", base.own)] if base.own else [])
                else:
                    by = [base_part] + ([("STR/2", half_str)] if str_part else [])
                option(f"Move By with {base.label}",
                       by + [("v/10", float(int(v.meters // 10)))], base_dcs, "Move By", on)
                option(f"Move Through with {base.label}",
                       plain + [("v/6", float(int(v.meters // 6)))], base_dcs,
                       "Move Through", on)
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
                doubling_base = base_dcs + (extra if base.unarmed else 0)
                div = _velocity_divisor(m)
                label = f"{m.display} with {base.label}"
                option(label, parts, doubling_base, m.display, on_str)
                for v in (moving(on_str) if div else []):
                    option(label, parts + [(f"v/{div}", float(int(v.meters // div)))],
                           doubling_base, m.display, on_str + v.shares)
        return options


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
        best: dict[str | None, Reached] = {}
        for base in r.bases:
            got = r.best(base)
            held = best.get(base.hd_id)
            if got is not None and (held is None or got.dcs > held.dcs):
                best[base.hd_id] = got
    return list(best.values()), list(r.unmeasured.values())


__all__ = ["AddedDamage", "Reached", "Unmeasured", "reach"]
