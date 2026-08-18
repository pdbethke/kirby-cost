"""
Charges modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Charges.java

Charges modifier with extensive custom logic for charge management,
clips, recoverable charges, and charge display formatting.
"""

from typing import Optional, List
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Charges(Modifier, xmlid="CHARGES"):
    """
    Charges modifier.
    
    Power has limited charges.
    
    This modifier has complex logic that needs to be fully implemented
    based on the Java source code.
    """
    
    def __init__(self, element=None):
        """Initialize a Charges modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        self.clips_level = 1
        self.clips_multiplier = 2
        self.clips_advantage_multiplier = 4
        self.boostable_level = 1
        self.recoverable_level = 1
        self.refresh_on_update = False
        self.current_levels = 0
        self.avail_ads = []
        self.last_call = 0
        
        if element is not None:
            self._init(element)
            # Parse additional attributes
            from kirby_cost.io.xml_utility import XMLUtility
            clips_level = XMLUtility.get_value(element, "CLIPSLEVEL")
            if clips_level:
                try:
                    self.clips_level = int(clips_level)
                except (ValueError, TypeError):
                    pass
            
            clips_mult = XMLUtility.get_value(element, "CLIPSMULTIPLIER")
            if clips_mult:
                try:
                    self.clips_multiplier = int(clips_mult)
                except (ValueError, TypeError):
                    pass
    
    def get_save_xml(self):
        """Charges, plus the price of its CLIPS adder.

        CLIPS_COST is not a field on the modifier — it is the base cost of the
        CLIPS adder hanging off it, which HD hoists onto the parent so that a
        restore can put it back before the adder is recosted
        (``Charges.getSaveXML``/``restoreFromSave``). Nothing here wrote it, so
        9 characters exported clips priced at whatever the template says
        instead of what the character paid.

        Declared as code rather than in XML_ATTRS because there is no field to
        declare: the value lives on a child.
        """
        element = super().get_save_xml()
        clips = GenericObject.find_object_by_id(self.assigned_adders, "CLIPS")
        if clips is not None:
            element.set("CLIPS_COST", str(clips.base_cost))
        return element

    def _init(self, element) -> None:
        """Read the document, then put CLIPS_COST back onto the CLIPS adder."""
        super()._init(element)
        if element is None:
            return
        from kirby_cost.io.xml_utility import XMLUtility

        cost = XMLUtility.get_value(element, "CLIPS_COST")
        if not (cost and cost.strip()):
            return
        clips = GenericObject.find_object_by_id(self.assigned_adders, "CLIPS")
        if clips is not None:
            try:
                clips.base_cost = float(cost)
            except (ValueError, TypeError):
                pass

    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.

        Complex formatting for Charges modifier with many adder types.
        """
        self.validation_check()  # Would need to implement this
        
        string = ""
        string2 = ""
        string3 = ""
        string4 = ""
        string5 = ""
        string6 = ""
        string7 = ""
        string8 = ""
        string9 = ""
        
        # Check if multiple charges (not 1)
        bl = True
        if self._selected_option is not None:
            try:
                n = int(self._selected_option.alias)
                bl = n != 1
            except (ValueError, TypeError):
                pass
        
        d = self.total_value
        
        # Process adders
        for adder in self.assigned_adders:
            if adder.xmlid == "CLIPS":
                string = adder.alias + " of"
            elif adder.xmlid == "CONTINUING":
                string4 = adder.alias
                if bl:
                    sel_opt = adder.selected_option
                    string5 = "lasting " + (sel_opt.alias if sel_opt else "???") + " each"
                else:
                    sel_opt = adder.selected_option
                    string5 = "lasting " + (sel_opt.alias if sel_opt else "???")
            elif adder.xmlid == "FUEL":
                string6 = adder.alias
            elif adder.xmlid == "BOOSTABLE":
                string2 = adder.alias
            elif adder.xmlid == "RECOVERABLE":
                string3 = adder.alias
            elif adder.xmlid == "INCREASEDTIME":
                sel_opt = adder.selected_option
                if bl:
                    string7 = "which Recover every " + (sel_opt.alias if sel_opt else "???")
                else:
                    string7 = "which Recovers every " + (sel_opt.alias if sel_opt else "???")
            elif adder.xmlid == "NEVERRECOVER":
                string7 = "which Never Recover"
                if not bl:
                    string7 = string7 + "s"
            elif adder.display_in_string:
                if string8:
                    string8 = string8 + "; "
                string8 = string8 + adder.alias
                if adder.selected_option and adder.selected_option.alias.strip():
                    string8 = string8 + ": " + adder.selected_option.alias.strip()
        
        # Build output string
        string9 = string
        string9 = string9.strip()
        
        if self._selected_option is not None:
            string9 = string9 + " " + self._selected_option.alias
        
        string9 = string9 + " " + string2
        string9 = string9.strip()
        string9 = string9 + " " + string3
        string9 = string9.strip()
        string9 = string9 + " " + string4
        string9 = string9.strip()
        string9 = string9 + " " + string6
        string9 = string9.strip()
        
        # Handle singular/plural
        alias = self._alias
        if bl or not alias.strip().upper().endswith("S"):
            string9 = string9 + " " + alias
        else:
            string9 = string9 + " " + alias[:-1]  # Remove 's'
        
        string9 = string9.strip()
        string9 = string9 + " " + string5
        string9 = string9.strip()
        string9 = string9 + " " + string7
        string9 = string9.strip()
        
        # Add input
        if self.input and self.input.strip():
            if string9.strip():
                string9 = string9 + ":  "
            string9 = string9 + self.input
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string9 = string9 + ", " + modifier.alias
        
        string9 = string9 + " ("
        
        if string8.strip():
            string9 = string9 + string8 + "; "
        
        if self.comments.strip():
            string9 = string9 + self.comments + "; "
        
        string9 = string9 + self.fraction(d) + ")"
        
        return string9
    
    @property
    def level_cost(self) -> float:
        """Charges doesn't use level cost."""
        return 0.0

    @level_cost.setter
    def level_cost(self, value) -> None:
        self._level_cost = value
    
    @property
    def level_value(self) -> float:
        """Charges uses -1.0 for level value."""
        return -1.0

    @level_value.setter
    def level_value(self, value) -> None:
        self._level_value = value
    
    @property
    def total_value(self) -> float:
        """
        Get total value of this modifier.
        
        Sets max cost based on whether parent uses END and if CONTINUING is present.
        """
        if self.parent is None:
            return 0.0
        
        bl = False
        d = 1.0
        
        # Check if parent uses END
        if not self._parent_uses_end():
            d = 0.0
            bl = True
        
        # Add BOOSTABLE cost
        boostable = GenericObject.find_object_by_id(
            self.assigned_adders, "BOOSTABLE")
        if boostable is not None:
            d += boostable.total_cost
        
        # Check for CONTINUING
        if GenericObject.find_object_by_id(
            self.assigned_adders, "CONTINUING") is None:
            bl = True
        
        # Set max cost
        if bl:
            self.max_set = True
            self._max_cost = d
        else:
            self.max_set = False
        
        self.min_set = False
        
        # Calculate total using base method
        d2 = super().total_value
        return d2
    
    def _parent_uses_end(self) -> bool:
        """Check if parent uses END."""
        if self.parent is None:
            return False
        
        # Check for LINGERING modifier
        if GenericObject.find_object_by_id(
            self.parent.assigned_modifiers, "LINGERING") is not None:
            return False
        
        parent = self.parent

        # A framework reserve never uses END itself — its slots do — so Java
        # asks them instead of the container (Charges.java:450-470):
        #
        #     if (parent instanceof com.hero.objects.List) {
        #         for (GenericObject o : list.getObjects())
        #             if (childUsesEND(o)) return true;
        #         return false;
        #     }
        #
        # Without this a Multipower reserve always answered "no", which sets
        # max = 0 in total_value and clamps the modifier away entirely — see
        # tests/test_framework_holds_its_slots.py.
        from kirby_cost.objects.list import List as _List
        if isinstance(parent, _List):
            return any(o.uses_end for o in parent.objects)

        # Clone parent and remove Charges to check END usage
        # For now, simplified check
        return parent.uses_end if parent else False
    
    def validation_check(self) -> None:
        """Perform validation checks (stub for now)."""
        pass
    
    @property
    def limitation_modifier(self) -> bool:
        """Charges is always a limitation."""
        return True
