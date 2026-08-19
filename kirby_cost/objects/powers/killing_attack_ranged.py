"""
Ranged Killing Attack power class for kirby-cost.

Converted from com.hero.objects.powers.KillingAttackRanged.java

RKA is a ranged attack that does BODY damage.
"""

from kirby_cost.objects.powers.power import Power


class KillingAttackRanged(Power, xmlid="RKA"):
    """
    Ranged Killing Attack power.
    
    Ranged attack that does BODY damage (killing damage).
    """
    
    def __init__(self):
        """Initialize a Ranged Killing Attack power."""
        super().__init__()
        self.xmlid = KillingAttackRanged.XMLID
        self.does_damage = True
        self.does_body = True
        self.killing = True
    
    @property
    def damage_display(self) -> str:
        """
        Get damage display string for RKA.
        
        Format: "Xd6" or "Xd6+1" or "Xd6-1" or "X 1/2d6"
        """
        # Base damage in pips
        n = self._levels * 3
        n2 = n  # BODY damage
        n3 = 0  # MINUSONEPIP flag
        stun_multiplier = 2  # Base STUN multiplier
        n5 = 0  # Half-die adjustment
        
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
                n2 += 1
            elif adder.xmlid == "PLUSONEHALFDIE":
                adder.display_in_string = False
                n += 2
                n2 += 2
                n5 -= 1
            elif adder.xmlid == "MINUSONEPIP":
                adder.display_in_string = False
                n += 3
                n2 += 3
                n3 = 1
                n5 -= 2
        
        # Format damage string
        n6 = n // 3
        n7 = n % 3
        
        damage_str = ""
        if n6 != 0:
            damage_str = str(n6)
        
        if n7 == 1:
            damage_str = damage_str + "d6+1" if n6 > 0 else "1 point"
        elif n7 == 2:
            damage_str = damage_str + " 1/2d6"
        else:
            damage_str = damage_str + "d6"
        
        damage_str = damage_str.strip()
        
        if n3 != 0:
            damage_str = damage_str + f"-{n3}"
        
        # Show BODY/STUN split if different
        if n != n2:
            damage_str += " / "
            n6 = n2 // 3
            n7 = n2 % 3
            damage_str += str(n6)
            if n7 == 1:
                damage_str += "d6+1"
            elif n7 == 2:
                damage_str += " 1/2d6"
            else:
                damage_str += "d6"
            if n3 != 0:
                damage_str += f"-{n3}"
        
        n += n5
        n2 += n5
        
        # Add standard effect if enabled
        if self.uses_standard_effect():
            if self.does_body:
                damage_str += f" (standard effect: {n}"
                if n != n2:
                    damage_str += f" / {n2}"
                damage_str += f" BODY, {n * stun_multiplier}"
                if n != n2:
                    damage_str += f" / {n2 * stun_multiplier}"
                damage_str += " STUN)"
            else:
                damage_str += f" (standard effect: {n * stun_multiplier}"
                if n != n2:
                    damage_str += f" / {n2 * stun_multiplier}"
                damage_str += " STUN)"
        
        return damage_str
    
    @property
    def all_assigned_modifiers(self):
        """Get all assigned modifiers (stub)."""
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
    

