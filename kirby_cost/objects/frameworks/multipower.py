"""
Multipower framework class for kirby-cost.

Converted from com.hero.objects.Multipower.java

Multipower allows multiple powers to share a common reserve.
Slots can be Ultra (1/10 cost) or Variable (1/5 cost).
"""

from typing import Optional
from kirby_cost.objects.list import List
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.rounder import round_half_down


class Multipower(List):
    """
    Multipower framework.
    
    Reserve Cost = Base Cost (typically 5 points per 1 point of reserve)
    
    Slot Costs:
    - Ultra: Active Cost / 10 (minimum 1 point)
    - Variable: Active Cost / 5 (minimum 1 point)
    """
    
    def __init__(self, name: Optional[str] = None):
        """Initialize a Multipower."""
        super().__init__()
        self.xmlid = "MULTIPOWER"
        self.abbreviation = "MP"
        self._minimum_cost = 1.0
        self._max_cost = 9999.0
        self.min_set = True
        self.max_set = True
        if name:
            self._display = name
            self._alias = name
        else:
            self._base_cost = 5.0  # Default 5-point reserve
    
    def real_cost_for_child(self, child: GenericObject) -> float:
        """
        Calculate real cost for a slot in this Multipower.
        
        Formula:
        - Ultra: (Active Cost / 10), minimum 1
        - Variable: (Active Cost / 5), minimum 1
        """
        # Get base real cost (includes framework adders)
        real_cost = super().real_cost_for_child(child)
        
        # Check if slot had any cost
        had_cost = real_cost > 0.0
        
        # Apply framework cost reduction
        if child.ultra:
            # Ultra slot: divide by 10
            real_cost = real_cost / 10.0
        else:
            # Variable slot: divide by 5
            real_cost = real_cost / 5.0
        
        # Round down
        real_cost = round_half_down(real_cost)
        
        # Minimum 1 point if it had cost
        if had_cost and real_cost < 1.0:
            real_cost = 1.0
        
        return real_cost
    
    def object_allowed(self, obj: GenericObject, show_warnings: bool = True) -> bool:
        """
        Check if an object can be added to this Multipower.
        
        Validation:
        - Active Cost cannot exceed Reserve Base Cost
        - Cannot add Lists
        - Cannot add VPPs
        - Modifier compatibility
        """
        # Clone object for testing
        test_obj = obj  # Would clone in real implementation
        
        # Check base List validation
        if not super().object_allowed(obj, show_warnings):
            return False
        
        # Check Active Cost vs Reserve
        active_cost = obj.active_cost
        reserve_cost = self.base_cost
        
        if active_cost > reserve_cost:
            self.error = f"The Active Cost of {obj.alias} exceeds the Base Cost of the Multipower.  {obj.alias} will be placed outside of this Multipower."
            return False
        
        # Check for Linked powers across framework slots (stub)
        # This would check if obj has LINKED modifier pointing to another framework slot
        
        # Check for SPECIAL type (stub - would check rules)
        # if obj.get_types() and "SPECIAL" in obj.get_types():
        #     # Warning or error based on rules
        
        return True
    
    def column1_suffix(self, obj: GenericObject) -> str:
        """Get suffix for column 1 (u/v for ultra/variable, or f/v for 6E)."""
        self._update_child_positions()
        # Stub - would check if 6E
        is_6e = False  # Would check from rules/template
        
        if is_6e:
            return "f" if obj.ultra else "v"
        else:
            return "u" if obj.ultra else "m"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = ""
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  "
        output += f"{self._alias}, {int(self.base_cost)}-point reserve"
        
        adder_str = self.adder_string  # Stub method
        if adder_str and adder_str.strip():
            output += f", {adder_str}"
        
        modifier_str = self.modifier_string  # Stub method
        output += modifier_str
        
        return output
    
    @property
    def adder_string(self) -> str:
        """Get adder string for display (stub)."""
        # Would build string from assigned adders
        return ""
    

