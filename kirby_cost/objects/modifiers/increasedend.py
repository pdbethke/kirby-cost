"""
IncreasedEND modifier for kirby-cost.

Converted from com.hero.objects.modifiers.IncreasedEND.java

IncreasedEND modifier with custom getColumn2Output(), getTotalValue(), and included() methods.
Halves value for Costs END Only To Activate. Cannot be applied with Reduced END.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class IncreasedEND(Modifier, xmlid="INCREASEDEND"):
    """
    IncreasedEND modifier.
    
    Increases END cost.
    
    Has custom value calculation that halves for Costs END Only To Activate.
    Cannot be applied with Reduced END or to abilities that don't cost END.
    """
    
    def __init__(self, element=None):
        """Initialize a IncreasedEND modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for IncreasedEND modifier.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        d = self.total_value
        
        # Add input
        if self.input and self.input.strip():
            if string2.strip():
                string2 = string2 + " "
            string2 = string2 + self.input
        
        string2 = string2.strip()
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + ", " + modifier.alias
        
        # Add selected option
        if self._selected_option is not None:
            string2 = string2 + " (" + self._selected_option.alias
        
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
    
    @property
    def total_value(self) -> float:
        """
        Get total value of this modifier.
        
        Halves value if parent has Costs END Only To Activate or Costs END with ACTIVATE option.
        """
        d = super().total_value
        
        if self.progenitor is not None:
            progenitor = self.progenitor
            
            # Check for Costs END Only To Activate
            if GenericObject.find_object_by_id(
                progenitor.assigned_modifiers, "COSTSENDONLYTOACTIVATE") is not None:
                d /= 2.0
            # Check for Costs END with ACTIVATE option
            elif GenericObject.find_object_by_id(
                progenitor.assigned_modifiers, "COSTSEND") is not None:
                costs_end = GenericObject.find_object_by_id(
                    progenitor.assigned_modifiers, "COSTSEND")
                if (costs_end and costs_end.selected_option and 
                    costs_end.selected_option.xmlid == "ACTIVATE"):
                    d /= 2.0
        
        return d
    
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
        
        # Cannot be applied with Reduced END
        if GenericObject.find_object_by_id(
            generic_object.assigned_modifiers, "REDUCEDEND") is not None:
            return f"{self.display} cannot be assigned to an ability with Reduced Endurance."
        
        # Can be applied to Lists
        from kirby_cost.objects.list import List
        if isinstance(generic_object, List):
            return ""
        
        # Cannot be applied if power doesn't cost END
        if generic_object.end_usage == 0:
            return f"{self.display} cannot be applied to an ability which does not cost END."
        
        return ""
