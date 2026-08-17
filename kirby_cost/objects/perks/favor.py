"""
Favor Perk for kirby-cost.

Converted from com.hero.objects.perks.Favor.java

Favor represents favors owed to the character.
"""

from typing import Optional, List
from kirby_cost.objects.perks.perk import Perk
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.modifier import Modifier
# Enhancer not yet converted - will be handled when needed
# from kirby_cost.objects.enhancers.enhancer import Enhancer
from kirby_cost.core.context import EngineContext
from kirby_cost.util.rounder import round_half_down, round_half_up


class Favor(Perk, xmlid="FAVOR"):
    """
    Favor Perk.
    
    Represents favors owed to the character.
    """
    
    def __init__(self, element=None):
        """Initialize a Favor perk."""
        super().__init__(element, self.XMLID)
    
    @property
    def real_cost_pre_list(self) -> float:
        """
        Calculate real cost before list modifiers.
        
        This includes special handling for enhancers and multipliers.
        
        Returns:
            Real cost value
        """
        self.enhancer_applied = None
        active_cost = self.active_cost
        has_limitations = False
        limitation_total = 0.0
        
        # Sum up limitation values
        for mod in self._assigned_modifiers:
            if mod.total_value < 0.0:
                limitation_total += mod.total_value
                has_limitations = True
        
        # Check parent list for limitations
        parent_list = self._parent
        if parent_list:
            parent_mods = parent_list.assigned_modifiers
            for mod in parent_mods:
                # Skip VPP modifiers, Charges in Multipower, or already assigned
                if (mod.types and "VPP" in mod.types):
                    continue
                if (mod.xmlid == "CHARGES" and 
                    hasattr(parent_list, '__class__') and 
                    parent_list.__class__.__name__ == "Multipower"):
                    continue
                if GenericObject.find_object_by_id(self._assigned_modifiers, mod.xmlid):
                    continue
                if mod.xmlid in ["GENERIC_OBJECT", "CUSTOM_MODIFIER"]:
                    continue
                
                if mod.total_value < 0.0:
                    limitation_total += mod.total_value
                    has_limitations = True
        
        # Apply limitations
        real_cost = active_cost / (1.0 + abs(limitation_total))
        if has_limitations:
            real_cost = round_half_down(real_cost)
        
        # Apply enhancers if types match
        # TODO: Implement enhancer support when Enhancer class is converted
        # if self.get_types() and len(self.get_types()) > 0:
        #     active_hero = EngineContext.get_active_hero()
        #     if active_hero:
        #         # Check skills for enhancers
        #         for skill in active_hero.get_skills():
        #             if isinstance(skill, Enhancer):
        #                 enhancer = skill
        #                 for perk_type in self.get_types():
        #                     if enhancer.applies_to_type(perk_type):
        #                         self.enhancer_applied = enhancer
        #                         if self not in enhancer.get_objects():
        #                             enhancer.get_objects().append(self)
        #                         
        #                         if real_cost > enhancer.get_cost_savings():
        #                             real_cost -= enhancer.get_cost_savings()
        #                             break
        #                         elif real_cost > 0.0:
        #                             real_cost /= 2.0
        #                             break
        #         
        #         # Check perks for enhancers
        #         for perk in active_hero.get_perks():
        #             if isinstance(perk, Enhancer):
        #                 enhancer = perk
        #                 for perk_type in self.get_types():
        #                     if enhancer.applies_to_type(perk_type):
        #                         self.enhancer_applied = enhancer
        #                         if real_cost > enhancer.get_cost_savings():
        #                             real_cost -= enhancer.get_cost_savings()
        #                             break
        #                         elif real_cost > 0.0:
        #                             real_cost /= 2.0
        #                             break
        
        # Apply multiplier
        active_hero = EngineContext.active_hero()
        if active_hero and active_hero.rules.multiplier_allowed:
            if self.multiplier != 1.0:
                real_cost *= self.multiplier
                real_cost = round_half_down(real_cost)
            elif parent_list and parent_list.multiplier != 1.0:
                real_cost *= parent_list.multiplier
                real_cost = round_half_down(real_cost)
        
        # Apply quantity modifier
        if self._quantity > 1:
            quantity = self._quantity
            multiplier_count = 0
            while quantity > 1.0:
                quantity /= 2.0
                multiplier_count += 1
            real_cost += multiplier_count * 5
        
        return real_cost

