"""
Extra Damage Classes for Martial Arts.

Converted from com.hero.objects.martialarts.ExtraDamageClasses.java

Extra Damage Classes add HTH damage classes to martial arts maneuvers.
"""

from kirby_cost.objects.base import GenericObject
from kirby_cost.core.context import EngineContext


class ExtraDamageClasses(GenericObject, xmlid="EXTRADC"):
    """
    Extra Damage Classes.
    
    Adds HTH damage classes to martial arts maneuvers.
    """
    
    def __init__(self, element=None, bl: bool = False):
        """
        Initialize Extra Damage Classes.
        
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
        self._display = "+[LVL] HTH Damage Class(es)"
        self._alias = ""
        self._base_cost = 0.0
        self._level_cost = 4.0
        self._level_value = 1.0
        self._minimum_cost = 4.0
        self._minimum_level = 1
        
        super()._init(element)
    
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
        
        # Add modifiers
        mod_str = self.modifier_string
        if mod_str.strip():
            output = output + " " + mod_str
        
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
    
    def get_save_xml(self):
        """
        Get XML element for saving.
        
        Returns:
            XML element with EXTRADC tag
        """
        element = super().get_save_xml()
        element.tag = "EXTRADC"
        return element
    
    def restore_from_save(self, element) -> None:
        """
        Restore from saved XML element.
        
        Args:
            element: XML element containing saved data
        """
        super().restore_from_save(element)


