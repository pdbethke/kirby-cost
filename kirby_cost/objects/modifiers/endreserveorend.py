"""
ENDReserveOrEND modifier for kirby-cost.

Converted from com.hero.objects.modifiers.ENDReserveOrEND.java

ENDReserveOrEND modifier with custom included() method.
Validates END cost and Endurance Reserve requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class ENDReserveOrEND(Modifier, xmlid="ENDRESERVEOREND"):
    """
    ENDReserveOrEND modifier.
    
    Can use END Reserve or regular END.
    """
    
    def __init__(self, element=None):
        """Initialize a ENDReserveOrEND modifier."""
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
        
        from kirby_cost.objects.powers.endurance_reserve import EnduranceReserve
        from kirby_cost.objects.powers.endurance_reserve_recovery import EnduranceReserveRecovery
        from kirby_cost.objects.powers.compound_power import CompoundPower
        from kirby_cost.core.context import EngineContext
        if isinstance(generic_object, (EnduranceReserve, EnduranceReserveRecovery)):
            return f"{self._display} cannot be applied to an {generic_object.display}"
        if generic_object.end_usage == 0:
            return f"{self._display} can only be applied to abilities which cost END."
        # Check if character has Endurance Reserve
        active_hero = EngineContext.active_hero()
        if active_hero:
            for power in active_hero.powers:
                if isinstance(power, EnduranceReserve):
                    return ""
                if isinstance(power, CompoundPower):
                    for sub_power in power.powers:
                        if isinstance(sub_power, EnduranceReserve):
                            return ""
        return f"{self._display} can only be applied to abilities on characters that have an Endurance Reserve."
