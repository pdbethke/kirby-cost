"""
Power class for kirby-cost.

Converted from com.hero.objects.powers.Power.java

This is the base class for all powers in Hero Designer.
"""

from typing import Optional
from kirby_cost.objects.base import GenericObject, option_alias
from kirby_cost.objects.char_affecting import CharAffectingObject
from kirby_cost.engine.xml_attrs import XMLAttr
from kirby_cost.util.rounder import round_half_down, round_half_up


class Power(CharAffectingObject):
    """
    Base class for all powers in Hero Designer.
    
    Extends CharAffectingObject with power-specific functionality:
    - END cost calculation
    - Damage display
    - Standard effect handling
    - Resistant defenses
    """

    XML_ATTRS = (
        #: NOTE the field is `use_standard_effect` (singular). `uses_standard_effect`
    #: is the METHOD that gates it, and binding the table to that name replaced
    #: the method with a bool — 'bool' object is not callable, three tests down.
    XMLAttr("USESTANDARDEFFECT", "use_standard_effect", "yesno"),
    )

    
    # Static last sense edit timestamp (for sense caching)
    last_sense_edit: float = 0.0
    
    def __init__(self):
        """Initialize a Power."""
        super().__init__()
        self._is_power = True
        self._duration = "INSTANT"
        self.end = 0  # END cost (calculated)
        self.can_affect_primary = True
        self.resistant_defenses = False
        self.standard_effect_allowed = False
        self.use_standard_effect = False
        self._quantity = 1
        self.affects_primary = False
        self.exclusive = False
    
    def can_affect_primary_power(self) -> bool:
        """Check if this power can affect primary characteristics."""
        return self.can_affect_primary
    
    def resistant_defenses(self) -> bool:
        """Check if this power has resistant defenses."""
        # Check for RESISTANT modifier
        resistant_mod = self.find_modifier_by_id("RESISTANT")
        if resistant_mod:
            return True
        return self.resistant_defenses
    
    def standard_effect_allowed(self) -> bool:
        """Check if standard effect is allowed for this power."""
        return self.standard_effect_allowed
    
    def uses_standard_effect(self) -> bool:
        """Whether Standard Effect applies — Java ``Power.useStandardEffect()``.

        NOT named ``use_standard_effect``: ``__init__`` sets an attribute of
        that name, which shadows any method sharing it, so the original was
        dead code that returned itself. Four powers called a
        ``set_use_standard_effect()`` that was never written at all, and their
        ``damage_display`` raised AttributeError as a result.

        Java gates the field on two things (Power.java:320)::

            if (!standardEffectAllowed) return false;
            if (activeHero != null && !rules.isStandardEffectAllowed()) return false;
            return useStandardEffect;

        The rules check needs campaign rules the engine does not model, so it
        is omitted rather than guessed; the two conditions that can be answered
        are answered.
        """
        if not self.standard_effect_allowed:
            return False
        return bool(self.use_standard_effect)
    
    @property
    def summable(self) -> bool:
        """Check if this power is summable (affects characteristics)."""
        return self.affects_characteristics()
    
    @property
    def column2_output(self) -> str:
        """``<i>Awkward On Land:</i>  Running -8m (total 4m)`` — the standard
        shape every power's line is built from.

        Ported from ``Power.getColumn2Output`` (Power.java). Power had none,
        so anything that did not override it fell through to GenericObject's
        default — the alias, the input and the comments — and lost the name,
        the damage display, the adders and the modifiers. Java's own
        GenericObject.getColumn2Output is just `return getDisplay()`; the
        shape below belongs to Power, which is why inheriting the wrong one
        was silent rather than obviously broken.

        The END-reserve note is gated on useWG being off, and HD's 6E default
        is on, so it does not print for this corpus. It is here because the
        preference is a preference.
        """
        ret = f"{self.alias or ''} {self.damage_display}".strip()
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        if self.input and self.input.strip():
            ret += f":  {self.input}"
        option = (option_alias(self) or "").strip()
        if option:
            ret += f" ({option})"
        adders = self.adder_string
        if adders.strip():
            ret += f", {adders}"
        ret += self.modifier_string
        ret += self._end_reserve_note()
        return ret

    def _end_reserve_note(self) -> str:
        """" (uses Personal END)" — printed only with the WG preference off.

        HD writes it when the power costs END, the character has an ENDURANCE
        RESERVE, and no ENDRESERVEOREND modifier settles the question. Shared
        by every power's column2_output, which is why it is a method rather
        than eight copies.
        """
        if self.end_usage <= 0:
            return ""
        from kirby_cost.core.context import EngineContext
        try:
            if EngineContext.prefs().use_wg:
                return ""
        except Exception:  # noqa: BLE001
            return ""
        hero = EngineContext.active_hero()
        if hero is None:
            return ""
        if GenericObject.find_object_by_id(hero.powers, "ENDURANCERESERVE") is None:
            return ""
        if GenericObject.find_object_by_id(
                self.all_assigned_modifiers, "ENDRESERVEOREND") is not None:
            return ""
        return (" (uses END Reserve)" if self.use_end_reserve
                else " (uses Personal END)")

    @property
    def damage_display(self) -> str:
        """Get the damage display string (e.g., '8d6', '12d6+1')."""
        if "[LVL]" in self._display.upper():
            return ""
        if self._level_value == 0.0 or self._level_cost == 0.0:
            return ""
        
        damage_str = f"{self._levels}d6"
        pip_count = 0
        
        # Check for damage adders
        for adder in self.assigned_adders:
            if adder.xmlid == "PLUSONEPIP":
                adder.display_in_string = False
                if self._levels > 0:
                    damage_str = f"{self._levels}d6+1"
                else:
                    damage_str = "1 point"
                pip_count += 1
            elif adder.xmlid == "PLUSONEHALFDIE":
                adder.display_in_string = False
                damage_str = f"{self._levels} 1/2d6"
                pip_count += 1
            elif adder.xmlid == "MINUSONEPIP":
                adder.display_in_string = False
                damage_str = f"{self._levels + 1}d6-1"
                pip_count += 1
        
        # Add standard effect if applicable
        if self.uses_standard_effect():
            points = self._levels * 3 + pip_count
            # Java pluralises on the LEVELS, not on the point total
            # (`getLevels() > 0 ? "s" : ""`), so a power with no levels reads
            # "1 point" and everything else takes the "s" regardless of count.
            point_str = "points" if self._levels > 0 else "point"
            damage_str += f" (standard effect: {points} {point_str})"
        
        return damage_str
    
    @property
    def ap_per_end(self) -> int:
        """Active Points per END. ``GenericObject.getAPPerEnd``, :1340-1356.

        Was a stub returning a hardcoded 10 ("This should come from
        rules.get_ap_per_end()"), which ignored the one branch that matters
        most: **a power that does not use END costs none**. Damage Reduction
        and Resistant Protection are both USESEND="No" in Main6E and were
        being charged END anyway -- Ravel's Resistant Protection reported 4
        where Hero Designer reports 0.

        The STR special-case is Java's and lives in this same base method
        (GenericObject.java:1344-1346); it is inert here because a Power is
        never xmlid STR, but it is kept so the two ports read alike.
        """
        from kirby_cost.core.context import EngineContext
        n = 10
        hero = EngineContext.active_hero()
        if hero is not None and hero.rules is not None:
            n = hero.rules.ap_per_end
            if self.xmlid == "STR":
                n = hero.rules.get_str_ap_per_end(hero)
        return n if self.uses_end else 0
    
    @property
    def column3_output(self) -> str:
        """``Power.getColumn3Output`` (Power.java:105-131).

        Three branches, and the middle one is the surprise: a power that costs
        no END prints "0" where the base class prints nothing. A power paid
        for with Charges prints the charge count in brackets instead, suffixed
        by the kind of charge -- bc boostable, rc recoverable, cc continuing,
        nr never-recovers.
        """
        from kirby_cost.objects.base import GenericObject
        usage = self.end_usage
        if usage > 0:
            return str(usage)
        charges = GenericObject.find_object_by_id(self.assigned_modifiers, "CHARGES")
        if charges is None:
            return "0"
        option = getattr(charges, "selected_option", None)
        count = getattr(option, "alias", "") or "" if option else ""
        adders = charges.assigned_adders
        for adder_id, suffix in (("BOOSTABLE", " bc"), ("RECOVERABLE", " rc"),
                                 ("CONTINUING", " cc"), ("NEVERRECOVER", " nr")):
            if GenericObject.find_object_by_id(adders, adder_id) is not None:
                return f"[{count}{suffix}]"
        return f"[{count}]"

    @property
    def end_usage(self) -> int:
        """``GenericObject.getEndUsage``, shared with Characteristic.

        The algorithm is the BASE one in Java; it lived here alone,
        which is why a characteristic bought as a power had none.
        """
        from kirby_cost.objects.base import compute_end_usage
        return compute_end_usage(self, self.ap_per_end)

    def get_md_levels(self) -> int:
        """Get Mental Defense levels from this power."""
        if self.md_increase_levels != 0:
            md_levels = (self._levels / self.md_increase_levels) * self.md_increase
            return int(round_half_up(md_levels))
        return 0
    
    def get_save_xml(self):
        """
        Get XML element for saving this power.
        
        Converted from com.hero.objects.powers.Power.getSaveXML()
        
        Returns:
            lxml.etree.Element representing this power's saved state
        """
        # Get base element from parent
        element = self.get_general_save_xml()
        
        # Set tag name to "POWER"
        element.tag = "POWER"
        
        # Power-specific attributes
        if self.standard_effect_allowed:
            element.set("USESTANDARDEFFECT", "Yes" if self.use_standard_effect else "No")
        
        element.set("QUANTITY", str(self._quantity))
        element.set("AFFECTS_PRIMARY", "Yes" if self.affect_primary else "No")
        element.set("AFFECTS_TOTAL", "Yes" if self.affect_total else "No")
        
        return element
    
    @property
    def quantity(self) -> int:
        """Get the quantity."""
        return self._quantity

    @quantity.setter
    def quantity(self, quantity: int) -> None:
        """Set the quantity.

        This decorator was missing, so the setter REPLACED the property and
        `power.quantity` returned a bound method — truthy, never equal to a
        number, and silently wrong anywhere it was compared.
        """
        self._quantity = quantity

