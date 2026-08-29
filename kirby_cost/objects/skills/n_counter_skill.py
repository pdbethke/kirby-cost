"""
NCounterSkill — consolidated adder-based skill with n-counter discount.

Replaces: Navigation, AnimalHandler, Gambling, Weaponsmith, Forgery.

Two adder-discount variants:
- Group N (Navigation, AnimalHandler, Weaponsmith): first adder pays full,
  subsequent adders pay minimum_cost discount. Negative adders use n-counter.
- Group G (Gambling, Forgery): first adder gets minimum_cost discount only when
  familiarity/proficiency. All other adders pay full. Negative adders are simple sums.
"""

from typing import ClassVar, Optional, TYPE_CHECKING
from kirby_cost.objects.skills.skill import Skill

if TYPE_CHECKING:
    from kirby_cost.io.hdc_loader import LoadedHero as Hero  # the live hero type


class NCounterSkill(Skill, xmlid="NAVIGATION"):
    """Skill where adders use an n-counter discount pattern.

    Used by: NAVIGATION, ANIMAL_HANDLER, GAMBLING, WEAPONSMITH, FORGERY.

    The default flag values port Java Navigation.java.  The Java siblings
    (AnimalHandler.java, Weaponsmith.java, Gambling.java, Forgery.java)
    differ only in the four class flags below — see the registered
    subclasses at the bottom of this module.

    Set ``_first_adder_full_cost = True`` (default) for Navigation-style:
    first adder pays full, subsequent get minimum_cost discount.

    Set ``_first_adder_full_cost = False`` for Gambling-style:
    first adder gets minimum discount only if familiarity/proficiency,
    all other adders pay full cost.
    """

    _first_adder_full_cost: ClassVar[bool] = True
    # Java Navigation/AnimalHandler early-return 0 only when
    # isFamiliarity() && isEveryman(); Weaponsmith/Gambling/Forgery
    # return 0 on isEveryman() alone.
    _everyman_zero_requires_familiarity: ClassVar[bool] = True
    # Java skill-maxima surcharge requires rollBased everywhere except
    # AnimalHandler.java (which omits the && rollBased condition).
    _maxima_requires_roll_based: ClassVar[bool] = True
    # Java Navigation's positive-adder loop only short-circuits custom
    # adders with getRealCost() > 0; the other four add custom adders of
    # any sign in the positive loop (`if (ad.isCustom()) { total += ... }`).
    _custom_adders_any_sign: ClassVar[bool] = False
    # Java Navigation's negative-adder loop uses the n-counter pattern;
    # the other four sum negative adders directly.
    _negative_adders_n_counter: ClassVar[bool] = True

    def __init__(self, xmlid: str = None):
        """Initialize NCounterSkill."""
        super().__init__(xmlid or self.XMLID)

    @property
    def total_cost(self) -> float:
        """Get total cost using n-counter adder discount pattern."""
        active_hero = self._get_active_hero()
        self.enhancer_applied = None

        d = self.base_cost
        if self._everyman_zero_requires_familiarity:
            if self.is_familiarity and self.is_everyman:
                return 0.0
        elif self.is_everyman:
            return 0.0

        # Check if there are any non-custom adders
        has_non_custom_adder = any(
            not adder.custom for adder in self.assigned_adders
        )

        if len(self.assigned_adders) == 0 or not has_non_custom_adder:
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

            # Skill maxima handling
            if (self._levels > 0
                    and active_hero is not None
                    and active_hero.rules.use_skill_maxima
                    and (self.roll_based
                         or not self._maxima_requires_roll_based)):
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
        if self._first_adder_full_cost:
            d = self._add_positive_adders_n_counter(d)
        else:
            d = self._add_positive_adders_simple(d)

        # Min/max limits
        if d < self._minimum_cost and self.min_set:
            d = self._minimum_cost
        elif d > self._max_cost and self.max_set:
            d = self._max_cost

        # Negative adders
        if self._negative_adders_n_counter:
            d = self._add_negative_adders_n_counter(d)
        else:
            d = self._add_negative_adders_simple(d)

        # Skill enhancer check
        d = self._apply_enhancer(d, active_hero)

        return d

    def _add_positive_adders_n_counter(self, d: float) -> float:
        """Navigation-style: first adder full, subsequent get minimum discount."""
        n = -1
        for adder in self.assigned_adders:
            if adder.custom and (self._custom_adders_any_sign
                                 or adder.real_cost > 0.0):
                d += adder.real_cost
                continue
            n += 1
            if adder.real_cost <= 0.0:
                continue
            if n == 0 and not self.is_familiarity and not self.is_proficiency:
                d += adder.real_cost
                continue
            if adder.minimum_cost < adder.real_cost:
                d += adder.minimum_cost
                continue
            d += adder.real_cost
        return d

    def _add_positive_adders_simple(self, d: float) -> float:
        """Gambling-style: first adder discount only if familiarity/proficiency."""
        n = -1
        for adder in self.assigned_adders:
            if adder.custom:
                d += adder.real_cost
                continue
            n += 1
            if adder.real_cost <= 0.0:
                continue
            if n == 0 and (self.is_familiarity or self.is_proficiency) and adder.minimum_cost < adder.real_cost:
                d += adder.minimum_cost
                continue
            d += adder.real_cost
        return d

    def _add_negative_adders_n_counter(self, d: float) -> float:
        """Navigation-style n-counter for negative adders."""
        n = -1
        for adder in self.assigned_adders:
            if adder.custom and adder.real_cost < 0.0:
                d += adder.real_cost
                continue
            n += 1
            if adder.real_cost >= 0.0:
                continue
            if n == 0 and not self.is_familiarity and not self.is_proficiency:
                d += adder.real_cost
                continue
            if adder.minimum_cost < adder.real_cost:
                d += adder.minimum_cost
                continue
            d += adder.real_cost
        return d

    def _add_negative_adders_simple(self, d: float) -> float:
        """Gambling-style: simple sum of negative adders."""
        for adder in self.assigned_adders:
            if adder.real_cost >= 0.0:
                continue
            d += adder.real_cost
        return d

    def _apply_enhancer(self, d: float, active_hero) -> float:
        """Apply skill enhancer discount if applicable."""
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


