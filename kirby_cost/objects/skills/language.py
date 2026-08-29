"""
Language skill class for kirby-cost.

Converted from com.hero.objects.skills.Language.java
"""

from typing import Optional, List, TYPE_CHECKING
from kirby_cost.objects.skills.skill import Skill
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.adder import Adder
from kirby_cost.objects.list import List as FrameworkList
from kirby_cost.util.rounder import round_half_down

if TYPE_CHECKING:
    from kirby_cost.io.hdc_loader import LoadedHero as Hero  # the live hero type
    from kirby_cost.ui.dialog.generic_dialog import GenericDialog


class ChartEntry:
    """Chart entry for language similarities."""
    
    def __init__(self, display: str = "", family: str = ""):
        """Initialize ChartEntry."""
        self._display: str = display
        self.family: str = family
        self.included: bool = True
        self.level1: List[str] = []
        self.level2: List[str] = []
        self.level3: List[str] = []
        self.level4: List[str] = []
    
    @property
    def display(self) -> str:
        """Get display."""
        return self._display
    
    def included(self) -> bool:
        """Check if included."""
        return self.included
    
    def __eq__(self, other):
        """Equality check."""
        if isinstance(other, ChartEntry):
            return self._display == other.display
        return False
    
    def __hash__(self):
        """Hash for set operations."""
        return hash(self._display)


def load_language_chart(provider) -> list:
    """Build the similarity chart from a template provider.

    The chart says which languages are similar to which, and at what distance,
    which is what decides a Language's cost. It is Hero Games' table and it
    lives in the user's own ``.hdt`` under ``<LANGUAGES>``.

    It used to ship as ``kirby_cost/data/language_chart.json`` — 161 KB
    extracted from Main6E.hdt, loaded at import time, and included in the wheel
    via ``package_data``. That was the same mistake as the old
    ``template_6e.json``, wearing a filename that did not look like template
    data, and it survived a repository audit because of it. Removed 2026-08-17.

    Returns [] when the provider offers no chart, which leaves every language
    unrelated to every other — the cost floor, never a discount the character
    has not paid for.
    """
    getter = getattr(provider, "get_language_chart", None)
    if getter is None:
        return []
    chart = []
    for e in getter() or []:
        ce = ChartEntry(display=e.get("display", ""), family=e.get("family", ""))
        ce.level1 = e.get("level1", [])
        ce.level2 = e.get("level2", [])
        ce.level3 = e.get("level3", [])
        ce.level4 = e.get("level4", [])
        chart.append(ce)
    return chart


