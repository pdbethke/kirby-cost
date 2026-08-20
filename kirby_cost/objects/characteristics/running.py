"""
Running characteristic class.

Converted from com.hero.objects.characteristics.Running.java
"""

from typing import Optional, TYPE_CHECKING

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType
from kirby_cost.util.rounder import round_half_up

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero


class Running(Characteristic, xmlid="RUNNING"):
    """Running movement characteristic."""
    
    def __init__(self):
        """Initialize Running."""
        super().__init__(self.XMLID)
        self._display = "Running"
        # 6E1 p43: Running, 12m base, 1 Character Point per +1m.
        # Was 2.0 -- a 5E rate (5E charged 2 CP per +1"). The error was
        # invisible because a 6E template supplies the correct value and
        # apply_template overwrites this before any cost is computed.
        self._level_cost = 1.0
        self._level_value = 1.0
        self._minimum_cost = 2.0
        self._base_cost = 0.0
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.RUNNING)
    
    def roll(self, active_hero: Optional['Hero'] = None) -> str:
        """Running doesn't have a roll."""
        return ""
    
    def total_display(self, active_hero: Optional['Hero'] = None) -> str:
        """Get total movement display."""
        # 6E throughout: the template chain is Main6E and the corpus is 6E,
        # so this "would need template access" stub had exactly one answer and
        # was giving the other. It printed inches on every movement
        # characteristic in the corpus.
        is_6e = True
        
        active_hero = active_hero or _active_hero()
        primary = self.get_primary_value(active_hero)
        secondary = self.get_secondary_value(active_hero)
        
        unit = "m" if is_6e else "\""
        string = f"{round_half_up(primary)}{unit}"
        if primary != secondary:
            string = f"{string}/{round_half_up(secondary)}{unit}"
        
        return string
    
    @property
    def damage_display(self) -> str:
        """Get damage display (movement rate)."""
        # 6E throughout: the template chain is Main6E and the corpus is 6E,
        # so this "would need template access" stub had exactly one answer and
        # was giving the other. It printed inches on every movement
        # characteristic in the corpus.
        is_6e = True
        
        unit = "m" if is_6e else "\""
        string = ""
        if self.affect_total and self._levels > 0:
            string = "+"
        string = f"{string}{self._levels}{unit}"
        return string
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output."""
        # The modifiers, which were stubbed out here with the call commented
        # beside them. Both places matter: a movement characteristic bought at
        # zero levels purely to CARRY a limitation prints as
        # "Increased Endurance Cost (x4 END; -1 1/2) applied to Running", and
        # that whole branch is unreachable while the string is empty.
        modifier_str = self.modifier_string
        
        if (self._levels == 0 and
            self.add_modifiers_to_base and
            modifier_str.strip()):
            string = modifier_str
            if string.strip().startswith(","):
                string = string.strip()[1:].strip()
            string = f"{string} applied to {self.alias or ''}"
            if self._name and self._name.strip():
                string = f"<i>{self._name}:</i>  {string}"
            return string
        
        # Java is `getAlias() + " " + getDamageDisplay()`. Preferring the
        # DISPLAY silently overrode a character who renamed the movement: one
        # NAGA calls its Running "(14m total)", and HD prints that, because
        # what the player typed is what the sheet says.
        alias = self.alias or ""
        string = f"{alias} {self.damage_display}"
        if self._name and self._name.strip():
            string = f"<i>{self._name}:</i>  {string}"
        
        if self.input and self.input.strip():
            string = f"{string}:  {self.input}"
        
        if self.affect_total:
            string = f"{string} ({self.total_display()} total)"
        
        if self._selected_option:
            option_alias = self._selected_option.display if self._selected_option.display else self._selected_option.xmlid
            string = f"{string} ({option_alias}"
            adder_str = self.adder_string
            if adder_str.strip():
                string = f"{string}; {adder_str}"
            string = f"{string})"
        else:
            adder_str = self.adder_string
            if adder_str.strip():
                string = f"{string} ({adder_str})"
        
        if modifier_str.strip():
            string = f"{string}{modifier_str}"
        
        return string

def _active_hero():
    """The character these totals are relative to.

    HD reads getPrimaryValue() off the character being displayed. With no hero
    the value is 0, so every total printed "0m" — a movement total is the
    CHARACTER's, and there is no such thing without one. Fails closed.
    """
    try:
        from kirby_cost.core.context import EngineContext
        return EngineContext.active_hero()
    except Exception:  # noqa: BLE001
        return None
