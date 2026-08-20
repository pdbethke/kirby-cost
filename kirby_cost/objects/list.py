"""
List class for Hero Designer frameworks.

Converted from com.hero.objects.List.java

Base class for power frameworks: Multipower, VPP, Elemental Control.
"""

from typing import List as ListType, Optional
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.rounder import round_up
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.adder import Adder


class List(GenericObject):
    """
    Base class for power frameworks (Multipower, VPP, Elemental Control).
    
    Handles:
    - Contained objects (powers in the framework)
    - Private modifiers and adders (framework-only)
    - Child cost calculations
    - Object validation
    """
    
    def __init__(self):
        """Initialize a List."""
        super().__init__()
        self._objects: ListType[GenericObject] = []
        self._private_mods: ListType[Modifier] = []
        self._private_adders: ListType[Adder] = []
        self._object_size_check: int = -1
        self.error: Optional[str] = None
    
    @property
    def objects(self) -> ListType[GenericObject]:
        """Get the list of objects in this framework."""
        if self._objects is None:
            self._objects = []
        # Cleanup if size changed
        if len(self._objects) != self._object_size_check:
            self._cleanup_objects()
            self._object_size_check = len(self._objects)
        return self._objects
    
    def _cleanup_objects(self) -> None:
        """Remove duplicate objects based on ID."""
        seen_ids = set()
        to_remove = []
        for i, obj in enumerate(self._objects):
            if obj._id in seen_ids:
                to_remove.append(i)
            else:
                seen_ids.add(obj._id)
        # Remove in reverse order to maintain indices
        for i in reversed(to_remove):
            self._objects.pop(i)
    
    def add_object(self, obj: GenericObject) -> None:
        """Add an object to this framework."""
        # Check if object already exists (by ID)
        for i, existing in enumerate(self._objects):
            if existing._id == obj._id and obj._id > 1:
                self._objects[i] = obj
                return
        self._objects.append(obj)
    
    def remove_object(self, obj: GenericObject) -> None:
        """Remove an object from this framework."""
        self._objects = [o for o in self._objects if o._id != obj._id]
        self._update_child_positions()
    
    @objects.setter
    def objects(self, objects: ListType[GenericObject]) -> None:
        """Set the list of objects."""
        self._objects = objects
    
    @property
    def modifier_string(self) -> str:
        """``; all slots Extra Time (Full Phase, -1/2)`` — a framework's line.

        Ported from ``List.getModifierString`` (List.java:501). A framework
        holds two kinds of modifier and says so: the ones PRIVATE to the
        reserve, which apply to the pool itself, and the public ones, which
        every slot inherits — and HD labels the second kind "all slots" so a
        reader can tell which is which. This class had no modifier_string, so
        it used GenericObject's, which knows about neither and printed the
        two groups as one undifferentiated list.

        The active-point note sits between the advantages and the limitations,
        as it does everywhere, and the whole thing is prefixed with ", " only
        if anything came out at all.
        """
        # Java splits these into two LISTS at load time
        # (`List.separatePrivateMods`) and its cost methods then sum both. Our
        # cost methods read `assigned_modifiers` alone, so moving them breaks
        # 68 oracle fixtures — the partition happens here instead, where only
        # the display can see it. Same question, asked at the point of use.
        every = list(self.assigned_modifiers) + list(self.private_mods)
        public = sorted((m for m in every if not m.private),
                        key=lambda m: m.total_value)
        # REVERSED. Java's separatePrivateMods walks the assigned list from the
        # back and appends what it removes, so privateMods ends up in reverse
        # document order — and the sort that follows is stable, so for two
        # modifiers of equal value that reversal is what decides which prints
        # first. A VPP with Zero-Phase and No Skill Roll, both +1, reads
        # "No Skill Roll Required (+1), Powers Can Be Changed..." for exactly
        # this reason.
        private = sorted((m for m in reversed(every) if m.private),
                         key=lambda m: m.total_value)

        def split(mods):
            adv = lim = ""
            for m in mods:
                if m.total_value >= 0:
                    if adv.strip():
                        adv += ", "
                    adv += m.column2_output
                else:
                    if lim.strip():
                        lim += ", "
                    lim += m.column2_output
            return adv, lim

        public_adv, public_lim = split(public)
        private_adv, private_lim = split(private)

        ret = ""
        if private_adv.strip():
            ret += private_adv
        if public_adv.strip():
            if ret.strip():
                ret += "; "
            ret += "all slots " + public_adv
        if self.display_active_cost and (
                self.active_cost != self.total_cost
                or self.real_cost != self.total_cost):
            ret += f" ({round_up(self.active_cost)} Active Points)"
        if private_lim.strip():
            if ret.strip():
                ret += "; "
            ret += private_lim
        if public_lim.strip():
            if ret.strip():
                ret += "; "
            ret += "all slots " + public_lim
        if ret.strip():
            ret = ", " + ret
        return ret

    @property
    def private_mods(self) -> ListType[Modifier]:
        """Get private modifiers (framework-only)."""
        if self._private_mods is None:
            self._private_mods = []
        return self._private_mods
    
    @property
    def private_adders(self) -> ListType[Adder]:
        """Get private adders (framework-only)."""
        if self._private_adders is None:
            self._private_adders = []
        return self._private_adders
    
    def _separate_private_mods(self) -> None:
        """Separate private modifiers from assigned modifiers."""
        private = []
        assigned = []
        for mod in self.assigned_modifiers:
            if mod.private:
                private.append(mod)
            else:
                assigned.append(mod)
        self._assigned_modifiers = assigned
        self._private_mods = private
    
    def _separate_private_adders(self) -> None:
        """Separate private adders from assigned adders."""
        private = []
        assigned = []
        for adder in self.assigned_adders:
            if adder.private:
                private.append(adder)
            else:
                assigned.append(adder)
        self._assigned_adders = assigned
        self._private_adders = private
    
    def real_cost_for_child(self, child: GenericObject) -> float:
        """
        Calculate real cost for a child object in this framework.
        
        Base implementation: adds framework adders to child, calculates cost.
        Subclasses override for framework-specific calculations.
        """
        # Save child's original adders
        original_adders = list(child.assigned_adders)
        
        # Add framework adders temporarily
        combined_adders = list(original_adders)
        combined_adders.extend(self.assigned_adders)
        child.assigned_adders = combined_adders
        
        # Calculate real cost
        real_cost = child.real_cost_pre_list
        
        # Restore original adders
        child.assigned_adders = original_adders
        
        return real_cost
    
    @property
    def active_cost(self) -> float:
        """Calculate the active cost."""

    
        return self._compute_active_cost()


    
    def _compute_active_cost(self, exclude_xmlid: str = None) -> float:
        """
        Calculate active cost for this framework.
        
        Includes private modifiers in the calculation.
        """
        total_cost = self.total_cost
        modifier_sum = 0.0
        has_advantages = False
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            if exclude_xmlid and modifier.xmlid == exclude_xmlid:
                continue
            if modifier.total_value > 0.0:
                modifier_sum += modifier.total_value
                has_advantages = True
        
        # Add private modifiers
        for modifier in self.private_mods:
            if exclude_xmlid and modifier.xmlid == exclude_xmlid:
                continue
            # Skip LINKED modifiers from private mods
            if modifier.xmlid == "LINKED":
                continue
            if modifier.total_value > 0.0:
                modifier_sum += modifier.total_value
                has_advantages = True
        
        # Calculate active cost
        active_cost = total_cost * (1.0 + modifier_sum)
        if has_advantages:
            from kirby_cost.util.rounder import round_half_down
            active_cost = round_half_down(active_cost)
        
        return active_cost
    
    @property
    def real_cost_pre_list(self) -> float:
        """
        Calculate real cost for this framework.
        
        Includes private modifiers in the calculation.
        """
        active_cost = self.active_cost
        limitation_sum = 0.0
        has_limitations = False
        
        # Add assigned limitations
        for modifier in self.assigned_modifiers:
            if modifier.total_value < 0.0:
                limitation_sum += modifier.total_value  # Negative value
                has_limitations = True
        
        # Add private limitations
        for modifier in self.private_mods:
            if modifier.total_value < 0.0:
                limitation_sum += modifier.total_value
                has_limitations = True
        
        # Calculate real cost
        from kirby_cost.util.rounder import round_half_down
        real_cost = active_cost / (1.0 + abs(limitation_sum))
        if has_limitations:
            real_cost = round_half_down(real_cost)
        
        # Minimum real cost
        if (real_cost < 1.0 and 
            (active_cost > 0.0 or 
             (self._levels > 0 and len(self.assigned_adders) == 0 and 
              self.base_cost >= 0.0))):
            real_cost = 1.0
        
        # Apply multiplier (stub - requires rules access)
        # if rules.multiplier_allowed() and self.multiplier != 1.0:
        #     real_cost *= self.multiplier
        #     real_cost = round_half_down(real_cost)
        
        # Quantity cost
        if self._quantity > 1:
            quantity_cost = 0
            qty = float(self._quantity)
            while qty > 1.0:
                quantity_cost += 5
                qty /= 2.0
            real_cost += float(quantity_cost)
        
        return real_cost
    
    def _update_child_positions(self) -> None:
        """Update child object positions (sorting)."""
        # Remove None objects
        self._objects = [o for o in self._objects if o is not None]
        # Sort by position
        self._objects.sort(key=lambda o: o.position)
    
    def column2_prefix(self, obj: GenericObject) -> str:
        """Get prefix for column 2 output (position number)."""
        self._update_child_positions()
        pos = obj.position - self.position
        if pos < 10:
            return f"{pos})  "
        return f"{pos}) "
    
    def column2_suffix(self, obj: GenericObject) -> str:
        """Get suffix for column 2 output."""
        return ""
    
    def column1_suffix(self, obj: GenericObject) -> str:
        """Get suffix for column 1 output."""
        return ""
    
    def object_allowed(self, obj: GenericObject, show_warnings: bool = True) -> bool:
        """
        Check if an object can be added to this framework.
        
        Base implementation checks:
        - Object allows modifiers
        - Not a List
        - Not a VPP
        - Modifier compatibility
        
        Subclasses override for framework-specific validation.
        """
        if not self._alias or not self._alias.strip():
            self.error = ""
            return False
        
        # Check if object allows modifiers
        if not obj.allows_other_modifiers and len(self.assigned_modifiers) > 0:
            self.error = f"{obj.alias} is not allowed to have Modifiers assigned to it in its current configuration.\n\n{obj.alias} will be placed outside of the list."
            return False
        
        # Cannot add Lists
        if isinstance(obj, List):
            self.error = "You cannot add a List into another List.  New list will be placed outside of selection."
            return False
        
        # Cannot add VPPs. The isinstance(obj, List) check above already
        # catches VariablePowerPool instances (VPP is a List subclass), but
        # the HDC loader sometimes produces a bare _FallbackObject with
        # xmlid="VPP"; is_vpp() handles both paths. Once the loader is
        # refactored to instantiate real framework classes, this branch
        # collapses into the isinstance(obj, List) check above.
        from kirby_cost.objects.frameworks import is_vpp
        if is_vpp(obj):
            self.error = "You cannot add a VPP into a List.  The Variable Power Pool will be placed outside of the selection."
            return False
        
        # Check modifier compatibility (stub - would check modifier intelligence)
        # This would validate that framework modifiers can be applied to the object
        
        return True
    
    @property
    def rejection_message(self) -> str:
        """Get the rejection message if object was not allowed."""
        if self.error:
            return self.error
        return "You cannot add a List into another List.  New list will be placed outside of selection."
