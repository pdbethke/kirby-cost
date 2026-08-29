"""
Swimming characteristic class.

Converted from com.hero.objects.characteristics.Swimming.java
"""

from typing import Optional, TYPE_CHECKING

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType
from kirby_cost.util.rounder import round_half_up

if TYPE_CHECKING:
    from kirby_cost.io.hdc_loader import LoadedHero as Hero  # the live hero type


class Swimming(Characteristic, xmlid="SWIMMING"):
    """Swimming movement characteristic."""
    
    def __init__(self):
        """Initialize Swimming."""
        super().__init__(self.XMLID)
        self._display = "Swimming"
        # 6E1 p43: Swimming, 4m base, 1 Character Point per +2m.
        # _level_value was 1.0, charging 1 CP per metre -- double the 6E rate.
        # Masked by the loaded template, same as Running above.
        self._level_cost = 1.0
        self._level_value = 2.0
        self._minimum_cost = 1.0
        self._base_cost = 0.0
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.SWIMMING)
    
    def roll(self, active_hero: Optional['Hero'] = None) -> str:
        """Swimming doesn't have a roll."""
        return ""
    
    @property
    def damage_display(self) -> str:
        """Get damage display (movement rate)."""
        # 6E throughout: the template chain is Main6E and the corpus is 6E,
        # so this "would need template access" stub had exactly one answer and
        # was giving the other. It printed inches on every movement
        # characteristic in the corpus.
        is_6e = True
        
        hero = _active_hero()
        primary = self.get_primary_value(hero)
        secondary = self.get_secondary_value(hero)
        
        unit = "m" if is_6e else "\""
        string = f"{round_half_up(primary)}{unit}"
        if primary != secondary:
            string = f"{string}/{round_half_up(secondary)}{unit}"
        
        prefix = "+" if (self._levels > 0 and self.affect_total) else ""
        levels_str = f"{prefix}{self._levels}{unit}"
        
        if self.affect_total:
            string = f"{levels_str} ({string} total)"
        else:
            string = levels_str
        
        return string
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output."""
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
        
        # Extract total from damage display if present
        string2 = ""
        # Java's guard is indexOf("(") > 0, not >= 0 (Swimming.java:99). A
        # paren at position ZERO means the whole alias is parenthesised --
        # one NAGA renames its Swimming "(8m total)" -- and Java leaves that
        # alone. Treating it as found moved the string onto a leading space:
        # "<i>Amphibious Form:</i>   (8m total)", with three.
        idx = string.find("(")
        if idx > 0:
            string2 = " " + string[idx:]
            string = string[:idx].strip()
        string = f"{string}{string2}"
        
        if self._name and self._name.strip():
            string = f"<i>{self._name}:</i>  {string}"
        
        if self.input and self.input.strip():
            string = f"{string}:  {self.input}"
        
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
