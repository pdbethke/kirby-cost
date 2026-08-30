"""
NoRangeModifier modifier for kirby-cost.

Converted from com.hero.objects.modifiers.NoRangeModifier.java

NoRangeModifier modifier with custom included() method.
Validates range requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class NoRangeModifier(Modifier, xmlid="NORANGEMODIFIER"):
    """
    NoRangeModifier modifier.
    
    Power is not subject to range modifiers.
    """
    
    def __init__(self, element=None):
        """Initialize a NoRangeModifier modifier."""
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
        # NoRangeModifier.java:42-63. Note the ORDER: Java runs
        # super.included() but does NOT return on it until AFTER the
        # Teleportation check, so a 6E Teleportation is allowed even when the
        # generic rules refused it. The port had the guard first.
        result = super().included(generic_object)

        if self.force_allow:
            return result

        from kirby_cost.objects.base import is_6e
        from kirby_cost.objects.frameworks.multipower import Multipower
        from kirby_cost.objects.frameworks.elemental_control import ElementalControl
        from kirby_cost.objects.powers.teleportation import Teleportation

        # Java asks HeroDesigner.getActiveTemplate().is6E();
        # EngineContext.active_template() is None everywhere, so this took its
        # 5E form under every 6E template.
        if isinstance(generic_object, Teleportation) and is_6e():
            return ""

        if result and result.strip():
            return result

        if isinstance(generic_object, (Multipower, ElementalControl)):
            return ""
        # Java's third alternative is `o instanceof FindWeakness`, a 5E power:
        # Main6E declares no FINDWEAKNESS element and the engine has no class
        # for it, so the xmlid stands in rather than an import that cannot
        # resolve. Unreachable under Main6E; kept so the rule is complete.
        if (generic_object.xmlid or "").upper() == "FINDWEAKNESS":
            return ""

        if generic_object.range_value <= 0:
            return f"{self.display} can only be applied to Ranged Powers."

        return ""
