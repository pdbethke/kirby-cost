"""
Mind Link power class for kirby-cost.

Converted from com.hero.objects.powers.MindLink.java

Power to link minds.
"""

from kirby_cost.objects.powers.power import Power


class MindLink(Power, xmlid="MINDLINK"):
    """
    Mind Link power.
    
    Creates a mental link between minds.
    """
    
    def __init__(self):
        """Initialize a Mind Link power."""
        super().__init__()
        self.xmlid = MindLink.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Empty — Java's ``MindLink.getDamageDisplay`` returns "".

        How many minds is an ADDER ("Number of Minds (x8)"), not a damage
        figure, so "0 minds" was a number the power never had.
        """
        return ""
    @property
    def column2_output(self) -> str:
        """``Mind Link , Any Willing Target, Number of Minds (x8)``.

        Ported from ``MindLink.getColumn2Output``. The input and the
        MULTIPLECLASSES adders are collected into one phrase — "human and
        alien classes of minds" — rather than listed separately, and
        pluralised on the count.
        """
        from kirby_cost.objects.base import option_alias
        ret = f"{self.alias or ''} {self.damage_display}"
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"

        classes = []
        if self.input and self.input.strip():
            classes.append(self.input.strip())
        for ad in self.assigned_adders:
            if ad.xmlid == "MULTIPLECLASSES":
                ad.display_in_string = False
                classes.append(ad.alias or "")
        if classes:
            ret += ", "
            for i, c in enumerate(classes):
                if 0 < i < len(classes) - 1:
                    ret += ", "
                elif i > 0:
                    ret += " and "
                ret += c
            ret += " classes of minds" if len(classes) > 1 else " class of minds"

        option = (option_alias(self) or "").strip()
        if option:
            ret += ", " + option
        adders = self.adder_string
        if adders.strip():
            ret += f", {adders}"
        ret += self.modifier_string
        ret += self._end_reserve_note()
        return ret
