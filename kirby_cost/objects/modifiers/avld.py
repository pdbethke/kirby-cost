"""
AVLD modifier for kirby-cost.

Converted from com.hero.objects.modifiers.AVLD.java

AVLD modifier with custom getBaseCost(), getAvailableAdders(), getColumn2Output(),
and included() methods. Handles standard vs non-standard defense costs.
"""

from typing import List
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.adder import Adder


class AVLD(Modifier, xmlid="AVLD"):
    """
    AVLD modifier.
    
    Attack Versus Limited Defense.
    
    Has custom cost calculation for standard vs non-standard defenses,
    and custom adder handling for common defense option.
    """
    
    def __init__(self, element=None):
        """Initialize a AVLD modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        self.non_standard_cost = 0.75
        self.available_check = False
        
        # Create common defense adder
        self.common_defense = Adder()
        self.common_defense.set_fixed_value(True)
        self.common_defense.xmlid = "COMMONDEFENSE"
        self.common_defense.set_selectable(True)
        self.common_defense.display_in_string = False
        self.common_defense.set_display("Defense is Extraordinarily Common")
        self.common_defense.base_cost = 0.0
        self.common_defense.set_exclusive(True)
        
        if element is not None:
            self._init(element)
    
    def _init(self, element) -> None:
        """
        Initialize from XML element.
        
        Args:
            element: XML element to parse
        """
        super()._init(element)
        self.available_check = False
        
        # Parse NONSTANDARDDEFENSE attribute
        from kirby_cost.io.xml_utility import XMLUtility
        non_standard_str = XMLUtility.get_value(element, "NONSTANDARDDEFENSE")
        if non_standard_str and non_standard_str.strip():
            try:
                self.non_standard_cost = float(non_standard_str)
            except (ValueError, TypeError):
                self.non_standard_cost = 0.75
    
    def _is_standard_defense(self) -> bool:
        """
        Check if parent has standard defense.
        
        Returns:
            True if standard defense, False otherwise
        """
        parent = self.parent
        if parent is None:
            return True
        
        from kirby_cost.objects.powers.naked_modifier import NakedModifier
        if isinstance(parent, NakedModifier):
            return True
        
        defense = parent.get_defense("AVLD")
        return defense == "NORMAL"
    
    @property
    def base_cost(self) -> float:
        """
        Get base cost based on defense type.

    @base_cost.setter
    def base_cost(self, value) -> None:
        self._base_cost = value
        
        Returns:
            Base cost (baseCost for standard, nonStandardCost for non-standard)
        """
        if (self._is_standard_defense() and 
            GenericObject.find_object_by_id(self.assigned_adders, "COMMONDEFENSE") is None):
            return self._base_cost
        
        return self.non_standard_cost
    
    @property
    def available_adders(self) -> List[Adder]:
        """
        Get available adders, including common defense option if applicable.
        
        Returns:
            List of available adders
        """
        adders = list(super().available_adders)
        
        if (self._is_standard_defense() and 
            GenericObject.find_object_by_id(self.assigned_adders, "COMMONDEFENSE") is None):
            adders.append(self.common_defense)
        elif self._is_standard_defense():
            common_def = GenericObject.find_object_by_id(self.assigned_adders, "COMMONDEFENSE")
            if common_def:
                adders.append(common_def)
        
        return adders
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for AVLD modifier.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        d = self.total_value
        
        # Handle adders
        for adder in self.assigned_adders:
            if adder.display_in_string:
                if string:
                    string = string + ", "
                string = string + adder.alias + " (" + self.fraction(adder.base_cost) + ")"
            d -= adder.base_cost
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + ", " + modifier.alias
        
        string2 = string2 + " ("
        
        # Add input
        if self.input and self.input.strip():
            string2 = string2 + self.input + "; "
        
        # Add comments
        if self.comments.strip():
            string2 = string2 + self.comments + "; "
        
        string2 = string2 + self.fraction(d) + ")"
        
        # Append adders string
        if string.strip():
            if string2.strip():
                string2 = string2 + ", "
            string2 = string2 + string
        
        return string2
    
    @property
    def max_cost(self) -> float:
        """Get maximum cost (same as base cost)."""
        return self.base_cost

    @max_cost.setter
    def max_cost(self, value) -> None:
        self._max_cost = value
    
    @property
    def minimum_cost(self) -> float:
        """Get minimum cost (same as base cost)."""
        return self.base_cost

    @minimum_cost.setter
    def minimum_cost(self, value) -> None:
        self._minimum_cost = value
    
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
        
        from kirby_cost.objects.powers.naked_modifier import NakedModifier
        if isinstance(generic_object, NakedModifier):
            return ""
        
        # Can only be applied to abilities which affect others
        target = generic_object.target
        if target == "SELFONLY" or target == "N/A":
            return f"{self._display} can only be applied to abilities which affect others."
        
        # Can only be applied to abilities which act against standard Defense types
        defense = generic_object.defense
        if defense == "NONE":
            return (f"{self._display} can only be applied to abilities which act against "
                   f"one of the standard Defense types (Normal, Power, Flash, Mental).")
        
        return ""
