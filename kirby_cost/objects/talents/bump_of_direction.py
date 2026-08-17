"""
Bump Of Direction Talent for kirby-cost.

There is no bespoke com.hero.objects.talents.BumpOfDirection.java class; in the
Java oracle this talent loads as the generic Talent (class="Talent") with a
template-driven fixed base cost (3 points in 6E) and no level or adder cost.
A minimal registered subclass inheriting the base Talent cost matches the
oracle exactly.
"""

from kirby_cost.objects.talents.talent import Talent


class BumpOfDirection(Talent, xmlid="BUMP_OF_DIRECTION"):
    """Bump Of Direction Talent. Fixed cost inherited from the template."""

    def __init__(self, element=None):
        """Initialize a Bump Of Direction talent."""
        super().__init__(element, self.XMLID)