class Language(Skill, xmlid="LANGUAGES"):
    """Language skill."""

    _roll_based_default = False

    # Populated by the HDC loader from the character's template; see
    # load_language_chart. Empty until then.
    chart: List[ChartEntry] = []
    global_exclude: Optional[str] = None
    number_languages_purchased: int = 0
    
    def __init__(self, xmlid: str = None):
        """Initialize Language."""
        super().__init__(xmlid or Language.XMLID)
        
        self.discounted_by: Optional[str] = None
        self.native_tongue: bool = False
        
        # Default values
        self._display = "Language"
        self._base_cost = 0.0
        self._level_cost = 0.0
        self._level_value = 0.0
        self._minimum_cost = 0.0
        self._minimum_level = 0
        self._alias = "Language"
    
    def _init(self, element) -> None:
        """Initialize from XML element, including native tongue flag."""
        super()._init(element)
        if element is not None:
            native_tongue_str = element.get("NATIVE_TONGUE", "")
            if native_tongue_str:
                self.native_tongue = native_tongue_str.strip().upper().startswith("Y")
        # Folded in from restore_from_save, which ran after _init.
        # One ingest per class; see engine/xml_attrs.py.
        native_tongue_str = element.get("NATIVE_TONGUE", "")
        self.native_tongue = native_tongue_str and native_tongue_str.strip().upper().startswith("Y")

    @property
    def column2_output(self) -> str:
        """Get column 2 output."""
        active_hero = self._get_active_hero()
        
        string = self._alias
        
        if self._name and self._name.strip():
            string = f"<i>{self._name}:</i>  {string}"
        
        if self.input and self.input.strip():
            string = f"{string}:  {self.input}"
        
        if self._selected_option is not None:
            string = f"{string} ({self._selected_option.alias}"
            
            # INT-based roll if using languages as INT skill
            if (active_hero is not None and 
                active_hero.rules.use_languages_as_int_skill()):
                int_char = active_hero.characteristic(5)  # INT
                if int_char is not None:
                    string = f"{string}; {int_char.roll}"
            
            adder_str = self.adder_string
            if adder_str.strip():
                string = f"{string}; {adder_str}"
            
            string = f"{string})"
        else:
            adder_str = self.adder_string
            if adder_str.strip():
                string = f"{string} ({adder_str})"
        
        string = string + self.modifier_string
        
        # END Reserve note (stub - would need END Reserve check and useWG() check)
        # if (self.get_end_usage() > 0 and ...):
        #     string = f"{string} ({'uses END Reserve' if self.use_end_reserve else 'uses Personal END'})"
        
        return string.strip()
    
    def dialog(self, bl: bool = False, bl2: bool = False) -> 'GenericDialog':
        """Get dialog (stub - would need LanguageDialog)."""
        # Would need: from kirby_cost.ui.dialog.language_dialog import LanguageDialog
        # return LanguageDialog(self, bl, bl2)
        raise NotImplementedError("LanguageDialog not yet implemented")
    
    def discounting_language(self, exclude_list: List[str], chart_entry: ChartEntry, active_hero: Optional['Hero'] = None) -> Optional['Language']:
        """Get the language that discounts this one."""
        if active_hero is None:
            active_hero = self._get_active_hero()
        if active_hero is None:
            return None
        
        if self.input is None or not self.input.strip():
            return None
        
        Language.number_languages_purchased = 0
        generic_object = None
        generic_object2 = None
        generic_object3 = None
        generic_object4 = None
        
        # Search through skills
        for skill in active_hero.skills:
            if isinstance(skill, Language):
                Language.number_languages_purchased += 1
                if skill == self:
                    continue
                skill_input = skill.input if hasattr(skill, 'input') else (skill.input if hasattr(skill, 'input') else "")
                if skill_input and skill_input.strip().upper() in exclude_list:
                    continue
                if skill.base_cost < self.base_cost:
                    continue
                if skill_input == self.input:
                    continue
                
                # Check similarity levels
                skill_input_upper = skill_input.strip().upper() if skill_input else ""
                if skill_input_upper in chart_entry.level4:
                    if generic_object4 is None or skill.base_cost > generic_object4.base_cost:
                        generic_object4 = skill
                elif skill_input_upper in chart_entry.level3:
                    if generic_object3 is None or skill.base_cost > generic_object3.base_cost:
                        generic_object3 = skill
                elif skill_input_upper in chart_entry.level2:
                    if generic_object2 is None or skill.base_cost > generic_object2.base_cost:
                        generic_object2 = skill
                elif skill_input_upper in chart_entry.level1:
                    if generic_object is None or skill.base_cost > generic_object.base_cost:
                        generic_object = skill
                else:
                    # Check family
                    family = self.family(skill)
                    if family in chart_entry.family:
                        if generic_object is None or skill.base_cost > generic_object.base_cost:
                            generic_object = skill
            elif isinstance(skill, FrameworkList):
                # Check languages in frameworks
                for obj in skill.objects:
                    if not isinstance(obj, Language):
                        continue
                    Language.number_languages_purchased += 1
                    if obj == self:
                        continue
                    obj_input = obj.input if hasattr(obj, 'input') else (obj.input if hasattr(obj, 'input') else "")
                    if obj_input and obj_input.strip().upper() in exclude_list:
                        continue
                    if obj.base_cost < self.base_cost:
                        continue
                    
                    obj_input_upper = obj_input.strip().upper() if obj_input else ""
                    if obj_input_upper in chart_entry.level4:
                        if generic_object4 is None or obj.base_cost > generic_object4.base_cost:
                            generic_object4 = obj
                    elif obj_input_upper in chart_entry.level3:
                        if generic_object3 is None or obj.base_cost > generic_object3.base_cost:
                            generic_object3 = obj
                    elif obj_input_upper in chart_entry.level2:
                        if generic_object2 is None or obj.base_cost > generic_object2.base_cost:
                            generic_object2 = obj
                    elif obj_input_upper in chart_entry.level1:
                        if generic_object is None or obj.base_cost > generic_object.base_cost:
                            generic_object = obj
                    else:
                        family = self.family(obj)
                        if family in chart_entry.family:
                            if generic_object is None or obj.base_cost > generic_object.base_cost:
                                generic_object = obj
        
        # Return highest level match
        if generic_object4 is not None:
            return generic_object4
        if generic_object3 is not None:
            return generic_object3
        if generic_object2 is not None:
            return generic_object2
        if generic_object is not None:
            return generic_object
        
        return None
    
    def family(self, language: 'Language') -> str:
        """Get family for a language."""
        family = ""
        lang_input = language.input if hasattr(language, 'input') else (language.input if hasattr(language, 'input') else "")
        if not lang_input:
            return ""
        for chart_entry in Language.chart:
            if chart_entry.display.lower() in lang_input.lower().strip():
                family = chart_entry.family
                break
        if not family:
            family = lang_input
        return family
    
    @property
    def real_cost_pre_list(self) -> float:
        """Get real cost before list adjustments."""
        active_hero = None  # Parameter removed — never passed
        if active_hero is None:
            active_hero = self._get_active_hero()
        if active_hero is None:
            # Fall back to _loaded_hero for Language-specific native tongue handling
            active_hero = getattr(self, '_loaded_hero', None)
        if active_hero is None:
            return super().real_cost_pre_list
        
        self.discounted_by = ""
        n = 0
        
        # Native tongue handling
        if self.native_tongue:
            d = 4.0
            for option in self.options:
                if option.xmlid == "IDIOMATIC":
                    d = option.base_cost
                    break
            n = int(self._selected_option.base_cost if 
                   (self._selected_option is not None and 
                    self._selected_option.base_cost < d) else d)
            
            # Literacy adder handling
            literacy_adder = GenericObject.find_object_by_id(self.assigned_adders, "LITERACY")
            if (literacy_adder is not None and 
                isinstance(literacy_adder, Adder) and
                literacy_adder.is_selected and
                (active_hero.rules.native_literacy_free or 
                 active_hero.rules.literacy_free)):
                n = int(n + literacy_adder.total_cost)
        
        d = super().real_cost_pre_list
        
        if self.native_tongue:
            d -= float(n)
            if d < 0.0:
                d = 0.0
        elif (active_hero.rules.literacy_free and
              GenericObject.find_object_by_id(self.assigned_adders, "LITERACY") is not None):
            literacy_adder = GenericObject.find_object_by_id(self.assigned_adders, "LITERACY")
            if (isinstance(literacy_adder, Adder) and
                literacy_adder.is_selected and
                (active_hero.rules.native_literacy_free or 
                 active_hero.rules.literacy_free)):
                d -= literacy_adder.total_cost
            if d < 0.0:
                d = 0.0
        
        # Language similarities handling
        if (d <= 0.0 or 
            not active_hero.rules.language_similarities_used or 
            self.native_tongue):
            # Apply multiplier if allowed
            if (active_hero.rules.multiplier_allowed and 
                self.multiplier != 1.0):
                d *= self.multiplier
                d = round_half_down(d)
            elif (active_hero.rules.multiplier_allowed and 
                  self._parent is not None and 
                  self._parent.multiplier != 1.0):
                d *= self._parent.multiplier
                d = round_half_down(d)
            return d
        
        # Find chart entry
        chart_entry = None
        for entry in Language.chart:
            if entry.display.lower() == self.input.strip().lower():
                chart_entry = entry
                break
        
        if chart_entry is None:
            # Apply multiplier if allowed
            if (active_hero.rules.multiplier_allowed and 
                self.multiplier != 1.0):
                d *= self.multiplier
                d = round_half_down(d)
            elif (active_hero.rules.multiplier_allowed and 
                  self._parent is not None and 
                  self._parent.multiplier != 1.0):
                d *= self._parent.multiplier
                d = round_half_down(d)
            return d
        
        # Get discounting language
        exclude_list = []
        if Language.global_exclude and Language.global_exclude.strip():
            exclude_list.append(Language.global_exclude)
        
        language = self.discounting_language(exclude_list, chart_entry, active_hero)
        
        if (language is not None and 
            language.base_cost == self.base_cost and
            (Language.global_exclude is None or not Language.global_exclude.strip())):
            self.discounted_by = language.input
            Language.global_exclude = ""
        
        if Language.number_languages_purchased <= 1:
            # Apply multiplier if allowed
            if (active_hero.rules.multiplier_allowed and 
                self.multiplier != 1.0):
                d *= self.multiplier
                d = round_half_down(d)
            elif (active_hero.rules.multiplier_allowed and 
                  self._parent is not None and 
                  self._parent.multiplier != 1.0):
                d *= self._parent.multiplier
                d = round_half_down(d)
            return d
        
        bl2 = False
        if language is not None:
            self.discounted_by = language.input if hasattr(language, 'input') else (language.input if hasattr(language, 'input') else "")
            language_family = self.family(language)
            self_family = self.family(self)
            lang_input = language.input if hasattr(language, 'input') else (language.input if hasattr(language, 'input') else "")
            language_input_upper = lang_input.strip().upper() if lang_input else ""
            
            if language_input_upper in chart_entry.level4:
                bl2 = True
                discount = language.base_cost / 2.0
                d -= round_half_down(discount) if discount > 1.0 else 0.0
            elif language_input_upper in chart_entry.level3:
                d -= 1.0
            elif language_input_upper in chart_entry.level2:
                d -= 1.0
            elif language_input_upper in chart_entry.level1:
                pass  # No discount
            elif language_family.lower() == self_family.lower():
                pass  # No discount
        elif (d >= 1.0 and 
              chart_entry is not None and 
              active_hero.rules.penalize_no_level1() and
              not self.native_tongue_exists_in_group(chart_entry, active_hero)):
            d += 1.0
        
        bl = False
        if bl2:
            bl = False
        if d < float(bl):
            d = float(bl)
        
        # Apply multiplier if allowed
        if (active_hero.rules.multiplier_allowed and 
            self.multiplier != 1.0):
            d *= self.multiplier
            d = round_half_down(d)
        elif (active_hero.rules.multiplier_allowed and 
              self._parent is not None and 
              self._parent.multiplier != 1.0):
            d *= self._parent.multiplier
            d = round_half_down(d)
        
        return d
    
    @property
    def roll(self) -> str:
        """Get roll (empty for languages)."""
        return ""
    
    def get_save_xml(self):
        """Get save XML."""
        element = super().get_save_xml()
        element.attrib.pop("CHARACTERISTIC", None)
        element.set("NATIVE_TONGUE", "Yes" if self.native_tongue else "No")
        return element
    
    
    def native_tongue_exists_in_group(self, chart_entry: ChartEntry, active_hero: Optional['Hero'] = None) -> bool:
        """Check if native tongue exists in group."""
        if active_hero is None:
            active_hero = self._get_active_hero()
        if active_hero is None:
            return False
        
        Language.number_languages_purchased = 0
        if self.input is None or not self.input.strip():
            return False
        
        for skill in active_hero.skills:
            if not isinstance(skill, Language):
                continue
            Language.number_languages_purchased += 1
            skill_input = skill.input if hasattr(skill, 'input') else (skill.input if hasattr(skill, 'input') else "")
            if skill_input == self.input or not skill.native_tongue:
                continue
            
            skill_input_upper = skill_input.strip().upper() if skill_input else ""
            if (skill_input_upper in chart_entry.level4 or
                skill_input_upper in chart_entry.level3 or
                skill_input_upper in chart_entry.level2 or
                skill_input_upper in chart_entry.level1):
                return True
        
        return False
    
    def native_tongue_selected(self, active_hero: Optional['Hero'] = None) -> bool:
        """Check if native tongue is selected."""
        if active_hero is None:
            active_hero = self._get_active_hero()
        if active_hero is None:
            return False
        
        Language.number_languages_purchased = 0
        for skill in active_hero.skills:
            if not isinstance(skill, Language):
                continue
            Language.number_languages_purchased += 1
            if skill.native_tongue:
                return True
        
        return False
    
    

