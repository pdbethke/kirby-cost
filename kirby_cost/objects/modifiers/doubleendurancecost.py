"""
DoubleEnduranceCost modifier for kirby-cost.

Converted from com.hero.objects.modifiers.DoubleEnduranceCost.java

Not registered before this port. Main6E.hdt carries no ``DOUBLEENDCOST``
(nor ``DOUBLEENDURANCECOST``) template entry -- the survey never exercises
this class, and doubling END cost is offered in Main6E as INCREASEDEND's
``2X`` option instead. The Java class exists for other templates that do
declare it, so it is ported here for the same reason ``ENDReserveOrEND``
is: an unregistered xmlid falls to the generic ``Modifier``, which drops
this rule silently rather than refusing it.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class DoubleEnduranceCost(Modifier, xmlid="DOUBLEENDCOST"):
    """
    DoubleEnduranceCost modifier.

    Doubles a power's END cost; meaningless on an ability that costs no
    END, and meaningless on a character with no Endurance Reserve to draw
    from.
    """

    def __init__(self, element=None):
        """Initialize a DoubleEnduranceCost modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)

    def included(self, generic_object: GenericObject) -> str:
        """
        Check if this modifier can be applied to the given object.

        Ported from ``DoubleEnduranceCost.included``
        (DoubleEnduranceCost.java:40-72). Same acknowledged deviation as
        ``ENDReserveOrEND.included``: Java runs the EnduranceReserve/
        EnduranceReserveRecovery/end_usage checks unconditionally and only
        gates the FINAL hero-scan block on ``ret.trim().length() == 0``, so a
        super().included() refusal can still be overwritten by a more
        specific message from those checks. This port returns immediately on
        any non-empty super().included() instead, short-circuiting all four
        checks together -- same ALLOWED/REFUSED verdict in every case (none
        of the four branches below ever returns ""), but a different REASON
        STRING than Java's when super() already refused for an unrelated
        cause. Untested against the oracle either way (neither xmlid is a
        Main6E.hdt template modifier -- see the module docstring), so left
        as the simpler shape rather than chasing an unverifiable match.
        """
        result = super().included(generic_object)
        if result and result.strip():
            return result

        if self.force_allow:
            return result

        from kirby_cost.objects.powers.endurance_reserve import EnduranceReserve
        from kirby_cost.objects.powers.endurance_reserve_recovery import (
            EnduranceReserveRecovery,
        )

        # DoubleEnduranceCost.java:45-50.
        if isinstance(generic_object, EnduranceReserve):
            return f"{self.display} cannot be applied to an {generic_object.display}"
        if isinstance(generic_object, EnduranceReserveRecovery):
            return f"{self.display} cannot be applied to an {generic_object.display}"

        # DoubleEnduranceCost.java:51-54.
        if generic_object.end_usage == 0:
            return f"{self.display} can only be applied to abilities which cost END."

        # DoubleEnduranceCost.java:55-70 -- the hero-level read: only
        # meaningful on a character that HAS an Endurance Reserve, found
        # among the hero's powers or inside a CompoundPower.
        from kirby_cost.objects.base import active_hero_objects
        for obj in active_hero_objects():
            if isinstance(obj, EnduranceReserve):
                return ""

        return (f"{self.display} can only be applied to abilities on "
                "characters that have an Endurance Reserve.")
