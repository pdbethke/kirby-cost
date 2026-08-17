"""
SemiArmorPiercing modifier for kirby-cost.

Converted from com.hero.objects.modifiers.SemiArmorPiercing.java

SemiArmorPiercing modifier with custom getColumn2Output() and included() methods.
Formats with levels multiplier and validates target/defense requirements.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class SemiArmorPiercing(Modifier, xmlid="SEMIARMORPIERCING"):
    """
    SemiArmorPiercing modifier.
    
    Attack is semi-armor piercing.
    
    Has custom formatting with levels multiplier and validation for target/defense.
    """
    
    def __init__(self, element=None):
        """Initialize a SemiArmorPiercing modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for SemiArmorPiercing modifier.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        d = self.total_value
        
        # Add selected option
        if self._selected_option is not None:
            string2 = string2 + " " + self._selected_option.alias
        
        # Add input
        if self.input and self.input.strip():
            if string2.strip():
                string2 = string2 + " "
            string2 = string2 + self.input
        
        string2 = string2.strip()
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + ", " + modifier.alias
        
        # Add levels multiplier if > 1
        if self._levels > 1:
            string2 = string2 + " (x" + str(self._levels)
        
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
        
        string2 = string2 + self.fraction(d) + ")"
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
        
        # Can be applied to Strength
        from kirby_cost.objects.characteristics.strength import Strength
        if isinstance(generic_object, Strength):
            return ""
        
        # Can be applied to Teleportation
        from kirby_cost.objects.powers.teleportation import Teleportation
        if isinstance(generic_object, Teleportation):
            return ""
        
        # Can be applied to Maneuver
        from kirby_cost.objects.martial_arts.maneuver import Maneuver
        if isinstance(generic_object, Maneuver):
            return ""
        
        # Can be applied to NakedModifier
        from kirby_cost.objects.powers.naked_modifier import NakedModifier
        if isinstance(generic_object, NakedModifier):
            return ""
        
        # Can only be applied to abilities which affect/are targeted on others
        target = generic_object.target
        if target == "SELFONLY" or target == "N/A":
            return f"{self._display} can only be applied to abilities which affect/are targeted on others."
        
        # Can only be applied to abilities which act against a target's defenses
        if generic_object.defense == "NONE":
            return f"{self._display} can only be applied to abilities which act against a target's defenses."
        
        return ""
