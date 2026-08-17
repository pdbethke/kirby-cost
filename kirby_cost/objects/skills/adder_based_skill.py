"""
Adder-based skill cost for kirby-cost.

Skills where cost = base (familiarity/proficiency/3) + adder costs,
with special first-adder handling for familiarity/proficiency.

Used by: Survival, Navigation, AnimalHandler, Gambling, Weaponsmith,
TransportFamiliarity, Forgery.

Ported from Survival.java -- same cost pattern shared by all the above
Java classes (Navigation.java, AnimalHandler.java, Gambling.java, etc.).
"""

from typing import Optional, TYPE_CHECKING
from kirby_cost.objects.skills.skill import Skill
from kirby_cost.objects.base import GenericObject

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero


class AdderBasedSkill(Skill, xmlid="SURVIVAL"):
    """Skill whose cost derives from adders rather than a flat base.

    Registered for SURVIVAL — this class is the direct port of Java
    Survival.java (the other Java siblings differ slightly and are
    registered via NCounterSkill and its subclasses).
    """

    def __init__(self, xmlid: str = "SURVIVAL"):
        super().__init__(xmlid)

    def _init(self, element) -> None:
        """Initialize from XML element.

        Adder-based skills default to familiarity=True when the XML doesn't
        explicitly set it (mirrors Java includeFamiliarity() returning true).
        """
        super()._init(element)
        if element is None:
            return
        # If FAMILIARITY was not explicitly set in the XML, default to True
        # (Java Skill.init() checks includeFamiliarity() which returns true
        # for all adder-based skills)
        fam_str = element.get("FAMILIARITY", "")
        if not fam_str or not fam_str.strip():
            self.set_familiarity(True)

    @property
    def total_cost(self) -> float:
        """Adder-based cost calculation.

        1. Base = familiarity(1) / proficiency(profCost) / levelsOnly(0) / 3
        2. + level costs (with skill maxima)
        3. + positive adders (familiarity/proficiency get minimum cost)
        4. Clamp to min/max
        5. + negative adders
        6. - enhancer savings
        """
        active_hero = self._get_active_hero()
        self.enhancer_applied = None

        d = self.base_cost
        if self.is_everyman:
            return 0.0

        # Determine if we have real (non-custom) adders
        all_custom = all(a.custom for a in self.assigned_adders)
        if len(self.assigned_adders) == 0 or all_custom:
            if self.is_familiarity:
                d = 1.0
            elif self.is_proficiency:
                d = float(self.proficiency_cost)
            elif self.levels_only:
                d = 0.0
            else:
                d = 3.0

        # Level cost
        if self._level_value != 0.0:
            d += float(self._levels) / self._level_value * self._level_cost

            # Skill maxima
            if (self._levels > 0
                    and active_hero is not None
                    and active_hero.rules.use_skill_maxima
                    and self.roll_based):
                maxima_limit = active_hero.rules.skill_maxima_limit
                roll_value = self.roll_value
                secondary = self.secondary_roll_value
                if secondary > roll_value:
                    roll_value = secondary
                if roll_value > maxima_limit:
                    excess = min(roll_value - maxima_limit, self._levels)
                    d += float(excess) / self._level_value * self._level_cost

        # Positive adders (special handling for familiarity/proficiency)
        for adder in self.assigned_adders:
            if adder.real_cost <= 0.0:
                continue
            if adder.custom:
                d += adder.real_cost
                continue
            if not (self.is_familiarity or self.is_everyman or self.is_proficiency):
                d += adder.real_cost
                continue
            # Familiarity/proficiency: use minimum of adder cost vs minimum_cost
            if adder.minimum_cost < adder.real_cost:
                d += adder.minimum_cost
            else:
                d += adder.real_cost

        # Min/max clamp
        if (d < self._minimum_cost
                and self.min_set
                and not self.is_everyman
                and not self.levels_only):
            d = self._minimum_cost
        elif d > self._max_cost and self.max_set:
            d = self._max_cost

        # Negative adders
        for adder in self.assigned_adders:
            if adder.real_cost >= 0.0:
                continue
            d += adder.real_cost

        # Enhancer savings
        if (self.types is not None
                and len(self.types) > 0
                and not self.levels_only
                and active_hero is not None):
            for skill in active_hero.skills:
                if hasattr(skill, 'applies_to_type') and hasattr(skill, 'cost_savings'):
                    for skill_type in self.types:
                        if not skill.applies_to_type(skill_type):
                            continue
                        self.enhancer_applied = skill
                        if d > float(skill.get_cost_savings()):
                            d -= float(skill.get_cost_savings())
                            return d
                        if d > 0.0:
                            d = 1.0
                        return d

        return d

    def include_familiarity(self) -> bool:
        return True


# Backward compatibility alias
Survival = AdderBasedSkill
