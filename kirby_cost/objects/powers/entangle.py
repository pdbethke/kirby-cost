"""
Entangle power class for kirby-cost.

Converted from com.hero.objects.powers.Entangle.java

Entangle immobilizes targets.
"""

from kirby_cost.util.rounder import round_down
from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_down


class Entangle(Power, xmlid="ENTANGLE"):
    """
    Entangle power.
    
    Immobilizes targets with DEF and BODY values.
    """
    
    def __init__(self):
        """Initialize an Entangle power."""
        super().__init__()
        self.xmlid = Entangle.XMLID
        # Java's Entangle sets NEITHER doesDamage nor doesBODY, and
        # Main6E.hdt's <ENTANGLE> states neither attribute, so HD's object has
        # both false -- doesDamage() and doesBODY() are field reads
        # (GenericObject.java:903-905, :868-869) with nothing to read but the
        # default. The port hardcoded both True, which made an Entangle answer
        # three applicability rules the opposite way from HD.
    
    @property
    def damage_display(self) -> str:
        """``3d6, 3 PD/3 ED`` — the dice, then what the web can take.

        Ported from ``Entangle.getDamageDisplay`` (6E branch). This printed
        the 5E shape, "3d6, 3 DEF, 3 BODY": before 6E an Entangle had a single
        DEF and its BODY was worth stating, and in 6E it has separate physical
        and energy defences and the BODY is the dice. Different edition,
        different sentence.

        The adders that feed those numbers are marked not-to-be-printed once
        read, because the line has just said what they contribute.
        """
        levels = self._levels
        lv = self._level_value or 1.0
        bod = levels
        additional = 0
        add_eff = 0
        pd = int(round_down(levels / lv))
        ed = int(round_down(levels / lv))

        for ad in self.assigned_adders:
            if ad.xmlid == "ADDITIONALPD":
                pd += ad.levels
                ad.display_in_string = False
            elif ad.xmlid == "ADDITIONALED":
                ed += ad.levels
                ad.display_in_string = False
            elif ad.xmlid == "ADDITIONALBODY":
                bod += ad.levels
                additional += ad.levels
                ad.display_in_string = False

        base_dice = levels + additional
        ret = f"{base_dice}d6"
        additional = 0
        for ad in self.assigned_adders:
            if ad.xmlid == "PLUSONEPIP":
                ad.display_in_string = False
                ret = f"{base_dice}d6"
                additional = 1
                add_eff += 1
            elif ad.xmlid == "PLUSONEHALFDIE":
                ad.display_in_string = False
                ret = f"{base_dice} 1/2d6"
                add_eff += 1
            elif ad.xmlid == "MINUSONEPIP":
                ad.display_in_string = False
                ret = f"{base_dice + 1}d6"
                additional -= 1
                add_eff += 1
        if additional != 0:
            ret += " + " if additional > 0 else " - "
            ret += str(additional)

        for mod in self.all_assigned_modifiers:
            if mod.xmlid == "NODEFENSE":
                pd = 0
                ed = 0

        ret += f", {pd} PD/{ed} ED"
        if self.uses_standard_effect():
            ret += (f" (standard effect: {bod + add_eff} BODY, "
                    f"{pd} PD/{ed} ED)")
        return ret
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = f"{self._alias} {self.damage_display}"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        if self.input and self.input.strip():
            output += f":  {self.input}"
        
        if self._selected_option:
            output += f" ({self._selected_option.alias}"
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                output += f"; {adder_str}"
            output += ")"
        else:
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                output += f" ({adder_str})"
        
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    
    

