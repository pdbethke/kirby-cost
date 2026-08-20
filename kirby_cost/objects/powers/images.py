"""
Images power class for kirby-cost.

Converted from com.hero.objects.powers.Images.java

Power to create images.
"""

from kirby_cost.objects.powers.sense_affecting_power import SenseAffectingPower


class Images(SenseAffectingPower, xmlid="IMAGES"):
    """
    Images power.
    
    Creates visual/auditory images.
    """
    
    def __init__(self):
        """Initialize an Images power."""
        super().__init__()
        self.xmlid = Images.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get images display."""
        return f"{self._levels}m radius"
    
    @property
    def column2_output(self) -> str:
        """``Sight Group Flash 4d6`` — what it affects, then what it is.

        Ported from ``Images.getColumn2Output``. All three sense-affecting
        powers open with the groups and senses they act on and only then name
        themselves; this printed the alias first and the group last, which is
        the same words in the wrong order.
        """
        ret = self._sense_prefix()
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        ret += " " + (self.alias or "")
        if self.input and self.input.strip():
            ret += f":  {self.input}"
        adders = self.adder_string
        if adders.strip():
            ret += f", {adders}"
        # INCREASEDRADIUS and ALTEREDSHAPE are folded into the line above
        # rather than listed as modifiers.
        from kirby_cost.objects.base import GenericObject as _GO
        for xmlid in ("INCREASEDRADIUS", "ALTEREDSHAPE"):
            mod = _GO.find_object_by_id(self.assigned_modifiers, xmlid)
            if mod is not None:
                mod.display_in_string = False
        ret += self.modifier_string
        ret += self._end_reserve_note()
        return ret
