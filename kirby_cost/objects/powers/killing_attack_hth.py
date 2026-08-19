"""
Hand-to-Hand Killing Attack power class for kirby-cost.

Converted from com.hero.objects.powers.KillingAttackHTH.java

HKA is a melee attack that does BODY damage.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_down

#: Java's Constants.STR — hero.characteristic() keys on this ordinal.
_STR = 1


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

        n2, n3, n7, n8 = self._add_strength(n, n4, n2, n3, n7, n8)
        
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

        # HD shows the STR-added damage only when STR actually changes it, or
        # when the primary and secondary figures disagree with each other.
        if n2 != n - n4 or (n2 != n3 and n3 != n - n4):
            damage_str += " (" + self._dice(n2, n4)
            if n2 != n3:
                damage_str += " / " + self._dice(n3, n4, tight=True)
            damage_str += " w/STR)"

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
    
    

    def _dice(self, pips: int, minus: int, *, tight: bool = False) -> str:
        """Pips as HD writes them inside the w/STR bracket.

        Not the same renderer as the headline damage: a remainder of two pips
        prints "1/2d6" normally but "d6 - 1" once a MINUSONEPIP adder is in
        play, because the attack is then being counted down from the next die
        rather than up from the last one. HD spaces that subtraction one way
        for the primary figure and another for the secondary — "d6 - 1" and
        "d6-1" — which is not a rule, just what the two branches say.
        """
        dice, rem = pips // 3, pips % 3
        if rem == 1:
            return f"{dice if dice else ''}d6+1"
        if rem == 2:
            if minus == 0:
                return f"{str(dice) + ' ' if dice else ''}1/2d6"
            gap = "-" if tight else " - "
            return f"{dice + 1 if dice else ''}d6{gap}1"
        return f"{dice if dice else ''}d6"

    def _add_strength(self, dc: int, minus: int, str_dc: int, str_dc2: int,
                      std: int, std2: int) -> tuple[int, int, int, int]:
        """STR adds to a Killing Attack, and HD prints the total.

        Ported from ``KillingAttackHTH.getDamageDisplay`` (the STR half). It
        was a stub reading "For now, skip STR bonus calculation", so an HKA
        printed its bought dice and nothing else — HD prints
        "1d6 (3d6 w/STR)".

        Three things switch it off, and they are not the same thing:
        NOSTRBONUS says the attack never adds STR; a STR MINIMUM with a
        CANNOTADD adder says the same; and a STR MINIMUM whose option cannot
        be read as a number ALSO says the same, because HD catches the parse
        failure and treats an unreadable minimum as no bonus at all.

        The advantage total raises the cost of a damage class, so an
        advantaged attack gets less out of the same STR. Reduced Endurance is
        excluded from that sum — it buys endurance, not effect.
        """
        from kirby_cost.objects.base import GenericObject
        from kirby_cost.util.rounder import round_down

        mods = self.all_assigned_modifiers
        no_str = GenericObject.find_object_by_id(mods, "NOSTRBONUS") is not None
        min_strength = 0

        str_min = GenericObject.find_object_by_id(mods, "STRMINIMUM")
        if str_min is not None:
            if GenericObject.find_object_by_id(
                    str_min.assigned_adders, "CANNOTADD") is not None:
                no_str = True
            elif str_min.selected_option is not None:
                try:
                    min_strength = int(str_min.selected_option.alias)
                except (TypeError, ValueError):
                    no_str = True
            else:
                no_str = True

        if no_str:
            return str_dc, str_dc2, std, std2

        hero = _active_hero()
        if hero is None:
            return str_dc, str_dc2, std, std2
        strength = hero.characteristic(_STR)
        if strength is None:
            return str_dc, str_dc2, std, std2

        adv = 1.0
        for mod in mods:
            if mod.total_value > 0 and mod.xmlid != "REDUCEDEND":
                adv += mod.total_value
        str_per_dc = 5 * adv

        primary = max(0.0, strength.get_primary_value(hero) - min_strength)
        secondary = max(0.0, strength.get_secondary_value(hero) - min_strength)
        sixth = _is_6e(hero)

        # The `else` arms are 5E: before 6E an attack could not more than
        # double its dice from STR. Every template in this corpus is 6E, so
        # they are here for faithfulness rather than for coverage.
        if primary / str_per_dc < dc - minus or sixth:
            str_dc += round_down(primary / str_per_dc)
        else:
            str_dc = (dc - minus) * 2
        if primary / str_per_dc < std or sixth:
            std = int(std + primary / str_per_dc)
        else:
            std = std * 2
        if secondary / str_per_dc < dc - minus or sixth:
            str_dc2 = int(str_dc2 + secondary / str_per_dc)
        else:
            str_dc2 = (dc - minus) * 2
        if secondary / str_per_dc < std2 or sixth:
            std2 = int(std2 + secondary / str_per_dc)
        else:
            std2 = std2 * 2
        return str_dc, str_dc2, std, std2

    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = f"{self._alias} {self.damage_display}"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        if self.input and self.input.strip() and not _use_wg():
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
    



def _use_wg() -> bool:
    """HD's 6E display preference. Java reads it inline as
    `HeroDesigner.getInstance().getPrefs().useWG()`; when it is on, the
    "(vs. ED)" defence note is not printed."""
    try:
        from kirby_cost.core.context import EngineContext
        return bool(EngineContext.prefs().use_wg)
    except Exception:  # noqa: BLE001
        return True


def _is_6e(hero) -> bool:
    """Java ``Template.is6E()``: the template's id contains "6E", or one of
    its parents' does. Main6E, Vehicle6E, Automaton6E and Computer6E all name
    themselves so, and the specialised ones extend Main6E, so the parent walk
    never changes the answer for this corpus. A character that declares no
    template at all is costed against the Main6E bootstrap, which is 6E — so
    an unknown template answers True rather than False.
    """
    tid = getattr(hero, "original_template_id", None) or "Main6E"
    return "6E" in tid


def _active_hero():
    """The character whose STR is added to this attack."""
    try:
        from kirby_cost.core.context import EngineContext
        return EngineContext.active_hero()
    except Exception:  # noqa: BLE001
        return None
