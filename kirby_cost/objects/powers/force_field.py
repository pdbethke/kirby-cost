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
        
        # Check for Flash Defense adder
        for adder in self.assigned_adders:
            if adder.xmlid == "FLASHDEFENSE":
                if not first:
                    output += "/"
                output += f"{adder.levels} Flash Defense"
                break
        
        output += ")"
        
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
    
    @property
    def adder_string(self) -> str:
        """Get adder string (excluding Flash Defense)."""
        adders = []
        for adder in self.assigned_adders:
            if adder.xmlid != "FLASHDEFENSE":
                if adder.display_in_string:
                    adders.append(adder.alias)
        return ", ".join(adders)
    
    @property
    def modifier_string(self) -> str:
        """Get modifier string (stub)."""
        return ""

