"""
ActivationRoll modifier for kirby-cost.

Converted from com.hero.objects.modifiers.ActivationRoll.java

ActivationRoll modifier with custom getColumn2Output() and setSelectedOption() methods.
Handles BURNOUT adder cost calculation and formatting. Uses base class included() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.adder import Adder


class ActivationRoll(Modifier, xmlid="ACTIVATIONROLL"):
    """
    ActivationRoll modifier.
    
    Requires activation roll to use power.
    
    Has custom formatting for BURNOUT and JAMMED adders, and cost calculation.
    Uses base class included() method.
    """
    
    def __init__(self, element=None):
        """Initialize a ActivationRoll modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
            self._init_burnout_adder()
    
    def _init_burnout_adder(self) -> None:
        """Initialize BURNOUT adder cost based on selected option."""
        # Find BURNOUT adder in available adders
        burnout_adder = None
        for adder in self.available_adders:
            if adder.xmlid == "BURNOUT":
                burnout_adder = adder
                break
        
        if burnout_adder is None:
            return
        
        burnout_adder.set_selectable(True)
        
        # Calculate cost based on next option
        options = self.options
        if len(options) <= 1:
            burnout_adder.base_cost = 0.25
            return
        
        selected = self._selected_option
        if selected:
            selected_index = options.index(selected) if selected in options else -1
            if selected_index >= 0 and selected_index + 1 < len(options):
                next_option = options[selected_index + 1]
                cost = max(next_option.base_cost - selected.base_cost, 0.25)
                burnout_adder.base_cost = cost
            else:
                burnout_adder.base_cost = 0.25
        else:
            burnout_adder.base_cost = 0.25
    
    @property
    def selected_option(self):
        """Get the selected option."""
        return self._selected_option

    @selected_option.setter
    def selected_option(self, adder: Adder) -> None:
        """
        Set selected option and update BURNOUT adder cost.
        
        Args:
            adder: The option adder to select
        """
        self._selected_option = adder
        
        if adder is not None:
            # Update base cost from selected option
            self._base_cost = adder.base_cost
            
            # Update BURNOUT adder cost
            burnout_available = None
            burnout_assigned = None
            
            for available_adder in self.available_adders:
                if available_adder.xmlid == "BURNOUT":
                    burnout_available = available_adder
                    break
            
            for assigned_adder in self.assigned_adders:
                if assigned_adder.xmlid == "BURNOUT":
                    burnout_assigned = assigned_adder
                    break
            
            if burnout_available or burnout_assigned:
                options = self.options
                selected_index = options.index(adder) if adder in options else -1
                
                if selected_index >= 0 and selected_index + 1 < len(options):
                    next_option = options[selected_index + 1]
                    cost = max(next_option.base_cost - adder.base_cost, 0.25)
                    
                    if burnout_available:
                        burnout_available.base_cost = cost
                        burnout_available.set_minimum_cost(cost)
                        burnout_available.max_cost = cost
                    
                    if burnout_assigned:
                        burnout_assigned.base_cost = cost
                        burnout_assigned.set_minimum_cost(cost)
                        burnout_assigned.max_cost = cost
                else:
                    cost = 0.25
                    if burnout_available:
                        burnout_available.base_cost = cost
                        burnout_available.set_minimum_cost(cost)
                        burnout_available.max_cost = cost
                    
                    if burnout_assigned:
                        burnout_assigned.base_cost = cost
                        burnout_assigned.set_minimum_cost(cost)
                        burnout_assigned.max_cost = cost
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for ActivationRoll modifier.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        
        # Add selected option
        if self._selected_option is not None:
            string2 = string2 + " " + self._selected_option.alias
        
        d = self.total_value
        
        # Handle adders (BURNOUT and JAMMED go in main string, others in separate)
        for adder in self.assigned_adders:
            if adder.xmlid == "BURNOUT":
                string2 = string2 + ", " + adder.alias
            elif adder.xmlid == "JAMMED":
                string2 = string2 + ", " + adder.alias
            else:
                if string:
                    string = string + ", "
                string = string + adder.alias + " (" + self.get_fraction(adder.base_cost) + ")"
                d -= adder.base_cost
        
        # Add input
        if self.input and self.input.strip():
            if string2.strip():
                string2 = string2 + ":  "
            string2 = string2 + self.input
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + ", " + modifier.alias
        
        string2 = string2 + " ("
        
        # Add comments
        if self.comments.strip():
            string2 = string2 + self.comments + "; "
        
        string2 = string2 + self.get_fraction(d) + ")"
        
        # Append other adders string
        if string.strip():
            if string2.strip():
                string2 = string2 + ", "
            string2 = string2 + string
        
        return string2
    
    def refresh_adders_on_update(self) -> bool:
        """Check if adders should be refreshed on update."""
        return True
    
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
        # ActivationRoll modifier doesn't override included() in Java source
        return ""
