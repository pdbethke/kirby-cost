"""
Density Increase power class for kirby-cost.

Converted from com.hero.objects.powers.DensityIncrease.java

Power to increase character density.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_half_up
import math


class DensityIncrease(Power, xmlid="DENSITYINCREASE"):
    """
    Density Increase power.
    
    Increases character density, affecting mass, STR, PD/ED, and KB.
    """
    
    def __init__(self):
        """Initialize a Density Increase power."""
        super().__init__()
        self.xmlid = DensityIncrease.XMLID
        self._duration = "CONSTANT"
        # Stub: would initialize mass multiplier and characteristic increases
    
    @property
    def damage_display(self) -> str:
        """``6,400 kg mass, +30 STR, +6 PD/ED, -12m KB``.

        Ported from ``DensityIncrease.getDamageDisplay``. Density Increase is
        not "6 levels" — the levels are what was paid and HD prints what they
        bought: the new mass, the strength, the defences and the knockback
        resistance.

        The mass is rounded to the nearest hundred grams and then back to
        kilograms, which is HD's double-rounding and not a simplification: a
        character at 6,400 kg is not 6,384.

        NODEFINCREASE names WHICH defence was declined, so the clause is
        rewritten rather than dropped — "+6 PD" when ED was waived, "+6 ED"
        when PD was, and nothing at all when both were.
        """
        from kirby_cost.util.rounder import round_half_up
        from kirby_cost.objects.base import GenericObject, is_6e

        hero = _active_hero()
        if hero is None:
            return f"{self._levels} levels"
        levels = self._levels

        grams = round_half_up(int(round_half_up(hero.weight)) * 453.5924)
        if self.mass_multiplier_levels:
            grams = grams * int(self.mass_multiplier ** (levels / self.mass_multiplier_levels))
        kilos = round(round(grams / 100000.0) * 100)
        weight = f"{int(kilos):,} kg mass"

        def scaled(increase: float, per_levels: int) -> int:
            if not per_levels:
                return 0
            return int(round_half_up(increase * round_half_up(levels / per_levels)))

        strength = f"+{scaled(self.str_increase, self.str_increase_levels)} STR"

        pded = scaled(self.pd_increase, self.pd_increase_levels)
        defence = f"+{pded} PD/ED"
        no_def = GenericObject.find_object_by_id(self.assigned_modifiers, "NODEFINCREASE")
        if no_def is not None:
            opt = (getattr(getattr(no_def, "selected_option", None), "xmlid", "") or "").upper()
            if opt == "PD":
                defence = f"+{scaled(self.ed_increase, self.ed_increase_levels)} ED"
            elif opt == "ED":
                defence = f"+{pded} PD"
            elif opt == "PDED":
                defence = None

        kb = scaled(self.kb_increase, self.kb_increase_levels)
        if is_6e():
            kb_str = f"{'' if kb < 0 else '+'}{kb * 2}m KB"
        else:
            kb_str = f"{'' if kb < 0 else '+'}{kb}\" KB"

        parts = [weight, strength]
        if defence is not None:
            parts.append(defence)
        parts.append(kb_str)
        return ", ".join(parts)
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = f"{self._alias} ({self.damage_display})"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        if self.input and self.input.strip():
            output += f":  {self.input}"
        
        adder_str = self.adder_string
        if adder_str and adder_str.strip():
            output += f", {adder_str}"
        
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    
    @property
    def levels(self) -> int:
        """Get levels (capped at 50)."""
        levels = self._levels
        return min(levels, 50)

    @levels.setter
    def levels(self, value) -> None:
        self._levels = value
    
    @property
    def str_increase(self) -> float:
        """Get STR increase (checks for NOSTRINCREASE modifier)."""
        # Stub: would check for NOSTRINCREASE modifier
        return self._str_increase

    @str_increase.setter
    def str_increase(self, value: float) -> None:
        self._str_increase = value

    @property
    def pd_increase(self) -> float:
        """Get PD increase (checks for NODEFINCREASE modifier)."""
        # Stub: would check for NODEFINCREASE modifier
        return self._pd_increase

    @pd_increase.setter
    def pd_increase(self, value: float) -> None:
        self._pd_increase = value

    @property
    def ed_increase(self) -> float:
        """Get ED increase (checks for NODEFINCREASE modifier)."""
        # Stub: would check for NODEFINCREASE modifier
        return self._ed_increase

    @ed_increase.setter
    def ed_increase(self, value: float) -> None:
        self._ed_increase = value
    
    



def _active_hero():
    """The character whose mass is being increased."""
    try:
        from kirby_cost.core.context import EngineContext
        return EngineContext.active_hero()
    except Exception:  # noqa: BLE001
        return None
