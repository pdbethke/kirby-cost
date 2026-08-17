"""
CostMixin — HERO System cost chain: base -> total -> active -> real.

Extracted from GenericObject to separate cost logic from object management.
All methods access attributes/methods on self via duck typing (MRO resolution).
"""

import math
from typing import Optional, List, TYPE_CHECKING

from kirby_cost.util.rounder import round_half_down, round_half_up

# Framework predicates are lazy-imported inside the methods that use them:
# cost.py is pulled in by base.py, and the framework classes live in
# subclasses of the base. Importing at module load time creates a circular
# import chain: base -> cost -> frameworks -> multipower -> list -> base.
# By the time these methods run, the full module graph is populated and the
# import is free.

if TYPE_CHECKING:
    from kirby_cost.objects.base import GenericObject
    from kirby_cost.objects.frameworks import (  # noqa: F401
        is_multipower, is_elemental_control,
    )
    from kirby_cost.objects.modifiers.linked import is_linked  # noqa: F401

# Enhancer definitions: maps enhancer XMLID to (applicable_types, cost_savings).
ENHANCER_DEFS: dict[str, tuple[list[str], int]] = {
    "SCHOLAR":             (["KNOWLEDGE"], 1),
    "SCIENTIST":           (["SCIENCE"], 1),
    "JACK_OF_ALL_TRADES":  (["PROFESSIONAL"], 1),
    "LINGUIST":            (["LANGUAGE"], 1),
    "TRAVELER":            (["AREA"], 1),
    "WELL_CONNECTED":      (["CONTACT"], 1),
}


