"""
Change Environment power class for kirby-cost.

Converted from com.hero.objects.powers.ChangeEnvironment.java

Power to change the environment.
"""

from kirby_cost.objects.powers.power import Power


class ChangeEnvironment(Power, xmlid="CHANGEENVIRONMENT"):
    """
    Change Environment power.
    
    Alters the environment in various ways.
    """
    
    def __init__(self):
        """Initialize a Change Environment power."""
        super().__init__()
        self.xmlid = ChangeEnvironment.XMLID
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Empty in 6E. The 5E branch computed a radius from the level power;
        6E states the area through an Area Of Effect modifier instead."""
        return ""
    # NOTE: no ``can_add`` here. There was one, and it was worse than nothing:
    # it called ``super().can_add(adder)``, which does not exist anywhere in
    # the engine, so ANY call raised AttributeError — while its docstring
    # advertised "special logic for MULTIPLECOMBATEFFECTS,
    # VARYINGCOMBATEFFECTS, LONG" that its body (a bare ``return True``) did
    # not contain. Nothing in kirby-cost, kirby-combat or kirby-api ever
    # called it, which is the only reason it never crashed anything.
    #
    # Adder/option VALIDATION — which adders a given power legally accepts —
    # is a capability this engine deliberately does not have (see
    # ChangeEnvironment.canAdd in the Java source for the shape it would
    # take). It is not needed to COST an imported build: HD validated the
    # character before it was ever saved. It becomes necessary when a build is
    # assembled here rather than imported, and at that point it wants a
    # template-derived matrix and a spec, not a stub that answers True.

    @property
    def column2_output(self) -> str:
        """``Change Environment (stench) (-6 to Smell/Taste Group PER Rolls, ...)``.

        Ported from ``ChangeEnvironment.getColumn2Output``. Everything the
        environment DOES goes in one bracket, and the PER-roll penalties are
        rewritten on the way in: a PERROLL adder is not printed as an adder
        but as "-N to <sense> PER Rolls", which is why it is marked
        not-to-be-printed once read.

        ALTEREDSHAPE is lifted out of the modifier list while the modifiers
        render and put back afterwards — it describes the shape of the area,
        which the bracket has already covered.
        """
        from kirby_cost.objects.base import GenericObject, option_alias
        ret = f"{self.alias or ''} {self.damage_display}".strip()
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        if self.input and self.input.strip():
            ret += f":  {self.input}"
        ret += " ("

        adder_str = ""
        for ad in self.assigned_adders:
            if ad.xmlid in ("PERROLL", "PERROLLGROUP"):
                if adder_str.strip():
                    adder_str += ", "
                adder_str += (f"-{ad.levels} to "
                              f"{(option_alias(ad) or '').strip()} PER Rolls")
                ad.display_in_string = False
        check = self.adder_string
        if check.strip():
            if adder_str.strip():
                adder_str += ", "
            adder_str += check

        option = (option_alias(self) or "").strip()
        if option:
            ret += ", " + option
            if adder_str.strip():
                ret += ", " + adder_str
        elif adder_str.strip():
            ret += adder_str
        ret += ")"

        original = self._assigned_modifiers
        altered = GenericObject.find_object_by_id(original, "ALTEREDSHAPE")
        if altered is not None:
            self._assigned_modifiers = [m for m in original if m is not altered]
        try:
            ret += self.modifier_string
        finally:
            self._assigned_modifiers = original
        ret += self._end_reserve_note()
        return ret
