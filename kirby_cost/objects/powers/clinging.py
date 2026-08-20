"""
Clinging power class for kirby-cost.

Converted from com.hero.objects.powers.Clinging.java

Power to cling to surfaces.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_half_up


class Clinging(Power, xmlid="CLINGING"):
    """
    Clinging power.
    
    Power to cling to surfaces with enhanced STR.
    """
    
    def __init__(self):
        """Initialize a Clinging power."""
        super().__init__()
        self.xmlid = Clinging.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get clinging display."""
        return ""  # Display is in column2_output
    
    @property
    def column2_output(self) -> str:
        """``Clinging (21 STR)`` — the character's STR plus what was bought.

        Ported from ``Clinging.getColumn2Output``. Clinging is not a strength
        of its own: it adds to the character's, so the number printed is
        STR + levels. Printing the levels alone was off by exactly the
        character's STR, which for a normal one is 10 and looked like an
        off-by-one.

        Usable On Others is the exception — the OTHER character's strength is
        not known, so HD prints levels + 10, the assumed normal.
        """
        from kirby_cost.objects.base import GenericObject, option_alias
        from kirby_cost.util.rounder import round_half_up
        from kirby_cost.util.constants import CharacteristicType

        ret = f"{self.alias or ''} ("
        uaa = False
        uoo = GenericObject.find_object_by_id(self.all_assigned_modifiers, "UOO")
        if uoo is not None:
            opt = getattr(uoo, "selected_option", None)
            if opt is not None and (opt.xmlid or "").upper() == "UAA":
                uaa = True

        if uaa:
            ret += f"{self._levels + 10} STR"
        elif self._levels == 0:
            ret += "normal STR)"
        else:
            hero = _active_hero()
            strength = hero.characteristic(CharacteristicType.STR) if hero else None
            if strength is None:
                ret += f"{self._levels} STR)"
            else:
                v1 = strength.get_primary_value(hero)
                v2 = strength.get_secondary_value(hero)
                if v1 != v2:
                    ret += (f"{int(round_half_up(self._levels + v1))}/"
                            f"{int(round_half_up(self._levels + v2))} STR)")
                else:
                    ret += f"{int(round_half_up(self._levels + v1))} STR)"

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


def _active_hero():
    """The character whose STR the clinging adds to."""
    try:
        from kirby_cost.core.context import EngineContext
        return EngineContext.active_hero()
    except Exception:  # noqa: BLE001
        return None
