"""
Compound Power class for kirby-cost.

Converted from com.hero.objects.powers.CompoundPower.java

Power that combines multiple powers together.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.char_affecting import CharAffectingObject
from kirby_cost.objects.base import _show_common_limitations
from kirby_cost.util.rounder import round_half_down, round_half_up
from typing import List


class CompoundPower(Power, xmlid="COMPOUNDPOWER"):
    """
    Compound Power.
    
    Combines multiple powers into a single power.
    """
    
    def __init__(self):
        """Initialize a Compound Power."""
        super().__init__()
        self.xmlid = CompoundPower.XMLID
        self.list_separator: str = " <b>plus</b> "
        self.powers: List[GenericObject] = []
    
    # ═══════════════════════════════════════════════════════════
    #  Cost calculations — delegates to sub-powers
    #  Ported from CompoundPower.java
    # ═══════════════════════════════════════════════════════════

    @property
    def total_cost(self) -> float:
        """Sum of sub-power total costs."""
        d = 0.0
        for obj in self.powers:
            obj.parent = self._parent
            d += obj.total_cost
            obj.parent = None
        return d

    @property
    def active_cost(self) -> float:
        """Calculate the active cost."""


        return self._compute_active_cost()



    def _compute_active_cost(self, exclude_xmlid: str = None) -> float:
        """Sum of sub-power active costs."""
        d = 0.0
        for obj in self.powers:
            obj.parent = self._parent
            d += obj.active_cost
            obj.parent = None
        return d

    @property
    def real_cost_pre_list(self) -> float:
        """Sum of sub-power real costs, plus quantity cost."""
        d = 0.0
        if self._quantity > 1:
            qty_cost = 0
            qty = float(self._quantity)
            while qty > 1.0:
                qty_cost += 5
                qty /= 2.0
            d += float(qty_cost)
        for obj in self.powers:
            obj.parent = self._parent
            d += obj.real_cost_pre_list
            obj.parent = None
        return d

    # ═══════════════════════════════════════════════════════════
    #  Display
    # ═══════════════════════════════════════════════════════════

    @property
    def column2_output(self) -> str:
        """Every sub-power in turn, joined by "plus", behind a cost summary.

        Ported from ``CompoundPower.getColumn2Output(boolean)``
        (CompoundPower.java). A compound power has no line of its own — it is
        the sum of its parts, and HD prints the parts:

            <i>Scaly Skin:</i>  (Total: 18 Active Cost, 18 Real Cost)
            +6 PD, Resistant <b>plus</b> +6 ED, Resistant

        This inherited the default, which is the alias, so all 460 of them in
        the corpus printed the words "Compound Power" and nothing else.

        The awkward part is faithful and deliberate: a sub-power does not
        carry the framework's limitations, but HD PRINTS them on it, so it
        pushes the parent's limitations onto each child, renders, and puts the
        child's own list back. Doing that by copy rather than in place would
        change what the children print, because a modifier reads its parent.
        """
        parent_mods = list(self._parent.assigned_modifiers) if self._parent else []
        ret = ""

        for obj in self.powers:
            original = obj._assigned_modifiers
            borrowed = list(original)
            if _show_common_limitations():
                for mod in parent_mods:
                    from kirby_cost.objects.frameworks import is_multipower
                    if mod.xmlid == "CHARGES" and is_multipower(self._parent):
                        continue
                    generic = mod.xmlid in ("MODIFIER", "CUSTOM_MODIFIER",
                                            "GENERIC_OBJECT")
                    already = GenericObject.find_object_by_id(original, mod.xmlid)
                    if mod.total_value < 0 and (already is None or generic):
                        borrowed.append(mod)
            # Assigning the list REPARENTS what is in it, and the borrowed
            # modifiers belong to the framework, not to this slot. Java
            # restores the child's own list afterwards; that puts the child's
            # modifiers back but leaves the BORROWED ones pointing at the
            # child — and `Modifier.isPrivate()` asks its progenitor what it
            # is, so a pool's private limitation silently became a public one
            # and leaked onto every power rendered after it.
            borrowed_parents = [(m, m.parent) for m in borrowed]
            obj._assigned_modifiers = borrowed
            try:
                if ret.strip():
                    ret += self.list_separator
                ret += obj.get_text_output()
                if self.display_active_cost:
                    ret += f" (Real Cost: {round_half_down(obj.real_cost_pre_list)})"
            finally:
                obj._assigned_modifiers = original
                for mod, owner in borrowed_parents:
                    mod.parent = owner

        if self.display_active_cost:
            ret = (f"(Total: {round_half_up(self.active_cost)} Active Cost, "
                   f"{round_half_up(self.real_cost_pre_list)} Real Cost) " + ret)
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        return ret

    def get_save_xml(self):
        """Serialize compound power including sub-powers."""
        element = self.get_general_save_xml()
        for sub in self.powers:
            sub_elem = sub.save_xml()
            if sub_elem is not None:
                element.append(sub_elem)
        return element

    def affects_characteristics(self) -> bool:
        """Check if any combined power affects characteristics."""
        for power in self.powers:
            if isinstance(power, CharAffectingObject):
                cao = power
                if (cao.str_increase != 0.0 or
                    cao.get_dex_increase() != 0.0 or
                    cao.get_con_increase() != 0.0 or
                    cao.get_body_increase() != 0.0 or
                    cao.get_int_increase() != 0.0 or
                    cao.get_ego_increase() != 0.0 or
                    cao.get_pre_increase() != 0.0 or
                    cao.get_com_increase() != 0.0 or
                    cao.pd_increase != 0.0 or
                    cao.ed_increase != 0.0 or
                    cao.get_spd_increase() != 0.0 or
                    cao.get_rec_increase() != 0.0 or
                    cao.get_end_increase() != 0.0 or
                    cao.get_stun_increase() != 0.0 or
                    cao.get_def_increase() != 0.0 or
                    cao.get_size_increase() != 0.0 or
                    cao.get_running_increase() != 0.0 or
                    cao.get_swimming_increase() != 0.0 or
                    cao.get_leaping_increase() != 0.0):
                    return True
        return False

