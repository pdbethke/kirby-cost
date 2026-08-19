"""
Incantations modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Incantations.java

Incantations modifier with custom getColumn2Output(), getAssignedModifiers(), 
and getAvailableModifiers() methods for modifier intelligence logic.
Filters CONSTANT modifier for instant powers. Uses base class included() method for validation.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Incantations(Modifier, xmlid="INCANTATIONS"):
    """
    Incantations modifier.
    
    Requires incantations to activate.
    
    Has custom modifier filtering logic for modifier intelligence feature.
    Uses base class included() method for validation.
    """
    
    def __init__(self, element=None):
        """Initialize a Incantations modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    def included(self, generic_object: GenericObject) -> str:
        """
        Check if this modifier can be applied to the given object.
        
        Args:
            generic_object: The object to check
            
        Returns:
            Empty string if allowed, error message if not
        """
        result = super().included(generic_object)
        if result and result.strip():
            return result
        
        if self.force_allow:
            return result
        
        # No additional validation needed - uses base class validation
        # Incantations modifier doesn't override included() in Java source
        return ""
    
    def _should_filter_constant(self) -> bool:
        """
        Check if CONSTANT modifier should be filtered.
        
        Returns:
            True if should filter, False otherwise
        """
        # TODO: Would need HeroDesigner.getInstance().getPrefs().isModifierIntelligenceOn()
        # For now, assume modifier intelligence is on
        modifier_intelligence_on = True
        
        if not modifier_intelligence_on:
            return False
        
        progenitor = self.progenitor
        if progenitor is None:
            return False
        
        # Check if progenitor is a List
        from kirby_cost.objects.list import List
        if isinstance(progenitor, List):
            objects = progenitor.objects
            if not objects or len(objects) == 0:
                return False
            
            for obj in objects:
                if (obj.duration == "INSTANT" and
                    GenericObject.find_object_by_id(obj.assigned_modifiers, "EXTRATIME") is None and
                    GenericObject.find_object_by_id(obj.assigned_modifiers, "REGENEXTRATIME") is None and
                    obj.xmlid not in ("MINDCONTROL", "MINDSCAN", "MINDLINK", "TELEPATHY", "FORCEWALL")):
                    return True
            return False
        
        # Check single power
        from kirby_cost.objects.powers.power import Power
        if not isinstance(progenitor, Power):
            return False
        
        # TODO: Would need HeroDesigner.getActiveHero() access
        # For now, assume hero is available and not loading
        # active_hero = HeroDesigner.getActiveHero()
        # if active_hero is None or active_hero.isLoading():
        #     return False
        
        duration = progenitor.duration
        if duration != "INSTANT":
            return False
        
        if GenericObject.find_object_by_id(progenitor.assigned_modifiers, "EXTRATIME") is not None:
            return False
        
        if GenericObject.find_object_by_id(progenitor.assigned_modifiers, "REGENEXTRATIME") is not None:
            return False
        
        xmlid = progenitor.xmlid
        if xmlid in ("MINDCONTROL", "MINDSCAN", "MINDLINK", "TELEPATHY", "FORCEWALL"):
            return False
        
        return True
    
    @property
    def assigned_modifiers(self):
        """
        Get assigned modifiers, filtering CONSTANT if needed.
        
        Returns:
            List of assigned modifiers
        """
        modifiers = super().assigned_modifiers
        
        if not self._should_filter_constant():
            return modifiers
        
        # Remove CONSTANT modifier
        constant = GenericObject.find_object_by_id(modifiers, "CONSTANT")
        if constant:
            modifiers.remove(constant)
        
        return modifiers
    
    @property
    def available_modifiers(self):
        """
        Get available modifiers, filtering CONSTANT if needed.
        
        Returns:
            List of available modifiers
        """
        modifiers = list(super().available_modifiers)
        
        if not self._should_filter_constant():
            return modifiers
        
        # Remove CONSTANT modifier
        constant = GenericObject.find_object_by_id(modifiers, "CONSTANT")
        if constant:
            modifiers.remove(constant)
        
        return modifiers
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for Incantations modifier.
        """
        string = ""
        string2 = ""
        
        if not self.show_option_only:
            string2 = string2 + self._alias
        
        d = self.total_value
        
        # Add input
        if self.input and self.input.strip():
            if string2.strip():
                string2 = string2 + " "
            string2 = string2 + self.input
        
        string2 = string2.strip()
        
        # Count parentheses
        n = 0
        n2 = 0
        while string2.find("(", n) >= 0:
            n2 += 1
            n = string2.find("(", n) + 1
        
        n = 0
        while string2.find(")", n) >= 0:
            n2 -= 1
            n = string2.find(")", n) + 1
        
        string2 = string2 + " (" if n2 <= 0 else string2 + "; "
        
        # Add selected option
        if (self._selected_option is not None and 
            self._selected_option.display_in_string and
            self._selected_option.alias.strip()):
            string2 = string2 + self._selected_option.alias + "; "
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + modifier.alias + "; "
        
        # Add adders
        for adder in self.assigned_adders:
            if not adder.is_selected or not adder.column2_output.strip():
                continue
            string2 = string2 + adder.column2_output.strip() + "; "
        
        # Add comments
        if self.comments.strip():
            string2 = string2 + self.comments + "; "
        
        # Apply min/max limits
        if d > self._max_cost and self.max_set:
            d = self._max_cost
        if d < self._minimum_cost and self.min_set:
            d = self._minimum_cost
        
        string2 = string2 + self.get_fraction(d) + ")"
        n2 -= 1
        
        # Close remaining parentheses
        while n2 > 0:
            string2 = string2 + ")"
            n2 -= 1
        
        if string.strip():
            if string2.strip():
                string2 = string2 + ", "
            string2 = string2 + string
        
        return string2
