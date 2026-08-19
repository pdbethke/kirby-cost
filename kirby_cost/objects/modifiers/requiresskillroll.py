"""
Requires Skill Roll modifier for kirby-cost.

Converted from com.hero.objects.modifiers.RequiresSkillRoll.java

Requires a skill roll to activate the power.
"""

from kirby_cost.objects.base import option_alias
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class RequiresSkillRoll(Modifier, xmlid="REQUIRESASKILLROLL"):
    """
    Requires Skill Roll modifier.
    
    Requires a skill roll to activate the power.
    """
    
    def __init__(self, element=None):
        """Initialize a Requires Skill Roll modifier."""
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
        
        # No additional validation needed - uses base class validation
        # RequiresSkillRoll modifier doesn't override included() in Java source
        return ""

    @property
    def column2_output(self) -> str:
        """``Requires A Roll (14- roll; -1/4)``.

        Ported from ``RequiresSkillRoll.getColumn2Output`` (6E branch). This
        class had none and inherited the generic modifier line, which puts the
        option after the alias rather than inside the brackets:
        "Requires A Roll 14- roll (-1/4)".

        Java dereferences `getSelectedOption()` here without a null check —
        a Requires A Roll always has one in HD. `option_alias` reads the
        document's OPTION_ALIAS, which says the same thing and does not
        raise when the loader has not resolved the object.

        The 5E branch differs only in omitting that option, and is unreachable
        for this corpus.
        """
        ret = self.alias or ""
        val = self.total_value
        adder_str = ""
        for ad in self.assigned_adders:
            if adder_str:
                adder_str += ", "
            adder_str += ad.alias or ""
        if self.input and self.input.strip():
            if ret.strip():
                ret += ":  "
            ret += self.input
        for mod in self.assigned_modifiers:
            ret += ", " + (mod.alias or "")
        ret += " ("
        ret += (option_alias(self) or "") + "; "
        if adder_str.strip():
            ret += adder_str + "; "
        if (self.comments or "").strip():
            ret += self.comments + "; "
        ret += self.get_fraction(val) + ")"
        return ret
