"""
Absorption power class for kirby-cost.

Converted from com.hero.objects.powers.Absorption.java

Power to absorb damage and convert to other effects.
"""

from kirby_cost.objects.powers.power import Power


class Absorption(Power, xmlid="ABSORPTION"):
    """
    Absorption power.
    
    Absorbs damage and converts it to other effects (STUN, END, etc.).
    """
    
    def __init__(self):
        """Initialize an Absorption power."""
        super().__init__()
        self.xmlid = Absorption.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get absorption display string."""
        # Check for [LVL] in display
        if "[LVL]" in self._display.upper():
            return ""
        
        is_6e = True  # Stub: would check if 6E
        
        if is_6e:
            return f"{self._levels} BODY"
        else:
            # 5E: dice notation
            damage_str = f"{self._levels}d6"
            
            # Check for damage adders
            for adder in self.assigned_adders:
                if adder.xmlid == "PLUSONEPIP":
                    adder.display_in_string = False
                    damage_str = f"{self._levels}d6+1" if self._levels > 0 else "1 point"
                elif adder.xmlid == "PLUSONEHALFDIE":
                    adder.display_in_string = False
                    damage_str = f"{self._levels} 1/2d6"
                elif adder.xmlid == "MINUSONEPIP":
                    adder.display_in_string = False
                    damage_str = f"{self._levels + 1}d6-1"
            
            # Add standard effect if enabled
            if self.set_use_standard_effect():
                n = 0
                if any(a.xmlid in ("PLUSONEPIP", "PLUSONEHALFDIE") for a in self.assigned_adders):
                    n = 1
                elif any(a.xmlid == "MINUSONEPIP" for a in self.assigned_adders):
                    n = -1
                points = self._levels * 3 + n
                damage_str += f" (standard effect: {points} point{'s' if points != 1 else ''})"
            
            return damage_str

