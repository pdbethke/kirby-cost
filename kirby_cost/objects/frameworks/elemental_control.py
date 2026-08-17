"""
Elemental Control framework class for kirby-cost.

Converted from com.hero.objects.ElementalControl.java

Elemental Control allows multiple powers to share advantages.
In 6E, EC works like a regular List. In 5E, it has special cost calculations.
"""

from typing import Optional
from kirby_cost.objects.list import List
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.rounder import round_half_down


class ElementalControl(List):
    """
    Elemental Control framework.
    
    In 6E: Works like a regular List (no special cost reduction)
    In 5E: Powers share advantages, cost = max(EC Active Cost, Power Active Cost - EC Active Cost)
    """
    
    def __init__(self, name: Optional[str] = None):
        """Initialize an Elemental Control."""
        super().__init__()
        self.xmlid = "ELEMENTALCONTROL"
        self.abbreviation = "EC"
        self._minimum_cost = 1.0
        self._max_cost = 9999.0
        self.min_set = True
        self.max_set = True
        if name:
            self._display = name
            self._alias = name
        else:
            self._base_cost = 5.0  # Default 5-point EC
    
    def real_cost_for_child(self, child: GenericObject) -> float:
        """
        Calculate real cost for a power in this Elemental Control.
        
        In 6E: Uses standard List calculation (no special reduction)
        In 5E: Special calculation where powers share advantages
        """
        # Stub: Would check if 6E
        is_6e = True  # Default to 6E for now
        
        if is_6e:
            # 6E: Standard List calculation
            return super().real_cost_for_child(child)
        else:
            # 5E: Special EC calculation
            # This is complex - would need full 5E implementation
            # For now, return standard calculation
            return super().real_cost_for_child(child)
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        # Stub: Would check if 6E
        is_6e = True
        
        if is_6e:
            return super().column2_output
        else:
            # 5E format: "EC Name, X-point powers"
            output = ""
            if self._name and self._name.strip():
                output = f"<i>{self._name}:</i>  "
            active_cost = self.active_cost
            output += f"{self._alias}, {int(active_cost) * 2}-point powers"
            
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                output += f", {adder_str}"
            
            modifier_str = self.modifier_string
            output += modifier_str
            
            return output
    
    @property
    def adder_string(self) -> str:
        """Get adder string for display (stub)."""
        return ""
    
    @property
    def modifier_string(self) -> str:
        """Get modifier string for display (stub)."""
        return ""

