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
        """``Costs Endurance (Costs Half Endurance; -1/4)``.

        Ported from ``CostsEND.getColumn2Output``. The option says HOW MUCH
        endurance, and the generic line dropped it — leaving "Costs Endurance
        (-1/4)", which is the price without the term. HALFEND is the one
        option that REPLACES the alias rather than following it, because
        "Costs Half Endurance" already contains the word.
        """
        from kirby_cost.objects.base import option_alias
        ret = self.alias or ""
        option = self._selected_option
        option_id = (getattr(option, "xmlid", "") or "").upper() or \
            (getattr(self, "option_id", "") or "").upper()
        alias = (option_alias(self) or "").strip()
        if option_id == "HALFEND" and alias:
            ret = alias
        val = self.total_value
        if self.input and self.input.strip():
            if ret.strip():
                ret += " "
            ret += self.input
        ret = ret.strip()
        for mod in self.assigned_modifiers:
            ret += ", " + (mod.alias or "")
        if option is not None and getattr(option, "display_in_string", True) and alias:
            ret += " (" + alias

        paren = ret.count("(") - ret.count(")")
        ret += " (" if paren <= 0 else "; "
        for ad in self.assigned_adders:
            if not getattr(ad, "is_selected", True):
                continue
            text = (ad.column2_output or "").strip()
            if text:
                ret += text + "; "
        if (self.comments or "").strip():
            ret += self.comments + "; "
        if val > self._max_cost and self.max_set:
            val = self._max_cost
        if val < self._minimum_cost and self.min_set:
            val = self._minimum_cost
        ret += self.get_fraction(val) + ")"
        paren -= 1
        while paren > 0:
            ret += ")"
            paren -= 1
        return ret
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
        if duration == "INSTANT" and not progenitor.continuing_effect:
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
