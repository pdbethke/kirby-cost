"""
AlternateCombatValue modifier for kirby-cost.

Converted from com.hero.objects.modifiers.AlternateCombatValue.java

AlternateCombatValue modifier with custom getOptions(), getSelectedOption(),
and included() methods. Filters options based on mental vs non-mental powers.
"""

from typing import List
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.adder import Adder


class AlternateCombatValue(Modifier, xmlid="ACV"):
    """
    AlternateCombatValue modifier.
    
    Allows power to target alternate combat value.
    
    Has custom option filtering for mental vs non-mental powers.
    Uses base class getColumn2Output() method.
    """
    
    def __init__(self, element=None):
        """Initialize a AlternateCombatValue modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def options(self) -> List[Adder]:
        """
        Get options, filtered based on mental vs non-mental power.
        
        Returns:
            List of filtered option adders
        """
        options = super().options
        filtered_options = []
        
        progenitor = self.progenitor
        if progenitor is None:
            return options
        
        from kirby_cost.objects.powers.power import Power
        if not isinstance(progenitor, Power):
            return options
        
        types = progenitor.types
        is_mental = types and "MENTAL" in types
        
        if is_mental:
            # Clear selected option if it's NONMENTAL
            selected = self._selected_option
            if selected and "NONMENTAL" in selected.xmlid:
                self._selected_option = None
            
            # Filter out NONMENTAL options
            for option in options:
                if "NONMENTAL" not in option.xmlid:
                    filtered_options.append(option)
        else:
            # Clear selected option if it's not NONMENTAL
            selected = self._selected_option
            if selected and "NONMENTAL" not in selected.xmlid:
                self._selected_option = None
            
            # Only include NONMENTAL options
            for option in options:
                if "NONMENTAL" in option.xmlid:
                    filtered_options.append(option)
        
        return filtered_options
    
    @property
    def selected_option(self) -> Adder:
        """
        Get selected option, validating against power type.
        
        Returns:
            Selected option adder or None
        """
        option = self._selected_option
        
        progenitor = self.progenitor
        if progenitor is None:
            return option
        
        from kirby_cost.objects.powers.power import Power
        if not isinstance(progenitor, Power):
            return option
        
        types = progenitor.types
        is_mental = types and "MENTAL" in types
        
        if option:
            if is_mental and "NONMENTAL" in option.xmlid:
                self._selected_option = None
                return None
            elif not is_mental and "NONMENTAL" not in option.xmlid:
                self._selected_option = None
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
        
        # Can only be applied to abilities that are targeted on others
        target = generic_object.effective_target()
        if target in ("OCV", "ECV", "OMCV", "MCV", "DCV", "DMCV", "HEX"):
            return ""
        
        return f"{self.display} can only be applied to abilities that are targeted on others."
