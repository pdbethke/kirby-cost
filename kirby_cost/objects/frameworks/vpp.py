"""
Variable Power Pool (VPP) framework class for kirby-cost.

Converted from com.hero.objects.VariablePowerPool.java

VPP allows powers to be changed from phase to phase.
Cost = Pool Cost + Control Cost
"""

from typing import Optional
from kirby_cost.objects.list import List
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.adder import Adder
from kirby_cost.util.rounder import round_half_down


class VariablePowerPool(List):
    """
    Variable Power Pool framework.
    
    6E VPP Cost:
    - Pool Cost = (Pool Size / levelValue) × levelCost
    - Control Cost = Control Cost Adder Total Cost (minimum Pool Cost / 2)
    - Total = Pool Cost + Control Cost + Other Adders
    """
    
    def __init__(self, name: Optional[str] = None):
        """Initialize a Variable Power Pool."""
        super().__init__()
        self.xmlid = "VPP"
        self._name = name or ""
        self._base_cost = 0.0
        self._minimum_cost = 1.0
        self._max_cost = 9999.0
        self._levels = 10  # Default pool size
        self._minimum_level = 1
        self.min_set = True
        self.max_set = False
        
        # 6E: levelValue = 1.0, levelCost = 1.0
        self._level_value = 1.0
        self._level_cost = 1.0
        
        # Add Control Cost adder (required for 6E)
        self._setup_control_cost_adder()
    
    def _setup_control_cost_adder(self) -> None:
        """Set up the Control Cost adder (required for 6E VPP)."""
        # Check if already exists
        control_adder = None
        for adder in self.available_adders:
            if adder.xmlid == "CONTROLCOST":
                control_adder = adder
                break
        
        if control_adder is None:
            # Create Control Cost adder
            control_adder = Adder()
            control_adder.xmlid = "CONTROLCOST"
            control_adder.display = "Control Cost"
            control_adder.base_cost = 0.0
            control_adder.display_in_string = False
            control_adder.exclusive = True
            control_adder.level_cost = 1.0
            control_adder.level_value = 2.0  # Control cost is 1 per 2 points
            control_adder.minimum_level = 0
            control_adder.max_level = 99999
            control_adder._required = True
            control_adder._selected = True
            
            self.assigned_adders.append(control_adder)
            self.available_adders.append(control_adder)
        else:
            control_adder._required = True
    
    @property
    def level_cost(self) -> float:
        """Get level cost (always 1.0 for VPP)."""
        return 1.0

    @level_cost.setter
    def level_cost(self, value) -> None:
        self._level_cost = value
    
    @property
    def level_value(self) -> float:
        """Get level value (always 1.0 for VPP)."""
        return 1.0

    @level_value.setter
    def level_value(self, value) -> None:
        self._level_value = value
    
    @property
    def pool_cost(self) -> float:
        """Calculate the pool cost portion."""
        if self._level_value != 0.0:
            pool_cost = float(self._levels) / self._level_value * self._level_cost
            return pool_cost
        return 0.0
    
    @property
    def control_cost(self) -> float:
        """Calculate the control cost portion."""
        # Default: pool cost / 2
        control_cost = self.pool_cost / 2.0
        
        # Check for CONTROLCOST adder (6E)
        control_adder = None
        for adder in self.assigned_adders:
            if adder.xmlid == "CONTROLCOST":
                control_adder = adder
                break
        
        if control_adder:
            control_cost = control_adder.total_cost
        
        return control_cost
    
    @property
    def active_cost(self) -> float:
        """Calculate the active cost."""

    
        return self._compute_active_cost()


    
    def _compute_active_cost(self, exclude_xmlid: str = None) -> float:
        """
        Calculate active cost for VPP.
        
        Formula:
        Active Cost = (Total Cost - Pool Cost) × (1 + Advantages) + Pool Cost
        
        Advantages apply to control cost and other adders, but NOT to pool cost.
        """
        total_cost = self.total_cost
        pool_cost = self.pool_cost
        
        # Calculate advantage sum (from modifiers)
        advantage_sum = 0.0
        has_advantages = False
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            if exclude_xmlid and modifier.xmlid == exclude_xmlid:
                continue
            if modifier.total_value > 0.0:
                advantage_sum += modifier.total_value
                has_advantages = True
        
        # Add private modifiers (excluding limitations)
        for modifier in self.private_mods:
            if exclude_xmlid and modifier.xmlid == exclude_xmlid:
                continue
            if modifier.limitation_modifier:
                continue
            if modifier.total_value > 0.0:
                advantage_sum += modifier.total_value
                has_advantages = True
        
        # Apply advantages to non-pool portion only
        active_cost = (total_cost - pool_cost) * (1.0 + advantage_sum) + pool_cost
        
        if has_advantages:
            active_cost = round_half_down(active_cost)
        
        return active_cost
    
    @property
    def real_cost_pre_list(self) -> float:
        """
        Calculate real cost for VPP.
        
        Formula:
        Real Cost = (Active Cost - Pool Cost) / (1 + |Limitations|) + Pool Cost
        
        Limitations apply to control cost and other adders, but NOT to pool cost.
        """
        active_cost = self.active_cost
        pool_cost = self.pool_cost
        
        # Calculate limitation sum
        limitation_sum = 0.0
        has_limitations = False
        
        # Add assigned limitations
        for modifier in self.assigned_modifiers:
            if modifier.total_value < 0.0:
                limitation_sum += modifier.total_value  # Negative value
                has_limitations = True
        
        # Add private limitations
        for modifier in self.private_mods:
            if modifier.total_value < 0.0:
                limitation_sum += modifier.total_value
                has_limitations = True
        
        # Apply limitations to non-pool portion only
        real_cost = (active_cost - pool_cost) / (1.0 + abs(limitation_sum)) + pool_cost
        
        if has_limitations:
            real_cost = round_half_down(real_cost)
        
        # Minimum real cost
        if real_cost < 1.0:
            real_cost = 1.0
        
        # Apply multiplier (stub - requires rules access)
        # if rules.multiplier_allowed() and self.multiplier != 1.0:
        #     real_cost *= self.multiplier
        #     real_cost = round_half_down(real_cost)
        
        # Quantity cost
        if self._quantity > 1:
            quantity_cost = 0
            qty = float(self._quantity)
            while qty > 1.0:
                quantity_cost += 5
                qty /= 2.0
            real_cost += float(quantity_cost)
        
        return real_cost
    
    def real_cost_for_child(self, child: GenericObject) -> float:
        """
        Calculate real cost for a power in this VPP.
        
        VPP slots use their normal real cost (no framework reduction).
        However, Active Cost cannot exceed Pool Size.
        """
        return child.real_cost_pre_list
    
    def object_allowed(self, obj: GenericObject, show_warnings: bool = True) -> bool:
        """
        Check if an object can be added to this VPP.
        
        Validation:
        - Active Cost cannot exceed Pool Size
        - Cannot add Lists
        - Cannot nest VPPs
        """
        # Check base List validation
        if not super().object_allowed(obj, show_warnings):
            return False
        
        # Cannot nest VPPs. Uses is_vpp() (isinstance + xmlid fallback) so
        # both real VariablePowerPool instances and loader-created fallback
        # objects with xmlid="VPP" are caught.
        from kirby_cost.objects.frameworks import is_vpp
        if is_vpp(obj):
            self.error = "You cannot add a VPP into a VPP.  The Variable Power Pool will be placed outside."
            return False
        
        # Check Active Cost vs Pool Size
        active_cost = obj.active_cost
        pool_size = self._levels
        
        if active_cost > pool_size:
            self.error = f"The Active Cost of {obj.alias} exceeds the Pool Size of the VPP.  {obj.alias} will be placed outside of this VPP."
            return False
        
        return True
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = self._alias
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        if self.input and self.input.strip():
            output += f" ({self.input})"
        
        # Calculate control cost
        control_adder = None
        for adder in self.assigned_adders:
            if adder.xmlid == "CONTROLCOST":
                control_adder = adder
                break
        
        if control_adder:
            control_cost = control_adder.levels
        else:
            pool_cost = self.pool_cost
            control_cost = int(round_half_down(pool_cost / 2.0))
        
        output += f", {self._levels} base + {control_cost} control cost"
        
        adder_str = self.adder_string
        if adder_str and adder_str.strip():
            output += f"; {adder_str}"
        
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    
    def column2_suffix(self, obj: GenericObject) -> str:
        """Get suffix showing real cost."""
        real_cost = obj.real_cost_pre_list
        return f" Real Cost: {int(round_half_down(real_cost))}"
    
    

