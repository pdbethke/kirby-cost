"""
KnowledgeSkill skill class for kirby-cost.

Converted from com.hero.objects.skills.KnowledgeSkill.java
"""

from typing import Optional, List, TYPE_CHECKING
from kirby_cost.objects.skills.skill import Skill
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.constants import characteristic_string

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero
    from kirby_cost.ui.dialog.generic_dialog import GenericDialog


class KnowledgeSkill(Skill, xmlid="KNOWLEDGE_SKILL"):
    """Knowledge Skill."""
    
    def __init__(self, xmlid: str = None):
        """Initialize KnowledgeSkill."""
        super().__init__(xmlid or KnowledgeSkill.XMLID)

        # KS class defaults: level_cost=1 (cheaper than standard Skill's 2)
        self._level_cost = 1.0
        self._minimum_cost = 1.0

        # Knowledge skill type fields — display names match Main6E.hdt template
        # (GROUPS DISPLAY="General", PEOPLE DISPLAY="Cultural", etc.)
        self.groups_display: str = "General"
        self.groups_type: str = "KNOWLEDGE"
        self.groups_examples: List[str] = []
        self.groups_available: bool = True

        self.people_display: str = "Cultural"
        self.people_type: str = "AREA"
        self.people_examples: List[str] = []
        self.people_available: bool = True

        self.places_display: str = "Area"
        self.places_type: str = "AREA"
        self.places_examples: List[str] = []
        self.places_available: bool = True

        self.things_display: str = "City"
        self.things_type: str = "AREA"
        self.things_examples: List[str] = []
        self.things_available: bool = True

        self.selected_type: str = "KNOWLEDGE"
        self.selected_display: str = "General"
        
        # Default values
        self._display = "Knowledge Skill"
        self._alias = "KS"
        self._base_cost = 2.0
        self._level_cost = 1.0
        self._level_value = 1.0
        self._minimum_cost = 1.0
        self._minimum_level = 8
        self.characteristic = 0
    
    def _init(self, element) -> None:
        """Initialize from XML element, including TYPE for selected_type."""
        super()._init(element)
        # ONCE. Folded in from restore_from_save, which used to run after
        # _init -- but the fold left BOTH calls in place, and this setter is
        # not idempotent.
        #
        # `selected_type_by_display` decides whether to rewrite `display` by
        # asking whether the CURRENT selected type already matches the alias
        # (KnowledgeSkill.java:491-503). On the first call the type is still
        # the default, so the answer is no and the template's display stands.
        # The second call then finds the type it just set, agrees with the
        # alias, and overwrites "Knowledge Skill" with "CuK". Java calls it
        # exactly once, from restoreFromSave (:464-470).
        if element is not None:
            type_str = element.get("TYPE", "")
            if type_str and type_str.strip():
                self.selected_type_by_display(type_str)

    @property
    def column2_output(self) -> str:
        """Get column 2 output."""
        active_hero = self._get_active_hero()
        
        if self.levels_only:
            return self._get_level_only_output()
        
        string2 = self._alias
        
        if self._name and self._name.strip():
            string2 = f"<i>{self._name}:</i>  {string2}"
        
        if self.input and self.input.strip():
            string2 = f"{string2}: {self.input}"
        
        if self._selected_option is not None:
            string2 = f"{string2}: {self._selected_option.alias}"
        
        # Characteristic-based note (stub - would need HeroDesigner.getInstance().getPrefs().useWG() check)
        if (self.characteristic_choices and 
            len(self.characteristic_choices) > 1 and 
            self.characteristic != 0):
            string2 = f"{string2} ({characteristic_string(self.characteristic)}-based)"
        
        adder_str = self.adder_string
        if adder_str.strip():
            string2 = f"{string2} ({adder_str})"
        
        string2 = string2 + self.modifier_string
        
        if self.show_roll:
            string2 = f"{string2} {self.roll}"
        
        # END Reserve note (stub - would need END Reserve check and useWG() check)
        # if (self.get_end_usage() > 0 and ...):
        #     string2 = f"{string2} ({'uses END Reserve' if self.use_end_reserve else 'uses Personal END'})"
        
        return string2
    
    def dialog(self, bl: bool = False, bl2: bool = False) -> 'GenericDialog':
        """Get dialog (stub - would need KnowledgeSkillDialog)."""
        # Would need: from kirby_cost.ui.dialog.knowledge_skill_dialog import KnowledgeSkillDialog
        # return KnowledgeSkillDialog(self, bl, bl2)
        raise NotImplementedError("KnowledgeSkillDialog not yet implemented")
    
    @property
    def examples(self) -> List[str]:
        """Get examples list."""
        if self.selected_display == self.groups_display:
            if len(self.groups_examples) > 0:
                return list(self.groups_examples)
        elif self.selected_display == self.people_display:
            if len(self.people_examples) > 0:
                return list(self.people_examples)
        elif self.selected_display == self.places_display:
            if len(self.places_examples) > 0:
                return list(self.places_examples)
        elif self.selected_display == self.things_display:
            if len(self.things_examples) > 0:
                return list(self.things_examples)
        
        return super().examples if hasattr(super(), 'examples') else []
    
    def get_save_xml(self):
        """Get save XML."""
        element = super().get_save_xml()
        element.set("TYPE", self.selected_display)
        return element
    
    @property
    def types(self) -> List[str]:
        """Get types list."""
        types_list = [self.selected_type]
        
        uoo_modifier = GenericObject.find_object_by_id(self.all_assigned_modifiers, "UOO")
        if (uoo_modifier is not None and 
            uoo_modifier.selected_option is not None and
            uoo_modifier.selected_option.xmlid == "UAA"):
            types_list.append("ATTACK")
        
        return types_list
    
    
    def selected_type_by_display(self, display: str) -> None:
        """Set selected type by display string."""
        bl = False
        string2 = self._alias
        
        if display.upper() in ("GROUPS", "GENERAL"):
            display = self.groups_display
        elif display.upper() in ("PEOPLE", "CULTURAL"):
            display = self.people_display
        elif display.upper() in ("PLACES", "AREA"):
            display = self.places_display
        elif display.upper() in ("THINGS", "CITY"):
            display = self.things_display
        
        if (self.selected_type == self.groups_type and string2 == "KS"):
            bl = True
        elif (self.selected_type == self.people_type and string2 == "CuK"):
            bl = True
        elif (self.selected_type == self.places_type and string2 == "AK"):
            bl = True
        elif (self.selected_type == self.things_type and string2 == "CK"):
            bl = True
        elif string2 == self._display:
            bl = True
        
        self.selected_display = display
        
        if display == self.groups_display:
            self.selected_type = self.groups_type
            if bl:
                self._alias = "KS"
                self._display = "KS"
        elif display == self.people_display:
            self.selected_type = self.people_type
            if bl:
                self._alias = "CuK"
                self._display = "CuK"
        elif display == self.places_display:
            self.selected_type = self.places_type
            if bl:
                self._alias = "AK"
                self._display = "AK"
        elif display == self.things_display:
            self.selected_type = self.things_type
            if bl:
                self._alias = "CK"
                self._display = "CK"
    



