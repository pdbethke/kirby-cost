"""
Mage Sight Talent for kirby-cost.

Converted from com.hero.objects.talents.MageSight.java

Mage Sight is a sense-based talent for detecting magic.
"""

from typing import Optional
from kirby_cost.objects.powers.sense import Sense


class MageSight(Sense, xmlid="MAGESIGHT"):
    """
    Mage Sight Talent.
    
    A sense-based talent for detecting magic.
    Extends Sense power but saves as TALENT.
    """
    
    def __init__(self, element=None):
        """Initialize a Mage Sight talent."""
        # Sense.__init__ takes only an xmlid (matching the other Sense
        # subclasses); element is accepted for API symmetry but unused here.
        super().__init__(self.XMLID)
    
    @property
    def damage_display(self) -> str:
        """
        Get damage display (empty for talents).
        
        Returns:
            Empty string
        """
        return ""
    
    def get_save_xml(self):
        """
        Get XML element for saving.
        
        Returns:
            XML element with TALENT tag
        """
        element = super().get_save_xml()
        element.tag = "TALENT"
        return element



