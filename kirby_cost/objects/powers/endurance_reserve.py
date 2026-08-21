"""
Endurance Reserve power class for kirby-cost.

Converted from com.hero.objects.powers.EnduranceReserve.java

Reserve of END points with a separate Recovery component.
The Reserve and Recovery can share modifiers (recIsSamePower) or be separate.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.rounder import round_half_down
from kirby_cost.objects.frameworks import is_multipower, is_elemental_control
from kirby_cost.objects.modifiers.linked import is_linked
from typing import Optional


class EnduranceReserve(Power, xmlid="ENDURANCERESERVE"):
    """
    Endurance Reserve power.

    Has two components: the reserve (END pool) and recovery (REC rate).
    If both have identical modifiers, they're treated as one power for cost purposes.
    """

    def __init__(self):
        super().__init__()
        self.xmlid = EnduranceReserve.XMLID
        self._duration = "CONSTANT"
        self.rec: Optional[GenericObject] = None  # EnduranceReserveRecovery

    def get_save_xml(self):
        """Serialize endurance reserve including recovery component."""
        element = self.get_general_save_xml()
        if self.rec is not None:
            rec_elem = self.rec.save_xml()
            if rec_elem is not None:
                element.append(rec_elem)
        return element

    @property
    def damage_display(self) -> str:
        """Empty. Java's ``EnduranceReserve.getDamageDisplay`` returns "".

        The numbers this power is about — its defences and dimensions, or its
        END and REC — are written by column2_output itself, so a damage
        display that also produced them printed them twice.
        """
        return ""
    def rec_is_same_power(self) -> bool:
        """
        Check if recovery has the same modifiers as the reserve.

        If both components have identical modifier sets, they share cost calculations.
        Ported from EnduranceReserve.java recIsSamePower().
        """
        # No REC at all means there is nothing to tell apart, so they are the
        # same power -- Java returns TRUE here (EnduranceReserve.java:310).
        # Returning False instead labelled the two halves of a reserve that
        # has no separate REC: "(320 END, 150 REC) Reserve:  (180 Active
        # Points) ...; REC: ...".
        if self.rec is None:
            return True

        my_mods = self.assigned_modifiers
        rec_mods = self.rec.assigned_modifiers

        if len(my_mods) != len(rec_mods):
            return False

        # Each of mine must match ANY of the REC's, not the one at the same
        # index: Java's inner loop scans the whole list and `continue OUTER`s
        # on the first hit, so two identical sets in a different order are
        # still the same power.
        for mine in my_mods:
            if not any(getattr(theirs, "column2_output", "")
                       == getattr(mine, "column2_output", "")
                       for theirs in rec_mods):
                return False

        return True

    @property
    def active_cost(self) -> float:
        """Calculate the active cost."""


        return self._compute_active_cost()



    def _compute_active_cost(self, exclude_xmlid: str = None) -> float:
        """
        Calculate active cost for END Reserve.

        If recovery is same power, add its total cost before applying advantages.
        Otherwise, add recovery's active cost separately after.

        Ported from EnduranceReserve.java getActiveCost().
        """
        same_power = self.rec_is_same_power()

        # Start with reserve's total cost (calls GenericObject.getTotalCost via super)
        d = super().total_cost

        if same_power and self.rec is not None:
            d += self.rec.total_cost

        # Sum positive advantages
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

        result = d * (1.0 + modifier_sum)

        # Set recovery's parent list for its own calculations
        if self.rec is not None:
            self.rec.parent = self._parent

        if has_advantages:
            result = round_half_down(result)

        # If not same power, add recovery's active cost separately
        if not same_power and self.rec is not None:
            result += self.rec.active_cost

        return result

    @property
    def real_cost_pre_list(self) -> float:
        """
        Calculate real cost for END Reserve.

        If same power, apply limitations to combined active cost.
        Otherwise, add recovery's real cost separately.

        Ported from EnduranceReserve.java getRealCostPreList().
        """
        same_power = self.rec_is_same_power()

        # Use combined active cost if same power, else just reserve's active
        if same_power:
            d = self.active_cost
        else:
            # Get just the reserve's active cost (without recovery)
            d = super()._compute_active_cost()

        # Sum negative limitations
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
        if parent:
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

        result = d / (1.0 + abs(limitation_sum))
        if has_limitations:
            result = round_half_down(result)

        # Set recovery's parent list
        if self.rec is not None:
            self.rec.parent = self._parent

        # If not same power, add recovery's real cost separately
        if not same_power and self.rec is not None:
            result += self.rec.real_cost_pre_list

        # Minimum 1 CP
        if result == 0.0 and d > 0.0:
            result = 1.0

        # Quantity cost
        if self._quantity > 1:
            qty_cost = 0
            qty = float(self._quantity)
            while qty > 1.0:
                qty_cost += 5
                qty /= 2.0
            result += float(qty_cost)

        return result

    @property
    def column2_output(self) -> str:
        """``Endurance Reserve  (100 END, 12 REC)``.

        Ported from ``EnduranceReserve.getColumn2Output``. A reserve is two
        numbers, not one — how much END it holds and how fast it comes back —
        and the REC lives on a child object, so a port that only reads the
        power itself can only ever print half of it.

        A reserve bought at zero levels is really a REC purchase, and HD
        renders it AS the REC: alias, damage display and modifiers all come
        from the child.
        """
        rec = self.rec
        if self._levels == 0 and rec is not None:
            ret = f"{rec.alias or ''} {rec.damage_display}"
            if rec._name and rec._name.strip():
                ret = f"<i>{rec._name}:</i>  {ret}"
            ret += f" ({rec._levels} REC)"
            if rec.input and rec.input.strip():
                ret += f":  {rec.input}"
            rec_adders = rec.adder_string
            if rec_adders.strip():
                ret += f" (REC: {rec_adders})"
            rec_mods = rec.modifier_string.strip()
            if rec_mods.startswith(";"):
                rec_mods = rec_mods[1:]
            if rec_mods.strip():
                ret += f"; {rec_mods}"
            return ret

        ret = f"{self.alias or ''} {self.damage_display}"
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        ret += f" ({self._levels} END, {rec._levels if rec is not None else 0} REC)"
        if self.input and self.input.strip():
            ret += f":  {self.input}"
        # An Endurance Reserve is TWO purchases printed as one line -- the
        # reserve and its REC -- so each side's adders and modifiers are
        # labelled. Ported from EnduranceReserve.java:141-194; this tail used
        # to be a bare ", {adders}" + modifier_string, which dropped the
        # labels entirely:
        #   HD: ... (300 END, 60 REC) Reserve:  (115 Active Points); OIF (-1/2)
        #   py: ... (300 END, 60 REC) (115 Active Points); OIF (-1/2)
        from kirby_cost.objects.base import option_alias
        adders = self.adder_string
        rec_adders = rec.adder_string if rec is not None else ""
        if self._selected_option is not None:
            ret += f" ({option_alias(self)}"
            if adders.strip() or rec_adders.strip():
                ret += f"; {adders}"
                if adders.strip():
                    ret += ", "
                if rec_adders.strip():
                    ret += f"REC: {rec_adders}"
            ret += ")"
        elif adders.strip() or rec_adders.strip():
            ret += f" ({adders}"
            if adders.strip():
                ret += ", "
            if rec_adders.strip():
                ret += f"REC: {rec_adders}"
            ret += ")"

        # When the REC is its own purchase, each side's modifiers say which
        # side they are on. When it is the same power, they are already one
        # list and labelling would double-count.
        the_same = self.rec_is_same_power()
        modifier_string = self.modifier_string
        if not the_same and modifier_string.strip():
            ret += " Reserve: "
            if modifier_string.strip().startswith(";"):
                modifier_string = modifier_string.strip()[1:]
        ret += modifier_string
        if not the_same and rec is not None:
            rec_mods = rec.modifier_string
            if rec_mods.strip().startswith(";"):
                rec_mods = rec_mods.strip()[1:]
            if rec_mods.strip():
                ret += f"; REC: {rec_mods}"
        ret += self._end_reserve_note()
        return ret
