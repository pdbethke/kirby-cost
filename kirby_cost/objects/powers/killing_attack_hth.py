"""
Hand-to-Hand Killing Attack power class for kirby-cost.

Converted from com.hero.objects.powers.KillingAttackHTH.java

HKA is a melee attack that does BODY damage.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_down


class KillingAttackHTH(Power, xmlid="HKA"):
    """
    Hand-to-Hand Killing Attack power.
    
    Melee attack that does BODY damage (killing damage).
    """
    
    def __init__(self):
        """Initialize a Hand-to-Hand Killing Attack power."""
        super().__init__()
        self.xmlid = KillingAttackHTH.XMLID
        self.does_damage = True
        self.does_body = True
        self.killing = True
        self.range = "HTH"
    
    @property
    def damage_display(self) -> str:
        """
        Get damage display string for HKA.
        
        Format: "Xd6" or "Xd6+1" or "Xd6-1" or "X 1/2d6"
        Includes STR bonus calculation if applicable.
        """
        # Base damage in pips
        n = self._levels * 3
        n2 = n  # BODY damage
        n3 = n  # STUN damage
        n4 = 0  # MINUSONEPIP flag
        stun_multiplier = 2  # Base STUN multiplier
        n6 = 0  # Half-die adjustment
        
        # Check for STUN multiplier modifiers
        for mod in self.all_assigned_modifiers:
            if mod.xmlid == "INCREASEDSTUNMULTIPLIER":
                stun_multiplier += mod.levels
            elif mod.xmlid == "DECREASEDSTUNMULTIPLIER":
                stun_multiplier -= mod.levels
        
        # Check for damage adders
        for adder in self.assigned_adders:
            if adder.xmlid == "PLUSONEPIP":
                adder.display_in_string = False
                n += 1
            elif adder.xmlid == "PLUSONEHALFDIE":
                adder.display_in_string = False
                n += 2
                n6 -= 1
            elif adder.xmlid == "MINUSONEPIP":
                adder.display_in_string = False
                n += 3
                n4 = 1
                n6 -= 2
        
        n2 = n - n4
        n7 = n + n6
        n3 = n - n4
        n8 = n + n6
        
        # Check for STR bonus (stub - would check NOSTRBONUS and STRMINIMUM modifiers)
        # For now, skip STR bonus calculation
        
        # Format damage string
        n10 = n // 3
        n11 = n % 3
        
        damage_str = ""
        if n10 != 0:
            damage_str = str(n10)
        
        if n11 == 1:
            damage_str = damage_str + "d6+1" if n10 > 0 else "1 point"
        elif n11 == 2:
            damage_str = damage_str + " 1/2d6"
        else:
            damage_str = damage_str + "d6"
        
        damage_str = damage_str.strip()
        
        if n4 != 0:
            damage_str = damage_str + f"-{n4}"
        
        # Add standard effect if enabled
        if self.uses_standard_effect():
            if self.does_body:
                damage_str += f" (standard effect: {n7}"
                if n7 != n8:
                    damage_str += f" / {n8}"
                damage_str += f" BODY, {n7 * stun_multiplier}"
                if n7 != n8:
                    damage_str += f" / {n8 * stun_multiplier}"
                damage_str += " STUN)"
            else:
                damage_str += f" (standard effect: {n7 * stun_multiplier}"
                if n7 != n8:
                    damage_str += f" / {n8 * stun_multiplier}"
                damage_str += " STUN)"
        
        return damage_str
    
    @property
    def all_assigned_modifiers(self):
        """Get all assigned modifiers including nested ones (stub)."""
        return self.assigned_modifiers
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = f"{self._alias} {self.damage_display}"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        if self.input and self.input.strip():
            output += f" (vs. {self.input})"
        
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
    
    @property
    def adder_string(self) -> str:
        """Get adder string (stub)."""
        return ""
    

