"""
AreaEffect modifier for kirby-cost.

Converted from com.hero.objects.modifiers.AreaEffect.java

AreaEffect modifier with custom getArea() and getLevelInfo() methods.
Calculates area description based on levels and power cost.
"""

import math
from typing import Optional
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.rounder import round_half_up


class AreaEffect(Modifier, xmlid="AOE"):
    """
    AreaEffect modifier.
    
    Power affects an area.
    
    Has custom area calculation and formatting based on levels and power cost.
    """
    
    def __init__(self, element=None):
        """Initialize a AreaEffect modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def level_info(self) -> str:
        """Get level info string (area description)."""
        return self.area(None)
    
    def area(self, generic_object: Optional[GenericObject]) -> str:
        """
        Get area description string.
        
        Args:
            generic_object: Optional parent object for calculations
            
        Returns:
            Area description string
        """
        # Note: Would need HeroDesigner.getActiveTemplate().is6E() check
        # For now, implement 6E version
        from kirby_cost.util.rounder import round_half_up
        import locale
        
        string = ""
        adder = self._selected_option
        if adder is None:
            return string
        
        # Format number with locale
        try:
            num_format = locale.format_string("%d", self._levels, grouping=True)
        except (ValueError, TypeError):
            num_format = str(self._levels)
        
        if adder.xmlid == "RADIUS":
            string = string + num_format + "m Radius"
        elif adder.xmlid == "CONE":
            string = string + num_format + "m Cone"
        elif adder.xmlid == "LINE":
            string = string + num_format + "m"
            
            # Check for DOUBLEHEIGHT
            double_height = GenericObject.find_object_by_id(
                self.assigned_adders, "DOUBLEHEIGHT")
            if double_height is not None:
                double_height.display_in_string = False
                self.multiplier = double_height.levels
                string = string + " Long, " + str(int(self.multiplier)) + "m Tall"
            
            # Check for DOUBLEWIDTH
            double_width = GenericObject.find_object_by_id(
                self.assigned_adders, "DOUBLEWIDTH")
            if double_width is not None:
                double_width.display_in_string = False
                self.multiplier = double_width.levels
                if double_height is not None:
                    string = string + ", " + str(int(self.multiplier)) + "m Wide"
                else:
                    string = string + " Long, 2m Tall, " + str(int(self.multiplier)) + "m Wide"
            elif double_height is not None:
                string = string + ", 2m Wide"
            
            string = string + " Line"
        elif adder.xmlid == "ANY":
            string = string + num_format + " 2m Areas"
        elif adder.xmlid == "SURFACE":
            string = string + num_format + "m Surface"
        
        # Check for EXPLOSION adder
        explosion_adder = GenericObject.find_object_by_id(
            self.assigned_adders, "EXPLOSION")
        if explosion_adder is not None:
            explosion_adder.display_in_string = False
            string = string + " Explosion"
        
        return string
    
    @property
    def total_value(self) -> float:
        """
        Get total value of this modifier (6E version).

        6E uses logarithmic calculations for DOUBLEHEIGHT, DOUBLEWIDTH, and MOBILE
        adders. 5E delegates to the base class.

        Ported from AreaEffect.java getTotalValue() lines 209-284.
        """
        # 6E custom logic (assume 6E — would need template check for 5E)
        d = self.base_cost

        # Recalculate DOUBLEHEIGHT/DOUBLEWIDTH adder costs in available list
        for adder in self.available_adders:
            xmlid = adder.xmlid
            if xmlid not in ("DOUBLEHEIGHT", "DOUBLEWIDTH"):
                continue
            adder.display_in_string = False
            lp = adder.level_power
            lm = adder.level_multiplier
            if lp > 0 and lm > 0:
                n = int(math.ceil(math.log(float(adder.levels) / float(lm)) / math.log(lp)))
                n -= 1
                if n < 1:
                    n = 1
                adder.base_cost = 0.0
                adder.base_cost = float(n) * adder.level_cost - adder.double_total()

        # Process assigned adders
        for adder in self.assigned_adders:
            xmlid = adder.xmlid
            if xmlid in ("DOUBLEHEIGHT", "DOUBLEWIDTH"):
                adder.display_in_string = False
                lp = adder.level_power
                lm = adder.level_multiplier
                if lp > 0 and lm > 0:
                    n = int(math.ceil(math.log(float(adder.levels) / float(lm)) / math.log(lp)))
                    n -= 1
                    if n < 1:
                        n = 1
                    d += float(n) * adder.level_cost
                    adder.base_cost = 0.0
                    adder.base_cost = float(n) * adder.level_cost - adder.double_total()
            elif xmlid == "MOBILE":
                lp = adder.level_power
                lm = adder.level_multiplier
                if lp > 0 and lm > 0:
                    n = int(math.ceil(math.log(float(adder.levels) / float(lm)) / math.log(lp)))
                    if n < 1:
                        n = 1
                    d += float(n) * adder.level_cost + adder.orig_base_cost
                    adder.base_cost = 0.0
                    adder.base_cost = adder.orig_base_cost + float(n) * adder.level_cost - adder.double_total()
            else:
                d += adder.double_total()

        # Calculate level cost using logarithmic formula
        lp = self.level_power
        lm = self.level_multiplier
        if lp > 0 and lm > 0:
            n2 = int(math.ceil(math.log(float(self._levels) / float(lm)) / math.log(lp)))
            if n2 < 1:
                n2 = 1
            # Special case: IMAGES power at level 1 gets 0 level cost
            progenitor = self.progenitor
            if progenitor is not None and progenitor.xmlid == "IMAGES" and self._levels == 1:
                n2 = 0
            d += float(n2) * self._level_cost

        # Apply advantages (positive modifiers)
        advantage_sum = 0.0
        for modifier in self.assigned_modifiers:
            if modifier.total_value > 0.0:
                advantage_sum += modifier.total_value
        d3 = d * (1.0 + advantage_sum)

        # Apply limitations (negative modifiers)
        limitation_sum = 0.0
        for modifier in self.assigned_modifiers:
            if modifier.total_value < 0.0:
                limitation_sum += abs(modifier.total_value)
        d = d3 / (1.0 + limitation_sum)

        # Round to quarter
        sign = 1
        if d < 0.0:
            sign = -1
        d = abs(d) * 4.0
        d = round_half_up(d)
        d = (d / 4.0) * sign

        # Apply min/max limits
        if d < self._minimum_cost and self.min_set:
            return self._minimum_cost
        if d > self._max_cost and self.max_set:
            return self._max_cost

        return d

    @property
    def selected_option(self) -> Optional['Adder']:
        """Get the selected option."""
        return self._selected_option

    @selected_option.setter
    def selected_option(self, adder) -> None:
        """
        Set selected option. When shape changes, remove shape-specific adders.

        Ported from AreaEffect.java setSelectedOption() lines 287-308.
        """
        # Check if same option re-selected
        same = (self._selected_option is not None and
                adder is not None and
                self._selected_option is adder)

        self._selected_option = adder

        if same:
            return

        # Remove shape-specific adders when shape changes
        for xmlid in ("DOUBLEAREA", "DOUBLELENGTH", "DOUBLEWIDTH", "DOUBLEHEIGHT"):
            found = GenericObject.find_object_by_id(self.assigned_adders, xmlid)
            if found is not None:
                self.assigned_adders.remove(found)

    def included(self, generic_object: GenericObject) -> str:
        """
        Check if this modifier can be applied to the given object.
        
        Args:
            generic_object: The object to check
            
        Returns:
            Empty string if allowed, error message if not
        """
        result = super().included(generic_object)
        if result and result.strip():
            return result
        
        if self.force_allow:
            return result
        
        # Can be applied to NakedModifier, LifeSupport, Absorption
        from kirby_cost.objects.powers.naked_modifier import NakedModifier
        from kirby_cost.objects.powers.life_support import LifeSupport
        from kirby_cost.objects.powers.absorption import Absorption
        
        if isinstance(generic_object, (NakedModifier, LifeSupport, Absorption)):
            return ""
        
        # Cannot be applied to Possession
        if generic_object.xmlid == "POSSESSION":
            return f"{self._display} cannot be applied to Possession."
        
        # Can be applied to Images in 6E
        # Note: Would need HeroDesigner.getActiveTemplate().is6E() check
        if generic_object.xmlid == "IMAGES":
            # Assume 6E for now
            return ""
        
        # Cannot be applied if already affects area (unless it's this modifier)
        target = generic_object.target
        if target == "HEX":
            if GenericObject.find_object_by_id(
                generic_object.assigned_modifiers, "AOE") is None:
                return f"{self._display} cannot be applied to Powers which already affect an area."
        
        # Can only be applied to Powers which are targeted on others
        if target not in ("DCV", "ECV", "OCV", "OMCV", "MCV", "DMCV"):
            if GenericObject.find_object_by_id(
                generic_object.assigned_modifiers, "AOE") is None:
                return f"{self._display} can only be applied to Powers which are targeted on others."
        
        # Cannot be applied with Explosion
        if GenericObject.find_object_by_id(
            generic_object.assigned_modifiers, "EXPLOSION") is not None:
            return f"{self._display} cannot be applied to abilities which already affect an area."
        
        return ""
