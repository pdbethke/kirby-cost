"""
ExtraTime modifier for kirby-cost.

Converted from com.hero.objects.modifiers.ExtraTime.java

ExtraTime modifier with custom getColumn2Output(), getAssignedAdders(),
getAvailableAdders(), and included() methods. Filters NOOTHERACTIONS adder for attacks.
"""

from typing import List
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.adder import Adder


class ExtraTime(Modifier, xmlid="EXTRATIME"):
    """
    ExtraTime modifier.
    
    Takes extra time to activate.
    
    Has custom formatting and adder filtering for attack powers.
    Filters NOOTHERACTIONS adder for attack powers.
    """
    
    def __init__(self, element=None):
        """Initialize a ExtraTime modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def assigned_adders(self) -> List[Adder]:
        """
        Get assigned adders, filtering NOOTHERACTIONS for attack powers.
        
        Returns:
            List of assigned adders
        """
        adders = super().assigned_adders
        
        parent = self.parent
        if parent is None:
            return adders
        
        types = parent.types
        if not types or "ATTACK" not in types:
            return adders
        
        # Remove NOOTHERACTIONS adder for attack powers
        no_other_actions = GenericObject.find_object_by_id(adders, "NOOTHERACTIONS")
        if no_other_actions:
            adders.remove(no_other_actions)
        
        return adders

    @assigned_adders.setter
    def assigned_adders(self, value):
        # Java GenericObject.setAssignedAdders (GenericObject.java:3916) is
        # never overridden; getter-only Python overrides must re-expose it.
        self._assigned_adders = value

    
    @property
    def available_adders(self) -> List[Adder]:
        """
        Get available adders, filtering NOOTHERACTIONS for attack powers.
        
        Returns:
            List of available adders
        """
        adders = list(super().available_adders)
        
        parent = self.parent
        if parent is None:
            return adders
        
        types = parent.types
        if not types or "ATTACK" not in types:
            return adders
        
        # Remove NOOTHERACTIONS adder for attack powers
        no_other_actions = GenericObject.find_object_by_id(adders, "NOOTHERACTIONS")
        if no_other_actions:
            adders.remove(no_other_actions)
        
        return adders
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for ExtraTime modifier.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        d = self.total_value
        
        # Add selected option in parentheses
        if self._selected_option is not None:
            string2 = string2 + " (" + self._selected_option.alias
        
        # Add input
        if self.input and self.input.strip():
            if string2.strip():
                string2 = string2 + " "
            string2 = string2 + self.input
        
        string2 = string2.strip()
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + ", " + modifier.alias
        
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
        
        string2 = string2 + " (" if n2 <= 0 else string2 + ", "
        
        # Add adders
        for adder in self.assigned_adders:
            if not adder.is_selected or not adder.column2_output.strip():
                continue
            string2 = string2 + adder.column2_output.strip() + ", "
        
        # Add comments
        if self.comments.strip():
            string2 = string2 + self.comments + "; "
        
        # Apply min/max limits
        if d > self._max_cost and self.max_set:
            d = self._max_cost
        if d < self._minimum_cost and self.min_set:
            d = self._minimum_cost
        
        string2 = string2 + self.fraction(d) + ")"
        n2 -= 1
        
        # Close remaining parentheses
        while n2 > 0:
            string2 = string2 + ")"
            n2 -= 1
        
        # Append other adders string
        if string.strip():
            if string2.strip():
                string2 = string2 + ", "
            string2 = string2 + string
        
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
        
        # Cannot be applied to Regeneration
        from kirby_cost.objects.powers.regeneration import Regeneration
        if isinstance(generic_object, Regeneration):
            return f"{self._display} cannot be applied to Regeneration."
        
        return ""
