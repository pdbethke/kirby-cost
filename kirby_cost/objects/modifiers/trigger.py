"""
Trigger modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Trigger.java

Trigger modifier with custom getAssignedAdders() method.
Filters MULTIPLE adder based on parent having FOCUS or CHARGES.
"""

from typing import List
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Trigger(Modifier, xmlid="TRIGGER"):
    """
    Trigger modifier.
    
    Power is triggered.
    
    Has custom adder filtering logic for MULTIPLE adder based on parent modifiers.
    """
    
    def __init__(self, element=None):
        """Initialize a Trigger modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def assigned_adders(self) -> list:
        """
        Get assigned adders.
        
        Removes MULTIPLE adder if parent doesn't have FOCUS or CHARGES.
        """
        adders = super().assigned_adders
        
        if self.parent is None:
            return adders
        
        # If parent has FOCUS or CHARGES, allow MULTIPLE
        if (GenericObject.find_object_by_id(
            self.parent.assigned_modifiers, "FOCUS") is not None or
            GenericObject.find_object_by_id(
            self.parent.assigned_modifiers, "CHARGES") is not None):
            return adders
        
        # Remove MULTIPLE if present
        multiple = GenericObject.find_object_by_id(adders, "MULTIPLE")
        if multiple is not None:
            adders = [a for a in adders if a != multiple]
        
        return adders

    @assigned_adders.setter
    def assigned_adders(self, value):
        # Java GenericObject.setAssignedAdders (GenericObject.java:3916) is
        # never overridden; getter-only Python overrides must re-expose it.
        self._assigned_adders = value

    
    @property
    def available_adders(self) -> list:
        """
        Get available adders.
        
        Removes MULTIPLE adder if parent doesn't have FOCUS or CHARGES.
        """
        adders = list(super().available_adders)
        
        if self.parent is None:
            return adders
        
        # If parent has FOCUS or CHARGES, allow MULTIPLE
        if (GenericObject.find_object_by_id(
            self.parent.assigned_modifiers, "FOCUS") is not None or
            GenericObject.find_object_by_id(
            self.parent.assigned_modifiers, "CHARGES") is not None):
            return adders
        
        # Remove MULTIPLE if present
        multiple = GenericObject.find_object_by_id(adders, "MULTIPLE")
        if multiple is not None:
            adders = [a for a in adders if a != multiple]
        
        return adders
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for Trigger modifier.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        d = self.total_value
        
        # Handle adders
        for adder in self.assigned_adders:
            if string:
                string = string + ", "
            if adder.selected_option is not None:
                string = string + str(adder.selected_option)
            else:
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
