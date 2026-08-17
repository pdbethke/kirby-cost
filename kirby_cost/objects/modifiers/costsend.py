"""
CostsEND modifier for kirby-cost.

Converted from com.hero.objects.modifiers.CostsEND.java

CostsEND modifier with custom getColumn2Output() and included() methods.
Handles HALFEND option and validates duration requirements.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class CostsEND(Modifier, xmlid="COSTSEND"):
    """
    CostsEND modifier.
    
    Power costs END to use.
    """
    
    def __init__(self, element=None):
        """Initialize a CostsEND modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for CostsEND modifier.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        
        # Handle HALFEND option
        if (self._selected_option is not None and 
            self._selected_option.xmlid == "HALFEND"):
            string2 = self._selected_option.alias
        
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
        
        # Handle selected option display
        if (self._selected_option is not None and 
            self._selected_option.display_in_string and 
            self._selected_option.alias.strip()):
            string2 = string2 + " (" + self._selected_option.alias
        
        # Count parentheses for proper closing
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
    
    @property
    def options(self) -> list:
        """
        Get available options for this modifier.
        
        Filters options based on power duration.
        """
        options = super().options
        progenitor = self.progenitor
        
        if progenitor is None or not hasattr(progenitor, 'duration'):
            return options
        
        # Check if progenitor is a Power
        from kirby_cost.objects.powers.power import Power
        if not isinstance(progenitor, Power):
            return options
        
        duration = progenitor.duration
        
        # For 6E, handle INSTANT powers differently
        # Note: Would need HeroDesigner.getActiveTemplate().is6E() check
        # For now, assume 6E behavior
        if duration == "INSTANT":
            filtered_options = []
            for option in options:
                if option.xmlid != "INSTANT":
                    filtered_options.append(option)
            
            # If HALFEND was selected, switch to first available option
            if (self._selected_option is not None and 
                self._selected_option.xmlid == "ACTIVATE" and
                len(filtered_options) > 0):
                self._selected_option = filtered_options[0]
            
            return filtered_options
        
        return options
    
    @property
    def selected_option(self):
        """
        Get the selected option.
        
        Handles special case for INSTANT powers.
        """
        option = self._selected_option
        progenitor = self.progenitor
        
        if progenitor is None or not hasattr(progenitor, 'duration'):
            return option
        
        from kirby_cost.objects.powers.power import Power
        if not isinstance(progenitor, Power):
            return option
        
        duration = progenitor.duration
        
        # For INSTANT powers without continuing effect
        if duration == "INSTANT" and not progenitor.continuing_effect():
            # For 6E, handle ACTIVATE option
            # Note: Would need HeroDesigner.getActiveTemplate().is6E() check
            if (self._selected_option is not None and 
                self._selected_option.xmlid == "ACTIVATE" and
                self._options and len(self._options) > 0):
                self._selected_option = self._options[0]
                return self._selected_option
            else:
                # For non-6E, clear option and reset base cost
                self._base_cost = self.orig_base_cost
                return None
        
        return option
    
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
        
        # Cannot be applied to Endurance Reserve or its Recovery
        from kirby_cost.objects.powers.endurance_reserve import EnduranceReserve
        from kirby_cost.objects.powers.endurance_reserve_recovery import EnduranceReserveRecovery
        
        if isinstance(generic_object, (EnduranceReserve, EnduranceReserveRecovery)):
            return f"{self._display} cannot be applied to an Endurance Reserve or its Recovery."
        
        # Cannot be applied to non-Persistent (5E only)
        # Note: Would need HeroDesigner.getActiveTemplate().is6E() check
        nonpersistent = GenericObject.find_object_by_id(
            generic_object.assigned_modifiers, "NONPERSISTENT")
        if nonpersistent is not None:
            # Assume 6E for now - would check template version
            pass
        
        # Cannot be applied with Reduced END
        if GenericObject.find_object_by_id(
            generic_object.assigned_modifiers, "REDUCEDEND") is not None:
            return f"{self._display} cannot be applied to an ability with Reduced END."
        
        # Cannot be applied with Costs END Only To Activate
        if GenericObject.find_object_by_id(
            generic_object.assigned_modifiers, "COSTSENDONLYTOACTIVATE") is not None:
            return f"{self._display} cannot be applied to an ability with Costs END Only To Activate."
        
        # Cannot be applied with Costs END To Maintain
        if GenericObject.find_object_by_id(
            generic_object.assigned_modifiers, "COSTSENDTOMAINTAIN") is not None:
            return f"{self._display} cannot be applied to an ability with Costs END To Maintain."
        
        # Can only be applied if power doesn't already cost END
        if generic_object.end_usage == 0:
            return ""
        
        return f"{self._display} cannot be applied to an ability which already costs END."
