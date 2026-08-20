"""
Shrinking power class for kirby-cost.

Converted from com.hero.objects.powers.Shrinking.java

Power to reduce character size.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_half_up
import math


class Shrinking(Power, xmlid="SHRINKING"):
    """
    Shrinking power.
    
    Reduces character size, affecting mass, height, and various characteristics.
    """
    
    def __init__(self):
        """Initialize a Shrinking power."""
        super().__init__()
        self.xmlid = Shrinking.XMLID
        self._duration = "CONSTANT"
        # Stub: would initialize mass/height multipliers and characteristic increases
    
    @property
    def damage_display(self) -> str:
        """Get shrinking display (HTML formatted)."""
        return f"<html>{self.plain_damage_display}</html>"
    
    @property
    def plain_damage_display(self) -> str:
        """Get plain shrinking display string."""
        # Stub: would calculate mass, height, STR, BODY, STUN, DCV, PER, KB, reach
        # For now, return simplified version
        return f"{self._levels} levels"
    
    def _plain_damage_display(self) -> str:
        """``0.0314 m tall, 0.0004 kg mass, -12 PER Rolls to perceive character``.

        Ported from ``Shrinking.getPlainDamageDisplay`` (6E branch). A
        Shrinking is not "6 levels" — the levels are what was paid, and HD
        prints what they BOUGHT: how tall the character now is, what they
        weigh, and how much harder they are to see.

        The 6E line is a strict subset of the 5E one — size, weight, PER, DCV,
        knockback — dropping the STR, BODY, STUN and reach clauses that 5E
        showed. Both are built here and the edition picks.

        The number format switches to scientific notation below a threshold,
        which is HD's, not a rounding convenience: a character shrunk far
        enough is genuinely 3.14E-5 metres tall and no fixed-point rendering
        of that says anything.
        """
        from kirby_cost.util.rounder import round_half_up
        from kirby_cost.objects.base import GenericObject, is_6e

        hero = _active_hero()
        if hero is None:
            return f"{self._levels} levels"

        levels = self._levels

        # Mass. HD works in grams and prints kilograms.
        # Java: `weight * 453.5924` — the hero's weight is in POUNDS, and only
        # the metric preference makes it `* 1000`. `Hero.getWeight()` is an
        # int too, for the same reason getHeight() is.
        grams = int(round_half_up(hero.weight)) * 453.5924
        if GenericObject.find_object_by_id(self.assigned_modifiers, "NORMALMASS") is None:
            if self.mass_multiplier_levels:
                grams *= self.mass_multiplier ** (levels / self.mass_multiplier_levels)
        weight = _sig(grams / 1000.0, 0.00009) + " kg mass, "

        def scaled(increase: float, per_levels: int) -> int:
            if not per_levels:
                return 0
            return int(round_half_up(increase * round_half_up(levels / per_levels)))

        per = scaled(self.per_increase, self.per_increase_levels)
        # HD writes the sign itself for a positive PER and lets a negative
        # carry its own minus.
        per_str = (f"+{per} PER Rolls to perceive character, " if per > 0
                   else f"{per} PER Rolls to perceive character, " if per else "")
        dcv = scaled(self.dcv_increase, self.dcv_increase_levels)
        dcv_str = f"{'+' if dcv > 0 else ''}{dcv} DCV, " if dcv else ""

        kb = scaled(self.kb_increase, self.kb_increase_levels)
        show_kb = True
        normal_mass = GenericObject.find_object_by_id(
            self.assigned_modifiers, "NORMALMASS")
        if normal_mass is not None:
            opt = getattr(normal_mass, "selected_option", None)
            if opt is not None and (opt.xmlid or "").upper() == "ALWAYS":
                show_kb = False
        kb_str = ""
        if is_6e() and show_kb and kb:
            kb_str = f"takes {'+' if kb > 0 else ''}{kb}m KB, "

        # Height, in metres. The hero's height is inches unless metric.
        # `Hero.getHeight()` returns an INT — `(int) roundHalfUp(height)` — so
        # a 78.74-inch character is 79 inches here, not 78.74. That is the
        # whole of the discrepancy: 78.74 x 2.54 x 0.5^6 is 3.125cm and prints
        # "0.0312", while 79 x 2.54 x 0.5^6 is 3.1353cm and prints "0.0314",
        # which is what the oracle says. The rounding happens BEFORE the
        # conversion and before the shrink, so it is not a display nicety — it
        # changes the number.
        inches = int(round_half_up(hero.height))
        cm = inches * 2.54
        if levels >= self.height_increase_levels and self.height_increase_levels:
            cm = (inches * 2.54
                  * (self.height_increase ** (levels / self.height_increase_levels)))
        size = _sig(cm / 100.0) + " m tall, "

        ret = size + weight + per_str + dcv_str + kb_str
        return ret[:-2] if len(ret) >= 2 else ret

    @property
    def column2_output(self) -> str:
        """``Shrinking (0.0314 m tall, 0.0004 kg mass, -12 PER Rolls...)``.

        Ported from ``Shrinking.getColumn2Output``. The bracket holds what the
        levels bought, not the levels.
        """
        from kirby_cost.objects.base import option_alias
        ret = f"{self.alias or ''} ({self._plain_damage_display()})"
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


def _sig(value: float, threshold: float = 0.0009) -> str:
    """HD's number format: four decimals normally, scientific below a
    threshold — which is 0.0009 for the height and 0.00009 for the mass.

    ``DecimalFormat("#.####")`` and ``DecimalFormat("#.###E0")`` — the
    threshold is HD's and the switch matters: a character shrunk far enough is
    genuinely 3.14E-5 metres tall.
    """
    if value > threshold:
        text = f"{value:.4f}".rstrip("0").rstrip(".")
        return text or "0"
    mantissa = f"{value:.3E}"
    num, exp = mantissa.split("E")
    num = num.rstrip("0").rstrip(".")
    return f"{num}E{int(exp)}"


def _active_hero():
    """The character whose height and weight are being shrunk."""
    try:
        from kirby_cost.core.context import EngineContext
        return EngineContext.active_hero()
    except Exception:  # noqa: BLE001
        return None
