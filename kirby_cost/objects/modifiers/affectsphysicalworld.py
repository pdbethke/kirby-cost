"""
AffectsPhysicalWorld modifier for kirby-cost.

Converted from com.hero.objects.modifiers.AffectsPhysicalWorld.java

AffectsPhysicalWorld modifier with custom included() method.
Validates desolidification requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class AffectsPhysicalWorld(Modifier, xmlid="AFFECTSPHYSICALWORLD"):
    """
    AffectsPhysicalWorld modifier.
    
    Allows power to affect physical world while desolidified.
    """
    
    def __init__(self, element=None):
        """Initialize a AffectsPhysicalWorld modifier."""
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
        
        from kirby_cost.objects.powers.naked_modifier import NakedModifier
        from kirby_cost.objects.powers.compound_power import CompoundPower
        from kirby_cost.objects.powers.desolidification import Desolidification
        from kirby_cost.core.context import EngineContext
        if isinstance(generic_object, NakedModifier):
            return ""
        # AffectsPhysicalWorld.java:50 calls o.getTarget() -- the modifier-aware
        # read (GenericObject.java:2805-2828: a SELFONLY/BASEDONCON/UOO/BOECV/
        # AOE/EXPLOSION modifier changes what target() answers), not the raw
        # ``target`` attribute. A power with target DCV but a SELFONLY
        # modifier attached (e.g. an Adjustable Drain slot) reads back as
        # SELFONLY here, exactly as HD's own echo shows.
        target = generic_object.effective_target()
        if target in ("SELFONLY", "N/A") and generic_object.xmlid not in ("SUMMON", "DUPLICATION"):
            return f"{self.display} can only be applied to Powers which affect others."
        if isinstance(generic_object, Desolidification):
            return f"{self.display} cannot be applied to Desolidification.  It should be applied to the actual Powers/abilities that will affect the physical world while the character is Desolidified."
        # Check if character has Desolidification
        active_hero = EngineContext.active_hero()
        if active_hero:
            for power in active_hero.powers:
                if isinstance(power, Desolidification):
                    return ""
                if isinstance(power, CompoundPower):
                    for sub_power in power.powers:
                        if isinstance(sub_power, Desolidification):
                            return ""
        return f"{self.display} may only be purchased by characters who have Desolidification."
