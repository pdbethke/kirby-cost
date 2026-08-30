"""
ENDReserveOrEND modifier for kirby-cost.

Converted from com.hero.objects.modifiers.ENDReserveOrEND.java

Had no engine class before this port. ``ENDRESERVEOREND`` is NOT a
Main6E.hdt template modifier (0 hits; only the 5E ``Main.hdt`` shipped
alongside it declares this xmlid) -- Main6E never exercises this class
through the survey. With no Python class registered for the xmlid, the
loader's generic ``Modifier`` fallback answered every ``included()``
question with "" (no restriction), silently dropping this rule rather
than refusing it -- HD refuses it on anything that doesn't cost END, and
on any character with no Endurance Reserve to draw from.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class ENDReserveOrEND(Modifier, xmlid="ENDRESERVEOREND"):
    """
    ENDReserveOrEND modifier.

    A power may be powered by END Reserve or the character's own END;
    meaningless on an ability that costs no END, and meaningless on a
    character with no Endurance Reserve to draw from.
    """

    def __init__(self, element=None):
        """Initialize an ENDReserveOrEND modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)

    def included(self, generic_object: GenericObject) -> str:
        """
        Check if this modifier can be applied to the given object.

        Ported from ``ENDReserveOrEND.included`` (ENDReserveOrEND.java:40-72), with one
        acknowledged deviation: Java runs the EnduranceReserve/
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

        # ENDReserveOrEND.java:45-50.
        if isinstance(generic_object, EnduranceReserve):
            return f"{self.display} cannot be applied to an {generic_object.display}"
        if isinstance(generic_object, EnduranceReserveRecovery):
            return f"{self.display} cannot be applied to an {generic_object.display}"

        # ENDReserveOrEND.java:51-54.
        if generic_object.end_usage == 0:
            return f"{self.display} can only be applied to abilities which cost END."

        # ENDReserveOrEND.java:55-70 -- the hero-level read: only meaningful
        # on a character that HAS an Endurance Reserve to draw from, found
        # among the hero's powers or inside a CompoundPower.
        from kirby_cost.objects.base import active_hero_objects
        for obj in active_hero_objects():
            if isinstance(obj, EnduranceReserve):
                return ""

        return (f"{self.display} can only be applied to abilities on "
                "characters that have an Endurance Reserve.")
