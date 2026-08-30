"""
Custom Power class for kirby-cost.

Converted from com.hero.objects.powers.CustomPower.java

Power for user-defined custom powers.
"""

from kirby_cost.engine.xml_attrs import XMLAttr
from kirby_cost.objects.powers.power import Power
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.rounder import round_half_down, round_up
from kirby_cost.objects.frameworks import is_multipower, is_elemental_control, is_vpp
from kirby_cost.objects.modifiers.linked import is_linked
from typing import Optional


class CustomPower(Power, xmlid="CUSTOMPOWER"):
    """
    Custom Power.

    User-defined custom power with custom cost calculations.
    """

    #: A custom power has no template entry, so unlike every other power it
    #: carries its own definition of what it DOES — and none of it was read or
    #: written. 164 corpus characters round-tripped their custom powers into
    #: blanks: no damage, no killing flag, no defence, no range, no duration,
    #: no target. The engine's own fields for these existed and stayed at their
    #: constructor defaults, so nothing failed; the power simply became inert.
    #:
    #: Java writes all twelve unconditionally
    #: (``CustomPower.getSaveXML``) and reads them back in
    #: ``restoreFromSave`` — including DEFENSE falling back to "NONE" when the
    #: document leaves it blank, which is why the field defaults there too.
    #:
    #: DOESBODY/DOESKNOCKBACK/DURATION name ``orig_does_body``/
    #: ``orig_does_knockback``/``orig_duration`` rather than ``does_body``/
    #: ``does_knockback``/``duration``: this branch turned the latter three
    #: into COMPUTED properties (GenericObject's ``doesBODY()``/
    #: ``doesKnockback()``/``getDuration()``, which NND, AVAD, STUN Only and
    #: the duration Advantages rewrite), where CustomPower.java:280-289
    #: (``getSaveXML``) writes the plain FIELDS -- ``doesBODY``,
    #: ``doesKnockback``, ``duration`` -- unconditionally, never those
    #: methods. ``orig_*`` reads the same underlying field the computed
    #: property derives from, and its setter (added alongside this) writes
    #: to that same field, so both directions of XML_ATTRS land in the
    #: field CustomPower.java actually persists.
    XML_ATTRS = (
        XMLAttr("DOESBODY", "orig_does_body", "yesno"),
        XMLAttr("DOESDAMAGE", "does_damage", "yesno"),
        XMLAttr("DOESKNOCKBACK", "orig_does_knockback", "yesno"),
        XMLAttr("KILLING", "killing", "yesno"),
        XMLAttr("DEFENSE", "defense"),
        XMLAttr("END", "uses_end", "yesno"),
        XMLAttr("VISIBLE", "visible", "yesno"),
        XMLAttr("RANGE", "range"),
        XMLAttr("DURATION", "orig_duration"),
        XMLAttr("TARGET", "target"),
        # Java holds col3Output as null until set and writes "" for null or
        # blank, so the empty string IS the value HD states — the field starts
        # "" rather than None because the writer skips a None and HD writes
        # ENDCOLUMNOUTPUT on every custom power without exception.
        XMLAttr("ENDCOLUMNOUTPUT", "col3_output"),
        XMLAttr("USECUSTOMENDCOLUMN", "use_custom_column3", "yesno"),
    )

    @property
    def damage_display(self) -> str:
        """A custom power states no damage.

        Java's ``CustomPower.getDamageDisplay`` is `return ""`. Inheriting
        Power's put a bare "0d6" on the end of every one of them.
        """
        return ""

    def __init__(self):
        """Initialize a Custom Power."""
        super().__init__()
        self.xmlid = CustomPower.XMLID
        self.col3_output: str = ""
        self.use_custom_column3: bool = False
    
    @property
    def levels(self) -> int:
        """CustomPower levels = roundUp(baseCost)."""
        return round_up(self._base_cost)

    @levels.setter
    def levels(self, value) -> None:
        self._levels = value

    @property
    def active_cost(self) -> float:
        """Calculate the active cost."""


        return self._compute_active_cost()



    def _compute_active_cost(self, exclude_xmlid: str = None) -> float:
        """
        Calculate active cost for custom power.
        
        Includes base cost, required adders, optional adders, and advantages.
        """
        active_cost = self._base_cost
        
        # Add required adders
        for adder in self.assigned_adders:
            if adder.is_required:
                active_cost += adder.real_cost
        
        # Add optional positive adders
        for adder in self.assigned_adders:
            if not adder.is_required and adder.real_cost > 0.0:
                active_cost += adder.real_cost
        
        # Apply min/max limits
        if active_cost < self._minimum_cost and self.min_set:
            active_cost = self._minimum_cost
        elif active_cost > self._max_cost and self.max_set:
            active_cost = self._max_cost
        
        # Add optional negative adders
        for adder in self.assigned_adders:
            if not adder.is_required and adder.real_cost < 0.0:
                active_cost += adder.real_cost
        
        # Apply advantages
        modifier_sum = 0.0
        has_advantages = False
        
        for mod in self.assigned_modifiers:
            if mod.total_value > 0.0:
                modifier_sum += mod.total_value
                has_advantages = True
        
        # Parent list advantages
        parent = self._parent
        if self.main_power:
            parent = self.main_power.parent
        if parent:
            for mod in parent.assigned_modifiers:
                if mod.types and "VPP" in mod.types:
                    continue
                if mod.xmlid == "CHARGES" and is_multipower(parent):
                    continue
                if is_linked(mod):
                    continue
                if mod.total_value <= 0.0:
                    continue
                if (GenericObject.find_object_by_id(self._assigned_modifiers, mod.xmlid) and
                    mod.xmlid not in ("GENERIC_OBJECT", "CUSTOM_MODIFIER", "MODIFIER")):
                    continue
                if is_multipower(parent) or is_elemental_control(parent):
                    continue
                modifier_sum += mod.total_value
                has_advantages = True

        active_cost = active_cost * (1.0 + modifier_sum)
        if has_advantages:
            active_cost = round_half_down(active_cost)

        return active_cost

    @property
    def real_cost_pre_list(self) -> float:
        """
        Calculate real cost for custom power.

        Ported from CustomPower.java getRealCostPreList().
        """
        self.enhancer_applied = None
        d = self.active_cost
        limitation_sum = 0.0
        has_limitations = False

        for mod in self.assigned_modifiers:
            if mod.total_value < 0.0:
                limitation_sum += mod.total_value
                has_limitations = True

        # Parent list limitations
        parent = self._parent
        if self.main_power:
            parent = self.main_power.parent
        if parent and not is_vpp(parent):
            for mod in parent.assigned_modifiers:
                if mod.types and "VPP" in mod.types:
                    continue
                if mod.xmlid == "CHARGES" and is_multipower(self._parent):
                    continue
                if mod.total_value >= 0.0:
                    continue
                if (GenericObject.find_object_by_id(self._assigned_modifiers, mod.xmlid) and
                    mod.xmlid not in ("GENERIC_OBJECT", "CUSTOM_MODIFIER", "MODIFIER")):
                    continue
                limitation_sum += mod.total_value
                has_limitations = True

        real_cost = d / (1.0 + abs(limitation_sum))
        if has_limitations:
            real_cost = round_half_down(real_cost)

        # Minimum 1 CP
        if (real_cost < 1.0 and
            (d > 0.0 or
             (self._levels > 0 and len(self.assigned_adders) == 0 and
              self.base_cost >= 0.0))):
            real_cost = 1.0

        # Quantity cost
        if self._quantity > 1:
            qty_cost = 0
            qty = float(self._quantity)
            while qty > 1.0:
                qty_cost += 5
                qty /= 2.0
            real_cost += float(qty_cost)

        return real_cost
    


