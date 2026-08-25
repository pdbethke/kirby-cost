"""
Force Field power class for kirby-cost.

Converted from com.hero.objects.powers.ForceField.java

Force Field provides non-resistant defense.
"""

import math
from kirby_cost.objects.powers.power import Power
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.rounder import round_half_down
from kirby_cost.engine.xml_attrs import XMLAttr


class ForceField(Power, xmlid="FORCEFIELD"):
    """
    Force Field power.
    
    Provides non-resistant defense (PD, ED, Mental Defense, Power Defense).
    """
    
    #: HD costs Resistant Protection by the PD/ED split, not by LEVELS alone.
    #: Nothing in the engine read these — the fields existed and stayed 0 —
    #: so a re-exported character lost the whole power: 42 points to 0, in a
    #: file that opened cleanly.
    XML_ATTRS = (
        XMLAttr("PDLEVELS", "pd_levels", "int"),
        XMLAttr("EDLEVELS", "ed_levels", "int"),
        XMLAttr("MDLEVELS", "md_levels", "int"),
        XMLAttr("POWDLEVELS", "powd_levels", "int"),
    )

    def __init__(self):
        """Initialize a Force Field power."""
        super().__init__()
        self.xmlid = ForceField.XMLID
        self._duration = "CONSTANT"
        self.can_affect_primary = True
        # ForceField.java:274-277 overrides resistantDefenses() -> true. In 6E
        # this power IS "Resistant Protection", so every point of it is
        # resistant. Power.__init__ defaults the flag False and nothing here
        # raised it, so DefenseCharacteristic.calc_resistant_total skipped the
        # power entirely: Bokor's r_pd read 0 where HD says 10. Armor already
        # sets this.
        self.resistant_defenses = True
        self.pd_levels: int = 0
        self.ed_levels: int = 0
        self.md_levels: int = 0
        self.powd_levels: int = 0
    
    @property
    def total_cost(self) -> float:
        """
        Calculate total cost for Force Field.

        FLASHDEFENSE adder levels are counted as extra levels in the
        base level calculation, then excluded from the adder cost loops.

        Ported from ForceField.java getTotalCost().
        """
        d = self.base_cost
        available_adders = self.available_adders

        if self._level_value != 0.0:
            # Add FLASHDEFENSE levels to total level count
            n = self._levels
            for adder in self.assigned_adders:
                if adder.xmlid == "FLASHDEFENSE":
                    n += adder.levels

            d2 = math.floor(float(n) / self._level_value)
            if float(n) % self._level_value != 0.0 and self._level_value > 1.0:
                d2 += 1.0
            d += d2 * self._level_cost

            if self._level_cost < self._level_value:
                d = 1.0 if (d > 0.0 and d < 1.0) else round_half_down(d)

        # Required adders (skip FLASHDEFENSE — already counted in levels)
        for adder in self.assigned_adders:
            if not adder.is_required:
                continue
            if adder.xmlid == "FLASHDEFENSE":
                continue
            d += adder.real_cost

        # Available adders (skip FLASHDEFENSE)
        for adder in self.assigned_adders:
            if adder.is_required:
                continue
            if adder.xmlid == "FLASHDEFENSE":
                continue
            if not GenericObject.find_object_by_id(available_adders, adder.xmlid):
                continue
            d += adder.real_cost

        # Min/max clamp
        if d < self._minimum_cost and self.min_set:
            d = self._minimum_cost
        elif d > self._max_cost and self.max_set:
            d = self._max_cost

        # Custom adders (skip FLASHDEFENSE)
        for adder in self.assigned_adders:
            if adder.is_required:
                continue
            if adder.xmlid == "FLASHDEFENSE":
                continue
            if GenericObject.find_object_by_id(available_adders, adder.xmlid):
                continue
            d += adder.real_cost

        # Automaton defense multiplier — ForceField has DEFENSE type, so
        # when the character has Automaton (Takes No STUN), cost is multiplied.
        if "DEFENSE" in self.types:
            hero = getattr(self, '_loaded_hero', None)
            if hero is not None:
                from kirby_cost.objects.powers.automaton import Automaton
                for p in getattr(hero, 'powers', []):
                    if isinstance(p, Automaton):
                        option_id = getattr(p, 'option_id', '')
                        if option_id and option_id.upper().startswith("NOSTUN"):
                            d *= p.defense_cost_multiplier
                        break

        return d

    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Force Field)."""
        return ""
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output with defense values."""
        output = f"{self._alias} {self.damage_display}"
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Add defense values
        output += "("
        first = True
        if self.pd_levels > 0:
            output += f"{self.pd_levels} PD"
            first = False
        if self.ed_levels > 0:
            if not first:
                output += "/"
            output += f"{self.ed_levels} ED"
            first = False
        if self.md_levels > 0:
            if not first:
                output += "/"
            output += f"{self.md_levels} Mental Defense"
            first = False
        if self.powd_levels > 0:
            if not first:
                output += "/"
            output += f"{self.powd_levels} Power Defense"
            first = False
        
        # Flash Defense names the SENSE it protects, and that belongs inside
        # the defence list rather than trailing after it: HD writes
        # "8 Flash Defense:  Sight Group", not "8 Flash Defense) (Flash
        # Defense Sight Group:  +8)". Java also removes the adder from the
        # list before building the adder string, so it is stated once.
        from kirby_cost.objects.base import option_alias as _opt
        flash = [a for a in self._assigned_adders if a.xmlid == "FLASHDEFENSE"]
        for adder in flash:
            if not first:
                output += "/"
            output += f"{adder.levels} {adder.alias or ''}"
            sense = (_opt(adder) or "").strip()
            if sense:
                output += f":  {sense}"
            first = False

        output += ")"

        if self.input and self.input.strip():
            output += f":  {self.input}"

        original = self._assigned_adders
        self._assigned_adders = [a for a in original if a.xmlid != "FLASHDEFENSE"]
        try:
            adder_str = self.adder_string
        finally:
            self._assigned_adders = original

        if self._selected_option:
            output += f" ({self._selected_option.alias}"
            if adder_str and adder_str.strip():
                output += f"; {adder_str}"
            output += ")"
        else:
            if adder_str and adder_str.strip():
                output += f" ({adder_str})"
        
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    
    

    # ── Characteristic contribution ────────────────────────────────────
    #
    # ForceField.java:161-253 overrides getPdIncrease/getEdIncrease and their
    # *IncreaseLevels. Without them this power contributes NOTHING to the
    # PD/ED characteristic totals: DefenseCharacteristic._calc_primary_value
    # reaches a power through increase()/increase_levels(), and the base
    # class answers 0. Bokor's Resistant Protection (10 PD/10 ED) left his
    # PD reading 2 instead of 12.
    #
    # Overriding the DISPATCH rather than declaring `pd_increase` properties:
    # CharAffectingObject.__init__ assigns `self.pd_increase = 0.0` as a plain
    # attribute, so a read-only property on the subclass breaks construction.
    #
    # The levels figure is `self.levels` -- the COMBINED PD+ED levels -- not
    # pd_levels, matching getPdIncreaseLevels() -> getLevels(). increase_value
    # scales increase/increase_levels by levels, so 10/20 * 20 = 10.

    def increase(self, char_type: int) -> float:
        from kirby_cost.util.constants import CharacteristicType
        if char_type == CharacteristicType.PD:
            return float(self.pd_levels)
        if char_type == CharacteristicType.ED:
            return float(self.ed_levels)
        return super().increase(char_type)

    def increase_levels(self, char_type: int) -> int:
        from kirby_cost.util.constants import CharacteristicType
        if char_type in (CharacteristicType.PD, CharacteristicType.ED):
            return self.levels
        return super().increase_levels(char_type)
