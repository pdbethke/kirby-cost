"""
Mental Defense power class for kirby-cost.

Converted from com.hero.objects.powers.MentalDefense.java

Defense against mental attacks.
"""

from kirby_cost.objects.base import option_alias
from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_half_down, round_half_up


class MentalDefense(Power, xmlid="MENTALDEFENSE"):
    """
    Mental Defense power.
    
    Defense against mental attacks.
    """
    
    def __init__(self):
        """Initialize a Mental Defense power."""
        super().__init__()
        self.xmlid = MentalDefense.XMLID
        self._duration = "CONSTANT"
    
    @property
    def md_levels(self) -> int:
        """Every point of Mental Defense the character has, not just this one's.

        Ported from ``MentalDefense.getMdLevels``. HD prints a running TOTAL
        on each Mental Defense: this power's levels plus every other Mental
        Defense in powers and equipment (CompoundPowers included) plus the
        Mental Defense any Force Field supplies. A character with two of them
        sees the same total on both lines.
        """
        total = self._levels
        hero = _active_hero()
        if hero is None:
            return total

        def add(obj) -> int:
            from kirby_cost.objects.powers.force_field import ForceField
            if isinstance(obj, MentalDefense):
                return obj._levels if obj._id != self._id else 0
            if isinstance(obj, ForceField):
                return obj.md_levels
            return 0

        for group in (getattr(hero, "powers", None) or (),
                      getattr(hero, "equipment", None) or ()):
            for obj in group:
                total += add(obj)
                for sub in (getattr(obj, "powers", None) or ()):
                    total += add(sub)
        return total

    @property
    def damage_display(self) -> str:
        """``8 points total``.

        The 5E branch adds EGO/5; every template in this corpus is 6E, where
        the points are the points.
        """
        return f"{self.md_levels} points total"

    @property
    def column2_output(self) -> str:
        """``Mental Defense (8 points total)``.

        Ported from ``MentalDefense.getColumn2Output``. The bracket is part of
        the shape here rather than something adders opened, and the levels
        appear in front ONLY when this is not the first Mental Defense the
        character has — the first one's contribution is already inside the
        total, so repeating it would say the same number twice.
        """
        ret = f"{self.alias or ''} ({self.damage_display})"
        if not self._is_first_mental_defense():
            ret = f"+{self._levels} {ret}"
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        if self.input and self.input.strip():
            ret += f":  {self.input}"
        option = (option_alias(self) or "").strip()
        adders = self.adder_string
        if option:
            ret += f" ({option}"
            if adders.strip():
                ret += f"; {adders}"
            ret += ")"
        elif adders.strip():
            ret += f" ({adders})"
        ret += self.modifier_string
        ret += self._end_reserve_note()
        return ret

    def _is_first_mental_defense(self) -> bool:
        """Whether this is the first Mental Defense in the list HD searches.

        Java breaks out of the loop at the FIRST MentalDefense it finds and
        asks whether that one is this one — so it is genuinely "first in the
        list", not "the only one".
        """
        hero = _active_hero()
        if hero is None:
            return True
        group = (getattr(hero, "equipment", None) or ()) if self._is_equipment \
            else (getattr(hero, "powers", None) or ())
        for obj in group:
            if isinstance(obj, MentalDefense):
                return obj._id == self._id
        return False
    
    @property
    def active_cost(self) -> float:
        """
        Calculate active cost for Mental Defense.
        
        In 5E, includes EGO/5 bonus. In 6E, just base cost.
        """
        total_cost = self.total_cost
        
        # Stub: would check if 6E and get EGO characteristic
        # For now, return standard active cost
        return super().active_cost



def _active_hero():
    """The character whose Mental Defense adds up with this one's."""
    try:
        from kirby_cost.core.context import EngineContext
        return EngineContext.active_hero()
    except Exception:  # noqa: BLE001
        return None
