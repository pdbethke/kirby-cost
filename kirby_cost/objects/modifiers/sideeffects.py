"""
SideEffects modifier for kirby-cost.

Converted from com.hero.objects.modifiers.SideEffects.java

SideEffects modifier with custom getColumn2Output() and getBaseCost() methods.
Uses base class included() method for validation (no custom validation needed).
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject
from kirby_cost.io.xml_utility import XMLUtility


class SideEffects(Modifier, xmlid="SIDEEFFECTS"):
    """
    SideEffects modifier.
    
    Power has side effects.
    
    Custom implementation includes:
    - Custom getColumn2Output() for formatted display
    - Custom getBaseCost() with constant power activation adjustment
    """
    
    def __init__(self, element=None):
        """Initialize a SideEffects modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        self.constant_power_with_activation = -0.25
        if element is not None:
            self._init(element)
            # Parse CONSTANTPOWERWITHACTIVATION
            val = XMLUtility.get_value(element, "CONSTANTPOWERWITHACTIVATION")
            if val:
                try:
                    self.constant_power_with_activation = float(val)
                except (ValueError, TypeError):
                    pass
    
    @property
    def base_cost(self) -> float:
        """
        Get base cost.
        
        Adds constant power with activation adjustment.
        """
        d = self._base_cost
        parent = self.parent
        
        if parent is None:
            return d
        
        duration = parent.duration
        if duration in ("CONSTANT", "PERSISTENT", "INHERENT"):
            # Check for Activation Roll or Requires Skill Roll
            if (GenericObject.find_object_by_id(
                parent.assigned_modifiers, "ACTIVATIONROLL") is not None or
                GenericObject.find_object_by_id(
                parent.assigned_modifiers, "REQUIRESSKILLROLL") is not None):
                d += self.constant_power_with_activation
        
        return d

    @base_cost.setter
    def base_cost(self, value: float) -> None:
        self._base_cost = value

    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for SideEffects modifier.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        d = self.total_value
        
        # Handle adders
        for adder in self.assigned_adders:
            if string:
                string = string + ", "
            string = string + adder.alias
        
        # Add input
        if self.input and self.input.strip():
            if string2.strip():
                string2 = string2 + ":  "
            string2 = string2 + self.input
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + ", " + modifier.alias
        
        string2 = string2 + " ("
        
        # Add adders string
        if string.strip():
            string2 = string2 + string + "; "
        
        # Add comments
        if self.comments.strip():
            string2 = string2 + self.comments + "; "
        
        string2 = string2 + self.get_fraction(d) + ")"
        
        return string2
    
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
        # SideEffects modifier doesn't override included() in Java source
        return ""
