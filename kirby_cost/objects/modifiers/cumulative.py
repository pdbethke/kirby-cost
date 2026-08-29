"""
Cumulative modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Cumulative.java

Cumulative modifier with custom getColumn2Output(), getLevelInfo(), and included() methods.
Calculates accumulation points and validates power type restrictions.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Cumulative(Modifier, xmlid="CUMULATIVE"):
    """
    Cumulative modifier.
    
    Power effects are cumulative.
    
    Has custom accumulation point calculation and validation for power type restrictions.
    Cannot be applied to damage powers or certain cumulative powers.
    """
    
    def __init__(self, element=None):
        """Initialize a Cumulative modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for Cumulative modifier.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        d = self.total_value
        
        # Handle adders
        for adder in self.assigned_adders:
            if string:
                string = string + ", "
            string = string + adder.alias + " (" + self.get_fraction(adder.base_cost) + ")"
            d -= adder.base_cost
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + ", " + modifier.alias
        
        string2 = string2 + " ("
        
        # Add level info if levels > 0
        if self._levels > 0:
            string2 = string2 + self.level_info + "; "
        
        # Add input
        if self.input and self.input.strip():
            string2 = string2 + self.input + "; "
        
        # Add comments
        if self.comments.strip():
            string2 = string2 + self.comments + "; "
        
        string2 = string2 + self.get_fraction(d) + ")"
        
        # Append adders string
        if string.strip():
            if string2.strip():
                string2 = string2 + ", "
            string2 = string2 + string
        
        return string2
    
    @property
    def level_info(self) -> str:
        """
        Get level info string.
        
        Returns number of points that can be accumulated.
        """
        n = self._levels
        if self.progenitor is not None:
            progenitor = self.progenitor
            n2 = progenitor.levels * 6
            
            # Add dice adders
            for adder in progenitor.assigned_adders:
                if adder.xmlid == "PLUSONEHALFDIE":
                    n2 += 3
                elif adder.xmlid == "PLUSONEPIP":
                    n2 += 1
            
            from kirby_cost.util.rounder import round_half_up
            n = int(round_half_up(float(n2) * pow(2.0, n)))
        
        return str(n) + " points"
    
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
        
        # Cannot be applied to Absorption, Aid, Healing
        from kirby_cost.objects.powers.absorption import Absorption
        from kirby_cost.objects.powers.aid import Aid
        from kirby_cost.objects.powers.healing import Healing
        
        if isinstance(generic_object, (Absorption, Aid, Healing)):
            return (f"{generic_object.display} cannot have Cumulative applied to it, "
                   f"since it already has its own rules for how many Character points can be "
                   f"added to a particular Characteristic or Power and how and at what rate "
                   f"they're added.")
        
        # Cannot be applied to Transform
        from kirby_cost.objects.powers.transform import Transform
        if isinstance(generic_object, Transform):
            return f"{generic_object.display} is already cumulative in nature."
        
        # Cannot be applied to abilities that cause STUN or BODY damage
        if generic_object.does_damage:
            return f"{self._display} cannot be applied to abilities that cause STUN or BODY damage."
        
        # Can only be applied to abilities which act against a target's Defenses
        if generic_object.defense == "NONE":
            return f"{self._display} can only be applied to abilities which act against a target's Defenses"
        
        # Can only be applied to abilities which require an Attack Roll
        target = generic_object.target
        if target == "SELFONLY" or target == "N/A":
            return f"{self._display} can only be applied to abilities which require an Attack Roll."
        
        return ""
