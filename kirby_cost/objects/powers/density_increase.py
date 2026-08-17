"""
Density Increase power class for kirby-cost.

Converted from com.hero.objects.powers.DensityIncrease.java

Power to increase character density.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_half_up
import math


class DensityIncrease(Power, xmlid="DENSITYINCREASE"):
    """
    Density Increase power.
    
    Increases character density, affecting mass, STR, PD/ED, and KB.
    """
    
    def __init__(self):
        """Initialize a Density Increase power."""
        super().__init__()
        self.xmlid = DensityIncrease.XMLID
        self._duration = "CONSTANT"
        # Stub: would initialize mass multiplier and characteristic increases
    
    @property
    def damage_display(self) -> str:
        """Get density increase display string."""
        # Stub: would calculate mass, STR, PD/ED, KB from levels
        # For now, return simplified version
        return f"{self._levels} levels"
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = f"{self._alias} ({self.damage_display})"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        if self.input and self.input.strip():
            output += f":  {self.input}"
        
        adder_str = self.adder_string
        if adder_str and adder_str.strip():
            output += f", {adder_str}"
        
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    
    @property
    def levels(self) -> int:
        """Get levels (capped at 50)."""
        levels = self._levels
        return min(levels, 50)

    @levels.setter
    def levels(self, value) -> None:
        self._levels = value
    
    @property
    def str_increase(self) -> float:
        """Get STR increase (checks for NOSTRINCREASE modifier)."""
        # Stub: would check for NOSTRINCREASE modifier
        return self._str_increase

    @str_increase.setter
    def str_increase(self, value: float) -> None:
        self._str_increase = value

    @property
    def pd_increase(self) -> float:
        """Get PD increase (checks for NODEFINCREASE modifier)."""
        # Stub: would check for NODEFINCREASE modifier
        return self._pd_increase

    @pd_increase.setter
    def pd_increase(self, value: float) -> None:
        self._pd_increase = value

    @property
    def ed_increase(self) -> float:
        """Get ED increase (checks for NODEFINCREASE modifier)."""
        # Stub: would check for NODEFINCREASE modifier
        return self._ed_increase

    @ed_increase.setter
    def ed_increase(self, value: float) -> None:
        self._ed_increase = value
    
    @property
    def adder_string(self) -> str:
        """Get adder string (stub)."""
        return ""
    
    @property
    def modifier_string(self) -> str:
        """Get modifier string (stub)."""
        return ""

