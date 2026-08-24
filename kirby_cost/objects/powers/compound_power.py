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
        return self._column2(include_names=True)

    @property
    def nameless_column2_output(self) -> str:
        """``CompoundPower.getNamelessColumn2Output`` (CompoundPower.java:389).

        Java blanks its OWN name and renders the children NAMELESS too:
        `getColumn2Output(false)` calls `getNamelessColumn2Output()` on each
        child where the named form calls `getTextOutput()`. Inheriting the
        base class's version printed every child's `<i>Name:</i>` prefix, so
        an .hde export carried names Hero Designer omits.
        """
        return self._column2(include_names=False)

    def _column2(self, *, include_names: bool) -> str:
        """``getColumn2Output(boolean)`` (CompoundPower.java:198)."""
        parent_mods = list(self._parent.assigned_modifiers) if self._parent else []
        ret = ""

        for obj in self.powers:
            original = obj._assigned_modifiers
            borrowed = list(original)
            if _show_common_limitations():
                for mod in parent_mods:
                    # Java reads getParentList().getAssignedModifiers(), and a
                    # List has already MOVED its private modifiers out of that
                    # list (List.separatePrivateMods) -- so they are not there
                    # to borrow. This engine keeps both in one list and skips
                    # at the point of use, as modifier_string and both cost
                    # borrow loops already do. Without it, Doctor Yin Wu's
                    # pool-private "Only For Chinese Magic" was applied to the
                    # sub-powers of every Compound Power in the pool, and it
                    # divided their printed Real Cost: 13 for HD's 17.
                    if getattr(mod, "private", False):
                        continue
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
                if include_names:
                    ret += obj.get_text_output()
                else:
                    # A property on some classes, a zero-argument method on
                    # others; this engine is not consistent about it.
                    nameless = obj.nameless_column2_output
                    ret += nameless() if callable(nameless) else nameless
                if self.display_active_cost:
                    ret += f" (Real Cost: {round_half_down(obj.real_cost_pre_list)})"
            finally:
                obj._assigned_modifiers = original
                for mod, owner in borrowed_parents:
                    mod.parent = owner

        if self.display_active_cost:
            ret = (f"(Total: {round_half_up(self.active_cost)} Active Cost, "
                   f"{round_half_up(self.real_cost_pre_list)} Real Cost) " + ret)
        if include_names and self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        return ret

    @property
    def end_usage(self) -> int:
        """The children's END, summed (CompoundPower.java:295-303).

        A compound power has no active cost of its own, so the inherited
        Power.end_usage computed END from zero and always answered 0. Java
        sums the parts, and it temporarily reparents each child onto the
        compound's OWN parent list first -- a child's END consults its
        parent's modifiers, and the framework above the compound is the one
        that should have that say.
        """
        total = 0
        for obj in self.powers:
            original = obj.parent
            obj.parent = self._parent
            try:
                total += obj.end_usage
            finally:
                obj.parent = original
        return total

    @property
    def column3_output(self) -> str:
        """``CompoundPower.getColumn3Output`` (CompoundPower.java:253-286).

        As Power's rule, except the Charges modifier is looked for across the
        CHILDREN -- the container carries none itself -- and the first child
        that has one decides.
        """
        from kirby_cost.objects.base import GenericObject
        usage = self.end_usage
        if usage > 0:
            return str(usage)
        charges = None
        for obj in self.powers:
            found = GenericObject.find_object_by_id(obj.assigned_modifiers, "CHARGES")
            if found is not None:
                charges = found
                break
        if charges is None:
            return "0"
        option = getattr(charges, "selected_option", None)
        count = (getattr(option, "alias", "") or "") if option else ""
        for adder_id, suffix in (("BOOSTABLE", " bc"), ("RECOVERABLE", " rc"),
                                 ("CONTINUING", " cc"), ("NEVERRECOVER", " nr")):
            if GenericObject.find_object_by_id(charges.assigned_adders, adder_id) is not None:
                return f"[{count}{suffix}]"
        return f"[{count}]"

    @property
    def types(self) -> list:
        """Every child's types, gathered (CompoundPower.java:506-512).

        A compound power has no type of its own; it is whatever its parts
        are. HTMLWriter.filterByType branches on this, so a compound holding
        a Detect must answer SENSORY -- inheriting the base's own (empty)
        list printed no `sensory_power` where Hero Designer prints one.
        """
        gathered = []
        for obj in self.powers:
            gathered.extend(obj.types or ())
        return gathered

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

