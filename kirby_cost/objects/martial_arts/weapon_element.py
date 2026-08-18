"""
Weapon Element for Martial Arts.

Converted from com.hero.objects.martialarts.WeaponElement.java

Weapon Element allows using weapons with martial arts maneuvers.
"""

from kirby_cost.objects.base import GenericObject
from kirby_cost.core.context import EngineContext


class WeaponElement(GenericObject, xmlid="WEAPON_ELEMENT"):
    """
    Weapon Element.
    
    Allows using weapons with martial arts maneuvers.
    """
    
    def __init__(self, element=None, bl: bool = False):
        """
        Initialize Weapon Element.
        
        Args:
            element: Optional XML element for initialization
            bl: Optional boolean flag (unused in Java)
        """
        if bl:
            super().__init__()
        else:
            super().__init__()
            self.xmlid = self.XMLID
        
        if element is not None:
            self._init(element)
    
    def allows_other_modifiers(self) -> bool:
        """
        Check if other modifiers are allowed.
        
        Returns:
            False (no other modifiers allowed)
        """
        return False
    
    def allows_other_adders(self) -> bool:
        """
        Check if other adders are allowed.
        
        Returns:
            False (no other adders allowed)
        """
        return False
    
    def _init(self, element) -> None:
        """
        Initialize from XML element.
        
        Args:
            element: XML element for initialization
        """
        self._display = "Weapon Element"
        self._alias = "Weapon Element"
        self._base_cost = 0.0
        self._level_cost = 0.0
        self._level_value = 0.0
        self._minimum_cost = 1.0
        self._minimum_level = 0
        
        super()._init(element)
        
        # Ensure alias is set
        self._alias = "Weapon Element"
        # Folded in from restore_from_save, which ran after _init.
        # One ingest per class; see engine/xml_attrs.py.
    
    @property
    def column2_output(self) -> str:
        """
        Get formatted output for column 2 display.
        
        Returns:
            Formatted string representation
        """
        output = self._alias
        
        # Add input
        if self.input and self.input.strip():
            output = output + ":  " + self.input
        
        # Add adders
        adder_str = self.adder_string
        if adder_str.strip():
            output = output + ":  " + adder_str
        
        # Add modifiers (note: Java code calls this twice, keeping both)
        mod_str = self.modifier_string
        if mod_str.strip():
            output = output + " " + mod_str
        
        # Add modifiers again (as per Java code)
        output = output + self.modifier_string
        
        # Add END usage note
        if self.end_usage > 0:
            active_hero = EngineContext.active_hero()
            if active_hero:
                from kirby_cost.objects.base import GenericObject
                end_reserve = GenericObject.find_object_by_id(active_hero.powers, "ENDURANCERESERVE")
                if end_reserve:
                    all_mods = self.all_assigned_modifiers
                    end_reserve_mod = GenericObject.find_object_by_id(all_mods, "ENDRESERVEOREND")
                    prefs = EngineContext.prefs()
                    if not end_reserve_mod and not prefs.use_wg:
                        if self._use_end_reserve:
                            output = output + " (uses END Reserve)"
                        else:
                            output = output + " (uses Personal END)"
        
        return output
    
    @property
    def adder_string(self) -> str:
        """
        Get adder string with special sorting (COMMON first).
        
        Returns:
            Formatted adder string
        """
        adder_aliases = []
        for adder in self._assigned_adders:
            if hasattr(adder, 'add_alias_to_vector'):
                adder.add_alias_to_vector(adder_aliases)
            else:
                # Fallback: just get alias
                alias = adder.alias if hasattr(adder, 'alias') else str(adder)
                if alias:
                    adder_aliases.append(alias)
        
        # Sort: COMMON items first, then alphabetically
        def sort_key(s: str) -> tuple:
            s_upper = s.upper().strip()
            if s_upper.startswith("COMMON"):
                return (0, s)  # COMMON items first
            return (1, s)  # Other items after
        
        adder_aliases.sort(key=sort_key)
        
        # Join with commas
        result = ", ".join([s for s in adder_aliases if s.strip()])
        return result
    
    def get_save_xml(self):
        """
        Get XML element for saving.
        
        Returns:
            XML element with WEAPON_ELEMENT tag
        """
        element = super().get_save_xml()
        element.tag = "WEAPON_ELEMENT"
        return element
    


