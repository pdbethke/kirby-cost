"""
Shapeshift power class for kirby-cost.

Converted from com.hero.objects.powers.Shapeshift.java

Power to change shape.
"""

from kirby_cost.objects.powers.sense_affecting_power import SenseAffectingPower


class Shapeshift(SenseAffectingPower, xmlid="SHAPESHIFT"):
    """
    Shapeshift power.
    
    Power to change physical form.
    """
    
    def __init__(self):
        """Initialize a Shapeshift power."""
        super().__init__()
        self.xmlid = Shapeshift.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Empty — Java's ``Shapeshift.getDamageDisplay`` returns "".

        A Shape Shift is described by the senses it fools and the shapes it
        can take, both of which column2_output writes; "0 points" was a number
        with nothing behind it.
        """
        return ""
    @property
    def assigned_adders(self):
        """
        Get assigned adders with cost adjustments for 6E.
        
        In 6E, different sense groups have different costs.
        """
        adders = super().assigned_adders
        
        # Stub: would check if 6E and adjust costs based on sense type
        # For now, return as-is
        return adders

    @assigned_adders.setter
    def assigned_adders(self, value):
        # Java GenericObject.setAssignedAdders (GenericObject.java:3916) is
        # never overridden; getter-only Python overrides must re-expose it.
        self._assigned_adders = value

    @property
    def column2_output(self) -> str:
        """``Shape Shift  (Sight and Touch Groups, any humanoid shape)``.

        Ported from ``Shapeshift.getColumn2Output``. Unlike its siblings the
        groups go in BRACKETS after the alias rather than after a "to", and
        the SHAPES adder joins them inside the same bracket — what the
        character can turn into belongs with which senses are fooled.
        """
        from kirby_cost.objects.base import option_alias
        ret = f"{self.alias or ''} {self.damage_display}"
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        if self.input and self.input.strip():
            ret += f":  {self.input}"

        shapes = ""
        for ad in self.assigned_adders:
            if ad.xmlid == "SHAPES":
                ad.display_in_string = False
                shapes = (option_alias(ad) or "").strip()
        prefix = self._sense_prefix(default="[Unknown]")
        ret += " (" + prefix
        if shapes:
            ret += ", " + shapes
        ret += ")"
        adders = self.adder_string
        if adders.strip():
            ret += f", {adders}"
        ret += self.modifier_string
        ret += self._end_reserve_note()
        return ret
