"""
AccumulatorSkill — consolidated accumulator-pattern skill.

Replaces: Electronics, ComputerProgramming, SystemsOperation.

Adder costs accumulate: first familiarity/proficiency adder gets minimum_cost,
all others pay full cost. If no adders selected, base_cost applies.
Minimum cost is 2.0 when adders are present.
"""

from typing import ClassVar, Optional, TYPE_CHECKING
from kirby_cost.objects.skills.skill import Skill

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero


class AccumulatorSkill(Skill, xmlid="ELECTRONICS"):
    """Skill where adders accumulate with first-adder familiarity discount.

    Used by: ELECTRONICS, COMPUTER_PROGRAMMING, SYSTEMS_OPERATION.
    """

    def __init__(self, xmlid: str = None):
        """Initialize AccumulatorSkill."""
        super().__init__(xmlid or self.XMLID)

    @property
    def minimum_cost(self) -> float:
        """Minimum cost: 2.0 when adders are present."""
        if self.is_everyman:
            return 0.0
        if self.is_familiarity:
            return float(self.familiarity_cost)
        if self.is_proficiency:
            return float(self.proficiency_cost)
        if self.levels_only:
            return 0.0
        if len(self.assigned_adders) > 0:
            return 2.0
        return self._minimum_cost

    @minimum_cost.setter
    def minimum_cost(self, value) -> None:
        self._minimum_cost = value

    @property
    def total_cost(self) -> float:
        """Get total cost using accumulator pattern."""
        active_hero = self._get_active_hero()
        self.enhancer_applied = None

        d = 0.0
        # Level cost
        if self._level_value != 0.0:
            d += float(self._levels) / self._level_value * self._level_cost

            # Skill maxima handling
            if (self._levels > 0
                    and active_hero is not None
                    and active_hero.rules.use_skill_maxima
                    and self.roll_based):
                maxima_limit = active_hero.rules.skill_maxima_limit
                roll_value = self.roll_value
                secondary_roll = self.secondary_roll_value
                if secondary_roll > roll_value:
                    roll_value = secondary_roll
                if roll_value > maxima_limit:
                    excess = roll_value - maxima_limit
                    if excess > self._levels:
                        excess = self._levels
                    d += float(excess) / self._level_value * self._level_cost

        # Positive adders
        has_adder = False
        n = -1
        for adder in self.assigned_adders:
            if adder.custom:
                d += adder.real_cost
                continue
            n += 1
            if adder.real_cost <= 0.0:
                continue
            if (n == 0
                    and (self.is_familiarity or self.is_proficiency)
                    and adder.minimum_cost < adder.real_cost):
                d += adder.minimum_cost
            else:
                d += adder.real_cost
            has_adder = True

        # If no adders, apply base cost
        if not has_adder and not self.levels_only:
            d += self.base_cost

        # Min/max limits
        if d < self._minimum_cost and self.min_set:
            d = self._minimum_cost
        elif d > self._max_cost and self.max_set:
            d = self._max_cost

        # Negative adders
        for adder in self.assigned_adders:
            if adder.real_cost >= 0.0:
                continue
            d += adder.real_cost

        # Skill enhancer check
        if (self.types is not None
                and len(self.types) > 0
                and not self.levels_only
                and active_hero is not None):
            skills = active_hero.skills
            for skill in skills:
                if hasattr(skill, 'applies_to_type') and hasattr(skill, 'cost_savings'):
                    enhancer = skill
                    for skill_type in self.types:
                        if not enhancer.applies_to_type(skill_type):
                            continue
                        self.enhancer_applied = enhancer
                        if d > float(enhancer.get_cost_savings()):
                            d -= float(enhancer.get_cost_savings())
                            return d
                        if d > 0.0:
                            d = 1.0
                        return d

        return d

    def include_familiarity(self) -> bool:
        """Include familiarity option."""
        return True
