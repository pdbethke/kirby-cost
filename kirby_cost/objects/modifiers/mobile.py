"""
Mobile modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Mobile.java

Mobile modifier with custom included() method.
Validates area effect requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Mobile(Modifier, xmlid="MOBILE"):
    """
    Mobile modifier.
    
    Makes an area effect mobile.
    """
    
    def __init__(self, element=None):
        """Initialize a Mobile modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
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
        
        if not generic_object.effective_target() == "HEX":
            return f"{self.display} can only be applied to Powers which already affect an area."
        
        return ""

    @property
    def limitation(self) -> bool:
        """Mobile is an advantage, not a limitation."""
        return False

    @property
    def is_limitation(self) -> bool:
        """Always False.

        Java overrides ``isLimitation`` on this modifier rather than inferring
        it, because the general rule gets it wrong: the value can sit at or
        above zero and it is still an advantage. Charges is the one that shows —
        "8 Continuing Charges lasting 1 Turn each (+0)" is worth nothing and
        still belongs after the semicolon.
        """
        return False