class GamblingStyleSkill(NCounterSkill):
    """Gambling/Forgery variant: different adder discount pattern.

    Java Gambling.java / Forgery.java: plain isEveryman() early return,
    rollBased maxima, custom adders added regardless of sign, first adder
    min-discounted only when familiarity/proficiency, simple negative sums.
    """
    _first_adder_full_cost: ClassVar[bool] = False
    _everyman_zero_requires_familiarity: ClassVar[bool] = False
    _custom_adders_any_sign: ClassVar[bool] = True
    _negative_adders_n_counter: ClassVar[bool] = False


class AnimalHandler(NCounterSkill, xmlid="ANIMAL_HANDLER"):
    """Java AnimalHandler.java.

    Like Navigation but: skill-maxima surcharge does NOT require rollBased,
    custom adders are added in the positive loop regardless of sign, and
    negative adders are summed directly (no n-counter).
    """
    _maxima_requires_roll_based: ClassVar[bool] = False
    _custom_adders_any_sign: ClassVar[bool] = True
    _negative_adders_n_counter: ClassVar[bool] = False


class Weaponsmith(NCounterSkill, xmlid="WEAPONSMITH"):
    """Java Weaponsmith.java.

    Like AnimalHandler but with the plain isEveryman() early return and
    the rollBased condition on the skill-maxima surcharge.
    """
    _everyman_zero_requires_familiarity: ClassVar[bool] = False
    _custom_adders_any_sign: ClassVar[bool] = True
    _negative_adders_n_counter: ClassVar[bool] = False


class Gambling(GamblingStyleSkill, xmlid="GAMBLING"):
    """Java Gambling.java."""


class Forgery(GamblingStyleSkill, xmlid="FORGERY"):
    """Java Forgery.java."""