class CostMixin:
    """HERO System cost chain: base -> total -> active -> real.

    Mixed into GenericObject. Relies on these attributes/methods from the host:
    - get_base_cost(), get_levels(), get_level_cost(), get_level_value()
    - get_assigned_modifiers(), get_assigned_adders(), get_available_adders()
    - get_types(), get_minimum_cost(), get_max_cost()
    - minimum_cost, min_set, max_cost, max_set, xmlid, levels, parent, main_power,
      assigned_modifiers, quantity, uses_end, enhancer_applied, _loaded_hero
    - find_object_by_id() (static)
    """

    @property
    def total_cost(self) -> float:
        """
        Calculate the total cost (base cost + level cost + adder costs).

        Formula: Base Cost + Level Cost + Adder Costs
        With minimum/maximum cost limits and Automaton Defense multiplier.
        """
        from kirby_cost.objects.base import GenericObject

        total = self.base_cost
        available_adders = self.available_adders

        # Calculate level cost (use polymorphic methods)
        levels = self.levels
        level_cost = self.level_cost
        level_value = self.level_value
        if level_value != 0.0:
            level_units = math.floor(levels / level_value)
            if (levels % level_value != 0.0 and level_value > 1.0):
                level_units += 1.0
            total += level_units * level_cost
            if level_cost < level_value:
                if total > 0.0 and total < 1.0:
                    total = 1.0
                else:
                    total = round_half_down(total)

        # Add required adders
        for adder in self.assigned_adders:
            if adder.is_required:
                total += adder.real_cost

        # Add available adders that are assigned
        for adder in self.assigned_adders:
            if (not adder.is_required and
                    GenericObject.find_object_by_id(available_adders, adder.xmlid)):
                total += adder.real_cost

        # Apply minimum/maximum cost limits
        if total < self._minimum_cost and self.min_set:
            total = self._minimum_cost
        elif total > self._max_cost and self.max_set:
            total = self._max_cost

        # Add other adders (not required, not in available list)
        for adder in self.assigned_adders:
            if (not adder.is_required and
                    not GenericObject.find_object_by_id(available_adders, adder.xmlid)):
                total += adder.real_cost

        # Automaton Defense cost multiplier
        if "DEFENSE" in self.types:
            hero = getattr(self, '_loaded_hero', None)
            if hero is not None:
                from kirby_cost.objects.powers.automaton import Automaton
                for p in getattr(hero, 'powers', []):
                    if isinstance(p, Automaton):
                        option_id = getattr(p, 'option_id', '')
                        if option_id and option_id.upper().startswith("NOSTUN"):
                            total *= p.defense_cost_multiplier
                        break

        return total

    @property
    def active_cost(self) -> float:
        """Calculate the active cost (total cost with advantages)."""
        return self._compute_active_cost()

    def _compute_active_cost(self, exclude_xmlid: Optional[str] = None) -> float:
        """Active Cost = Total Cost x (1 + Sum of Advantage Values)."""
        from kirby_cost.objects.base import GenericObject
        from kirby_cost.objects.frameworks import (
            is_multipower, is_elemental_control,
        )
        from kirby_cost.objects.modifiers.linked import is_linked

        total_cost = self.total_cost
        modifier_sum = 0.0
        has_advantages = False

        for modifier in self.assigned_modifiers:
            modifier.parent = self
            if exclude_xmlid and modifier.xmlid == exclude_xmlid:
                continue
            if modifier.total_value > 0.0:
                modifier_sum += modifier.total_value
                has_advantages = True

        parent = self._parent
        if self.main_power:
            parent = self.main_power.parent

        if parent:
            for modifier in parent.assigned_modifiers:
                if modifier.types and "VPP" in modifier.types:
                    continue
                if modifier.xmlid == "CHARGES" and is_multipower(parent):
                    continue
                if is_linked(modifier):
                    continue
                if modifier.total_value <= 0.0:
                    continue
                if (GenericObject.find_object_by_id(self._assigned_modifiers, modifier.xmlid) and
                        modifier.xmlid not in ("GENERIC_OBJECT", "CUSTOM_MODIFIER", "MODIFIER")):
                    continue
                if is_multipower(parent) or is_elemental_control(parent):
                    continue
                if exclude_xmlid and modifier.xmlid == exclude_xmlid:
                    continue
                modifier_sum += modifier.total_value
                has_advantages = True

        active_cost = total_cost * (1.0 + modifier_sum)
        if has_advantages:
            active_cost = round_half_down(active_cost)
            if total_cost > 0.0 and active_cost < 1.0:
                active_cost = 1.0
        return active_cost

    @property
    def real_cost(self) -> float:
        """Real Cost = Active Cost / (1 + |Limitations|) - Enhancer Savings."""
        if self._parent:
            return self._parent.real_cost_for_child(self)
        return self.real_cost_pre_list

    @property
    def real_cost_pre_list(self) -> float:
        """Calculate real cost before parent list adjustments."""
        from kirby_cost.objects.base import GenericObject
        from kirby_cost.objects.frameworks import is_multipower, is_vpp

        self.enhancer_applied = None
        active_cost = self.active_cost
        limitation_sum = 0.0
        has_limitations = False

        # Check if enhancer should be applied
        should_check_enhancer = False
        if self._is_mental_awareness():
            should_check_enhancer = True
        elif self._is_transport_familiarity():
            should_check_enhancer = len(self.assigned_adders) > 0
        elif self._is_weapon_familiarity():
            should_check_enhancer = True
        elif self._is_weapon_element():
            should_check_enhancer = True

        # Add assigned limitations
        for modifier in self.assigned_modifiers:
            if modifier.total_value < 0.0:
                limitation_sum += modifier.total_value
                has_limitations = True

        # Check for enhancer trigger
        if not should_check_enhancer:
            available_adders = self.available_adders
            for adder in self.assigned_adders:
                found_in_available = GenericObject.find_object_by_id(
                    available_adders, adder.xmlid)
                is_generic = adder.xmlid.upper() == "GENERIC_OBJECT"
                if ((not found_in_available or is_generic) and
                        adder.total_cost <= 0.0):
                    should_check_enhancer = True
                    break

        # Add parent list limitations
        parent = self._parent
        if self.main_power:
            parent = self.main_power.parent

        # Skip parent-list limitations if the parent IS a Variable Power Pool
        # (VPP children don't inherit the pool's limitations the way Multipower
        # slots do — they share the pool's active point cap instead). The
        # modifier.types "VPP" check below is separate: those are limitation
        # tags that mark mods as VPP-only, filtered regardless of parent type.
        if parent and not is_vpp(parent):
            for modifier in parent.assigned_modifiers:
                if modifier.types and "VPP" in modifier.types:
                    continue
                if modifier.xmlid == "CHARGES" and is_multipower(self._parent):
                    continue
                if modifier.total_value >= 0.0:
                    continue
                if (GenericObject.find_object_by_id(self._assigned_modifiers, modifier.xmlid) and
                        modifier.xmlid not in ("GENERIC_OBJECT", "CUSTOM_MODIFIER", "MODIFIER")):
                    continue
                limitation_sum += modifier.total_value
                has_limitations = True

        # Calculate real cost with limitations
        real_cost = active_cost / (1.0 + abs(limitation_sum))
        if has_limitations:
            real_cost = round_half_down(real_cost)

        # Apply enhancer savings.
        real_cost = self._apply_enhancer_savings(real_cost)

        # Minimum real cost
        if (real_cost < 1.0 and
                (active_cost > 0.0 or
                 (self._levels > 0 and len(self.assigned_adders) == 0 and
                  self.base_cost >= 0.0)) and
                not should_check_enhancer):
            real_cost = 1.0
        if real_cost < 1.0 and not should_check_enhancer:
            real_cost = 1.0

        # Quantity cost (5 points per doubling)
        if self._quantity > 1:
            quantity_cost = 0
            qty = float(self._quantity)
            while qty > 1.0:
                quantity_cost += 5
                qty /= 2.0
            real_cost += float(quantity_cost)

        return real_cost

    def _apply_enhancer_savings(self, real_cost: float) -> float:
        """Apply cost savings from a matching Enhancer on the active hero.

        Enhancers are skills/perks like Scholar (KNOWLEDGE -1 pt),
        Linguist (LANGUAGE -1 pt), Traveler (AREA -1 pt), etc. — see
        ``ENHANCER_DEFS`` at the top of this module for the full table.
        For each non-enhancer object with one or more type tags, we scan
        the hero's skills and perks for an enhancer whose applicable
        types intersect this object's types. The first match reduces
        ``real_cost`` by the enhancer's savings (clamped so it never
        drops below 1.0 if the original was positive).

        Returns the (possibly reduced) real cost. Also sets
        ``self.enhancer_applied`` to the matching enhancer object for
        reporting purposes, or leaves it unchanged if no match.

        Called from ``real_cost_pre_list``; extracted so the cost chain
        reads as "limitations -> enhancer -> minimum -> quantity" at
        top level instead of a 30-line nested loop.
        """
        obj_types = self.types
        if not obj_types:
            return real_cost

        # Enhancer skills/perks themselves don't get enhancer discounts.
        if self.xmlid in ENHANCER_DEFS:
            return real_cost

        hero = getattr(self, '_loaded_hero', None)
        if hero is None:
            return real_cost

        # "Skill levels only" skills don't benefit from enhancers — they
        # already price at the level cost, not the base skill cost.
        try:
            from kirby_cost.objects.skills.skill import Skill as SkillClass
            if isinstance(self, SkillClass) and self.levels_only:
                return real_cost
        except ImportError:
            pass

        enhancer = self._find_matching_enhancer(hero, obj_types)
        if enhancer is None:
            return real_cost

        self.enhancer_applied = enhancer[0]
        savings = float(enhancer[1])
        if real_cost > savings:
            return real_cost - savings
        if real_cost > 0.0:
            return 1.0
        return real_cost

    def _find_matching_enhancer(self, hero, obj_types):
        """Search the hero's skills and perks for the first enhancer whose
        applicable-types list intersects ``obj_types``.

        Returns ``(enhancer_obj, savings)`` or ``None``. Search order is
        skills first, then perks — matching HD's original behaviour.
        """
        for search_list in (getattr(hero, 'skills', []),
                            getattr(hero, 'perks', [])):
            for enh_obj in search_list:
                enh_def = ENHANCER_DEFS.get(enh_obj.xmlid)
                if enh_def is None:
                    continue
                enh_types, enh_savings = enh_def
                for t in obj_types:
                    if t in enh_types:
                        return (enh_obj, enh_savings)
        return None

    def _is_mental_awareness(self) -> bool:
        return False

    def _is_transport_familiarity(self) -> bool:
        return False

    def _is_weapon_familiarity(self) -> bool:
        return False

    def _is_weapon_element(self) -> bool:
        return False

    def ap_per_end(self, active_hero: Optional[object] = None) -> int:
        """Get Active Points per END cost (default 10 for 6E)."""
        n = 10
        if active_hero is not None and hasattr(active_hero, 'rules') and active_hero.rules is not None:
            n = active_hero.rules.ap_per_end
            if self.xmlid == "STR":
                n = active_hero.rules.str_ap_per_end
        if not self.uses_end:
            return 0
        return n

    def orig_ap_per_end(self, active_hero: Optional[object] = None) -> int:
        """Get original AP per END (before modifiers)."""
        n = 10
        if active_hero is not None and hasattr(active_hero, 'rules') and active_hero.rules is not None:
            n = active_hero.rules.ap_per_end
            if self.xmlid == "STR":
                n = active_hero.rules.str_ap_per_end
        if not self.uses_end:
            n = 0
        return n
