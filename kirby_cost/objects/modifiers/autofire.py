"""
Autofire modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Autofire.java

Autofire modifier with custom getColumn2Output(), getTotalValue(), and included() methods.
Calculates shot count and applies surcharge for certain power types.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Autofire(Modifier, xmlid="AUTOFIRE"):
    """
    Autofire modifier.
    
    Power can autofire multiple shots.
    
    Has custom shot count calculation and surcharge logic for certain power types.
    Only applies to abilities that require an Attack Roll.
    """
    
    def __init__(self, element=None):
        """Initialize an Autofire modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        self.surcharge = False
        if element is not None:
            self._init(element)
    
    def surcharge_included(self) -> bool:
        """Check if surcharge should be included."""
        self.total_value  # This sets surcharge
        if GenericObject.find_object_by_id(self.assigned_adders, "ODDPOWER") is not None:
            return True
        return self.surcharge
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for Autofire modifier.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        
        # Get number of shots from selected option
        n = 1
        if self._selected_option is not None:
            n = self._selected_option.levels
            
            # Try to parse from alias if levels don't match
            if self._selected_option.alias != self._selected_option.display:
                alias = self._selected_option.alias
                num_str = ""
                for i, char in enumerate(alias):
                    if char.isdigit():
                        num_str += char
                    elif i > 0:
                        break
                if num_str:
                    try:
                        # `n = i` here — the LOOP INDEX, not the digits it had
                        # just collected. A renamed Autofire option therefore
                        # reported its own position in the string as a shot
                        # count.
                        n = int(num_str)
                    except ValueError:
                        pass
        
        n2 = 1  # Double multiplier
        d = self.total_value
        
        # Handle adders
        for adder in self.assigned_adders:
            if adder.xmlid == "DOUBLE":
                n2 = int(pow(adder.level_power, adder.levels))
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
        string2 = string2 + str(n * n2) + " shots;"
        string2 = string2 + " "
        
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
    def total_value(self) -> float:
        """
        Get total value of this modifier.
        
        Adds surcharge for certain power types.
        """
        d = self.base_cost
        
        # Add adder costs
        for adder in self.assigned_adders:
            d += adder.double_total()
        
        # Add level costs
        if self._level_value > 0.0:
            d += float(self._levels) / self._level_value * self._level_cost
        
        # Apply advantages
        advantage_sum = 0.0
        for modifier in self.assigned_modifiers:
            if modifier.total_value > 0.0:
                advantage_sum += modifier.total_value
        
        if advantage_sum > 0.0:
            d = d * (1.0 + advantage_sum)
        
        # Apply limitations
        limitation_sum = 0.0
        for modifier in self.assigned_modifiers:
            if modifier.total_value < 0.0:
                limitation_sum += abs(modifier.total_value)
        
        if limitation_sum > 0.0:
            d = d / (1.0 + limitation_sum)
        
        # Round to quarter
        sign = 1
        if d < 0.0:
            sign = -1
        d = abs(d) * 4.0
        from kirby_cost.util.rounder import round_half_up
        d = round_half_up(d)
        d = (d / 4.0) * sign
        
        # Check for surcharge
        self.surcharge = False
        if self.parent is not None:
            from kirby_cost.objects.powers.power import Power
            from kirby_cost.objects.powers.naked_modifier import NakedModifier
            from kirby_cost.objects.powers.images import Images
            from kirby_cost.objects.powers.absorption import Absorption
            
            if (isinstance(self.parent, Power) and 
                not isinstance(self.parent, NakedModifier) and
                not isinstance(self.parent, Images) and
                not isinstance(self.parent, Absorption)):
                
                parent = self.parent

                # Java (Autofire.java getTotalValue) swaps the power's
                # COMBINED modifiers (own + parent list) in before the
                # target / NND / AVLD checks, so the target check sees
                # AOE/EXPLOSION/BOECV etc. (getTarget -> "HEX"/"ECV") and
                # the NND/AVLD lookups see framework-level modifiers.
                all_mods = parent._java_all_assigned_modifiers()

                # Check target (modifier-aware — Java getTarget())
                if parent.effective_target() != "DCV":
                    self.surcharge = True

                # Check types
                types = parent.types
                if types and "MENTAL" in types:
                    self.surcharge = True

                # Check for NND or AVLD
                if GenericObject.find_object_by_id(all_mods, "NND") is not None:
                    self.surcharge = True
                if GenericObject.find_object_by_id(all_mods, "AVLD") is not None:
                    self.surcharge = True
                
                # Check for specific power types
                from kirby_cost.objects.powers.drain import Drain
                from kirby_cost.objects.powers.transform import Transform
                from kirby_cost.objects.powers.aid import Aid
                from kirby_cost.objects.powers.dispel import Dispel
                from kirby_cost.objects.powers.healing import Healing
                
                if isinstance(parent, (Drain, Transform, Aid, Dispel, Healing)):
                    self.surcharge = True
        
        # ODDPOWER adder removes surcharge
        if GenericObject.find_object_by_id(self.assigned_adders, "ODDPOWER") is not None:
            self.surcharge = False
        
        # Add surcharge if applicable
        # Note: Would need HeroDesigner.getInstance().getPrefs().isModifierIntelligenceOn() check
        if self.surcharge:
            d += 1.0
        
        # Apply min/max limits
        if d < self._minimum_cost and self.min_set:
            d = self._minimum_cost
        if d > self._max_cost and self.max_set:
            d = self._max_cost
        
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
        
        # Can be applied to Strength
        from kirby_cost.objects.characteristics.strength import Strength
        if isinstance(generic_object, Strength):
            return ""
        
        # Can be applied to Maneuver
        from kirby_cost.objects.martial_arts.maneuver import Maneuver
        if isinstance(generic_object, Maneuver):
            return ""
        
        # Can be applied to Absorption
        from kirby_cost.objects.powers.absorption import Absorption
        if isinstance(generic_object, Absorption):
            return ""
        
        # Can only be applied to abilities which require an Attack Roll
        target = generic_object.effective_target()
        if target == "SELFONLY" or target == "N/A":
            return f"{self.display} can only be applied to abilities which require an Attack Roll"
        
        return ""
