"""
Linked modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Linked.java

Linked modifier with extensive custom logic:
- getColumn2Output() - formats linked power name
- getBaseCost() - calculates cost based on linked power's active cost
- getTotalValue() - custom calculation with modifier handling
- included() - validates only powers, checks for available linked powers
- getDialog() - custom dialog with power selection (UI layer)
- getValue() - retrieves linked power object
- setSelectedOption() - sets linked power ID and adjusts base cost
- getOptionVector() - generates list of available powers to link to
"""

from typing import List, Optional
from kirby_cost.engine.xml_attrs import XMLAttr
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.adder import Adder


class Linked(Modifier, xmlid="LINKED"):
    """
    Linked modifier.
    
    Power is linked to another power.
    
    Has extensive custom logic for power selection, cost calculation,
    and validation. Dynamically generates list of available powers to link to.
    """
    
    #: LINKED_ID is the whole point of the modifier — it names the power this
    #: one is linked TO — and it was read and never written. 92 characters
    #: exported their Linked modifiers pointing at nothing, which HD reads back
    #: as unlinked: the discount stays, the link does not. LESSERVALUE joins it
    #: here for the same reason the module docstring gives for LINKED_ID, one
    #: ingest per class, so the pair cannot drift apart again.
    XML_ATTRS = (
        XMLAttr("LINKED_ID", "linked_to_id", "int"),
        XMLAttr("LESSERVALUE", "lesser_value", "float"),
    )

    def __init__(self, element=None):
        """Initialize a Linked modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        self.lesser_value = -0.25
        self.linked_to_id = -1
        # Note: orig_base_cost is inherited from GenericObject and tracked
        # automatically via the base class's base_cost setter. We do not
        # maintain a second copy (the Java port did because Java has no
        # properties — Python can just delegate).

        if element is not None:
            self._init(element)

    @property
    def base_cost(self) -> float:
        """
        Get base cost based on linked power's active cost.

        Returns the stored base cost (``orig_base_cost``) unless the linked
        power is strictly cheaper than the parent, in which case the
        "lesser value" discount (default -0.25) applies.

        Returns:
            -0.25 if the linked power's active cost is cheaper than the
            parent's, otherwise the original base cost.
        """
        orig = self.orig_base_cost
        linked_power = self.value
        if linked_power is None:
            return orig

        parent = self.parent
        if parent is None:
            return orig

        # Can't link to self or another Linked modifier
        if (linked_power.xmlid == parent.xmlid or
                isinstance(linked_power, Linked)):
            self.linked_to_id = -1
            return orig
        
        # Temporarily remove Linked modifiers to calculate active costs
        parent_list = parent.parent
        if parent_list:
            parent.parent = None
        
        parent_linked = None
        linked_power_linked = None
        parent_linked_index = -1
        linked_power_linked_index = -1
        
        # Find and temporarily remove Linked modifiers
        parent_modifiers = parent.assigned_modifiers
        for i, modifier in enumerate(parent_modifiers):
            if modifier.xmlid == self.XMLID:
                parent_linked = modifier
                parent_linked_index = i
                parent_modifiers.remove(modifier)
                break
        
        linked_modifiers = linked_power.assigned_modifiers
        for i, modifier in enumerate(linked_modifiers):
            if modifier.xmlid == self.XMLID:
                linked_power_linked = modifier
                linked_power_linked_index = i
                linked_modifiers.remove(modifier)
                break
        
        # Calculate cost based on which power is cheaper
        cost = self.lesser_value
        if linked_power.active_cost >= parent.active_cost:
            cost = orig

        # Restore Linked modifiers
        if parent_linked is not None and parent_linked_index >= 0:
            parent_modifiers.insert(parent_linked_index, parent_linked)
        if linked_power_linked is not None and linked_power_linked_index >= 0:
            linked_modifiers.insert(linked_power_linked_index, linked_power_linked)
        
        if parent_list:
            parent.parent = parent_list

        return cost

    @base_cost.setter
    def base_cost(self, value: float) -> None:
        """Store a new base cost. Delegates to the base class's field.

        Overriding the getter in a subclass drops the inherited setter, so
        we re-declare it here explicitly. The first write also seeds
        ``orig_base_cost`` (same semantics as ``GenericObject.base_cost``).
        """
        self._base_cost = value
        if self.orig_base_cost == 0.0:
            self.orig_base_cost = value

    @property
    def total_value(self) -> float:
        """
        Get total value with custom calculation.
        
        Returns:
            Total modifier value
        """
        d = self.base_cost
        
        # Add adder costs
        for adder in self.assigned_adders:
            d += adder.double_total()
        
        # Add level costs
        if self._level_value > 0.0:
            d += float(self._levels) / self._level_value * self._level_cost
        
        # Apply advantages
        advantage_sum = 0.0
        for modifier in self.assigned_modifiers:
            if modifier.total_value > 0.0:
                advantage_sum += modifier.total_value
        
        d = d * (1.0 + advantage_sum)
        
        # Apply limitations
        limitation_sum = 0.0
        for modifier in self.assigned_modifiers:
            if modifier.total_value < 0.0:
                limitation_sum += abs(modifier.total_value)
        
        d = d / (1.0 + limitation_sum)
        
        # Apply min/max limits
        if d < self._minimum_cost and self.min_set:
            return self._minimum_cost
        if d > self._max_cost and self.max_set:
            return self._max_cost
        
        return d
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Formats linked power name.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        d = self.total_value
        
        # Handle adders
        for adder in self.assigned_adders:
            if string:
                string = string + "; "
            string = string + adder.alias
        
        # Add input
        if self.input and self.input.strip():
            if string2.strip():
                string2 = string2 + ":  "
            string2 = string2 + self.input
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + ", " + modifier.alias
        
        string2 = string2 + " ("
        
        # Add linked power name
        linked_power = self.value
        if linked_power is None:
            string2 = string2 + "???"
        else:
            power_name = linked_power.name
            if power_name and power_name.strip():
                string2 = string2 + power_name
            else:
                string2 = string2 + linked_power.alias
        
        string2 = string2 + "; "
        
        # Add comments
        if self.comments.strip():
            string2 = string2 + self.comments + "; "
        
        # Add adders string
        if string.strip():
            string2 = string2 + string + "; "
        
        string2 = string2 + self.fraction(d) + ")"
        
        return string2
    
    def included(self, generic_object: GenericObject) -> str:
        """
        Check if this modifier can be applied to the given object.
        
        Args:
            generic_object: The object to check
            
        Returns:
            Empty string if allowed, error message if not
        """
        result = super().included(generic_object)
        if result and result.strip():
            return result
        
        if self.force_allow:
            return result
        
        # Only applies to powers
        from kirby_cost.objects.powers.power import Power
        if not generic_object.is_power and not isinstance(generic_object, Power):
            return f"{self._display} can only be applied to Powers."
        
        # Must have at least one available power to link to
        options = self.option_vector(generic_object)
        if len(options) > 0:
            return ""
        
        return "There are no other abilities on the character that can be Linked to."
    
    @property
    def value(self) -> Optional[GenericObject]:
        """
        Get the linked power object.
        
        Returns:
            Linked power object or None if not found
        """
        # TODO: Would need HeroDesigner.getActiveHero() access
        # For now, return None if linked_to_id is invalid
        self._purify_linked_object()
        
        if self.linked_to_id < 0:
            return None
        
        # TODO: Search through hero's powers and equipment
        # This would require access to HeroDesigner.getActiveHero()
        # For now, return None as placeholder
        return None
    
    def option_vector(self, generic_object: GenericObject) -> List[Adder]:
        """
        Generate list of available powers to link to.
        
        Args:
            generic_object: The power that will have this modifier
            
        Returns:
            List of Adder objects representing available powers
        """
        options = []
        option_ids = []
        
        # TODO: Would need HeroDesigner.getActiveHero() access
        # This method needs to:
        # 1. Iterate through hero's powers
        # 2. Iterate through hero's equipment
        # 3. Check compound powers
        # 4. Exclude invalid targets (self, frameworks, already linked, etc.)
        # 5. Create Adder objects for each valid power
        
        # Placeholder implementation
        return options
    
    @property
    def selected_option(self):
        """Get the selected option."""
        return self._selected_option

    @selected_option.setter
    def selected_option(self, adder: Optional[Adder]) -> None:
        """
        Set selected option (linked power).
        
        Args:
            adder: The adder representing the power to link to
        """
        if adder is not None and adder._id > 0:
            self.linked_to_id = adder._id
        else:
            self.linked_to_id = -1
        
        self._selected_option = adder
        
        if adder is None:
            return
        
        parent = self.parent
        if parent:
            if adder.base_cost > parent.active_cost:
                self.base_cost = self.orig_base_cost
            else:
                self.base_cost = self.lesser_value
    
    def _purify_linked_object(self) -> None:
        """Validate and clean up linked object reference."""
        progenitor = self.progenitor
        if progenitor:
            parent_list = progenitor.parent
            main_power = progenitor.main_power
            
            if ((parent_list and parent_list._id == self.linked_to_id) or
                (main_power and main_power._id == self.linked_to_id)):
                self.linked_to_id = -1
    
    @property
    def limitation(self) -> bool:
        """Check if this is a limitation."""
        return True
    


def is_linked(mod) -> bool:
    """True if ``mod`` is a Linked modifier instance.

    Used by the cost engine to filter Linked modifiers out of advantage/
    limitation stacks — a Linked modifier's value is accounted for directly
    by ``Linked.base_cost`` rather than by the generic modifier-sum path.

    The modifier factory (``Modifier.get_instance``) dynamically imports
    and instantiates ``Linked`` for every xmlid="LINKED" element, so this
    is a straightforward ``isinstance`` check — no xmlid fallback needed.
    """
    return mod is not None and isinstance(mod, Linked)
