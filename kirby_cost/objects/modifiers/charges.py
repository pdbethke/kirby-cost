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
        
        string9 = string9 + self.get_fraction(d) + ")"
        
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
            return any(self._child_uses_end(o) for o in parent.objects)
        # Java strips THIS Charges out of the parent's list before asking the
        # computed usesEND() -- otherwise Charges forces its own answer to
        # False (Charges.java:466-476: clone, remove by xmlid, ask, restore).
        # Then: no END under the campaign's rules means no END to save
        # (:475-477).
        # Swap in a NEW list via the setter rather than mutating in place --
        # Charges.total_value runs while the cost aggregation is ITERATING
        # the parent's modifier list, and Java's clone-assign-restore
        # (setAssignedModifiers with a clone, original reference restored)
        # leaves a live iterator untouched. An in-place remove/append here
        # corrupted that iteration and double-counted Charges.
        orig = parent.assigned_modifiers
        me = GenericObject.find_object_by_id(orig, self.xmlid)
        parent.assigned_modifiers = [m for m in orig if m is not me]
        try:
            ret = parent.uses_end
        finally:
            parent.assigned_modifiers = orig
        if ret:
            from kirby_cost.core.context import EngineContext
            hero = EngineContext.active_hero()
            if hero is not None and getattr(hero, "rules", None) is not None:
                ret = hero.rules.ap_per_end > 0
        # Charges.java:478-500 re-checks COSTSEND/REDUCEDEND over the parent's
        # own + parent-list modifiers; the computed usesEND() already folds
        # both in. Its ElementalControl negative-mods-only carve-out is
        # 5E-only under Main6E and is not ported.
        return ret

    @staticmethod
    def _child_uses_end(child) -> bool:
        """Charges.java:76-99 (childUsesEND): a LINGERING child never uses
        END; otherwise detach the child from its List, strip CHARGES from its
        own modifiers, ask the computed usesEND(), restore everything."""
        if GenericObject.find_object_by_id(
                child.assigned_modifiers, "LINGERING") is not None:
            return False
        orig = child.assigned_modifiers
        parent = child.parent
        child.parent = None
        child.assigned_modifiers = [m for m in orig if m.xmlid != "CHARGES"]
        try:
            return child.uses_end
        finally:
            child.parent = parent
            child.assigned_modifiers = orig
    
    def validation_check(self) -> None:
        """Perform validation checks (stub for now)."""
        pass
    
    @property
    def limitation_modifier(self) -> bool:
        """Charges is always a limitation."""
        return True

    @property
    def is_limitation(self) -> bool:
        """Always True.

        Java overrides ``isLimitation`` on this modifier rather than inferring
        it, because the general rule gets it wrong: the value can sit at or
        above zero and it is still a limitation. Charges is the one that shows —
        "8 Continuing Charges lasting 1 Turn each (+0)" is worth nothing and
        still belongs after the semicolon.
        """
        return True
