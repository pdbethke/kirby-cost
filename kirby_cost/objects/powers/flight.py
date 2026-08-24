"""
Flight power class for kirby-cost.

Converted from com.hero.objects.powers.Flight.java

Flight is a movement power that allows the character to fly.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_down


class Flight(Power, xmlid="FLIGHT"):
    """
    Flight power.
    
    Movement power that allows the character to fly through the air.
    """
    
    def __init__(self):
        """Initialize a Flight power."""
        super().__init__()
        self.xmlid = Flight.XMLID
        self.affects_primary = True  # Affects primary characteristics
        self._duration = "CONSTANT"
    
    @property
    def uses_end(self) -> bool:
        """``Flight.usesEND`` (Flight.java:41-47): NOT in 6E when Gliding.

        Two bugs in one. It was a stub -- "would check if 6E and has GLIDING
        modifier" -- and it was written as a METHOD whose body returned
        `self.uses_end`, which the base class assigns as an instance
        ATTRIBUTE. So it was shadowed and never ran; had it run it would have
        recursed. Exactly the shape of the resistant_defenses bug.

        A property with a setter, because the base assigns to this name both
        in __init__ and in apply_template; a read-only one breaks loading.
        """
        from kirby_cost.objects.base import is_6e, GenericObject
        if is_6e() and GenericObject.find_object_by_id(
                self.assigned_modifiers, "GLIDING") is not None:
            return False
        return getattr(self, "_uses_end_flag", False)

    @uses_end.setter
    def uses_end(self, value: bool) -> None:
        self._uses_end_flag = bool(value)
    
    @property
    def damage_display(self) -> str:
        """
        Get movement display string.
        
        Format: "Xm" (6E) or "X\"" (5E)
        """
        # Calculate movement from levels
        if self._level_value != 0.0:
            movement = round_down(float(self._levels) / self._level_value)
        else:
            movement = self._levels
        
        # Stub: would check if 6E
        is_6e = True  # Default to 6E
        
        if is_6e:
            return f"{int(movement)}m"
        else:
            return f"{int(movement)}\""
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string for display.
        
        Format: "Power Name Xm, [adders]; [modifiers]"
        """
        output = f"{self._alias} {self.damage_display}"
        
        # Add name if present
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Add input if present
        if self.input and self.input.strip():
            output += f":  {self.input}"
        
        # Add selected option
        if self._selected_option:
            output += f", {self._selected_option.alias}"
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                output += f"; {adder_str}"
        else:
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                output += f", {adder_str}"
        
        # Add modifiers
        modifier_str = self.modifier_string
        output += modifier_str
        
        # Add END usage note (stub - would check for END Reserve)
        # if self.get_end_usage() > 0:
        #     output += " (uses Personal END)"  # or " (uses END Reserve)"
        
        return output
    
    @property
    def summable(self) -> bool:
        """Check if Flight can be summed with other movement powers."""
        return True
    
    

