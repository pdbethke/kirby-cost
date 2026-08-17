"""
Rules class for kirby-cost.

Converted from com.hero.Rules.java

Manages campaign rules and settings.
"""

from typing import Optional, Dict


class Rules:
    """
    Rules engine for kirby-cost.
    
    Manages:
    - Base points and disadvantage points
    - AP per END
    - Equipment settings
    - Maximum values
    - Validation rules
    """
    
    # Response constants
    IGNORE = 0
    WARN = 1
    DONOTALLOW = 2
    
    def __init__(self):
        """Initialize Rules with defaults."""
        # Point totals
        self.base_points: int = 400  # Default superheroic
        self.disad_points: int = 75  # Default
        
        # END settings
        self.ap_per_end: int = 10  # 6E default
        self.str_ap_per_end: int = 5  # STR END cost
        
        # Equipment
        self.equipment_allowed: bool = True
        
        # NCM (Normal Characteristic Maxima)
        self.ncm_selected: bool = False
        self.ncm_user_changeable: bool = True
        
        # Maximum values
        self.attack_ap_max_value: int = 999
        self.attack_ap_max_response: int = Rules.IGNORE
        self.defense_ap_max_value: int = 999
        self.defense_ap_max_response: int = Rules.IGNORE
        self.characteristic_max_value: int = 999
        self.characteristic_max_response: int = Rules.IGNORE
        
        # Framework settings
        self.link_across_framework: int = Rules.WARN
        self.special_type_in_framework: int = Rules.WARN
        
        # Other settings
        self._multiplier_allowed: bool = True
        self.standard_effect_allowed: bool = True
        self.default_standard_effect: bool = False
        self._language_similarities_used: bool = False  # Java default is false
        
        # Skill settings
        self.skill_roll_base: int = 9
        self.skill_roll_denominator: float = 5.0
        self.char_roll_base: int = 9
        self.char_roll_denominator: float = 5.0
        self.use_skill_maxima: bool = False
        self.skill_maxima_limit: int = 20
        self.general_level: int = 10  # Default general characteristic level
        
        # Characteristic maxima
        self.characteristic_maxima: Dict[str, int] = {}
    
    @property
    def multiplier_allowed(self) -> bool:
        """Check if multipliers are allowed."""
        return self._multiplier_allowed
    
    def use_default(self) -> None:
        """Use default rules (6E Superheroic)."""
        self.base_points = 400
        self.disad_points = 75
        self.ap_per_end = 10
        self.str_ap_per_end = 5
        self.equipment_allowed = True
        self.ncm_selected = False
        self._multiplier_allowed = True
        self.standard_effect_allowed = True
        self._is_default = True
    
    @property
    def default(self) -> bool:
        """Check if using default rules."""
        return getattr(self, '_is_default', True)
    
    @property
    def native_literacy_free(self) -> bool:
        """Check if native tongue literacy is free (6E: True)."""
        return True

    @property
    def literacy_free(self) -> bool:
        """Check if all literacy is free (6E: True)."""
        return True

    @property
    def language_similarities_used(self) -> bool:
        """Check if language similarity discounts are used (default: False)."""
        return self._language_similarities_used

    def penalize_no_level1(self) -> bool:
        """Check if penalty applies when no level-1 similarity language exists (6E: False)."""
        return False

    def use_languages_as_int_skill(self) -> bool:
        """Check if languages use INT-based skill rolls (6E: False)."""
        return False

    @property
    def rules_xml(self):
        """
        Get XML element for saving custom rules.
        
        Returns:
            lxml.etree.Element representing the rules, or None if default
        """
        if self.default:
            return None
        
        from lxml import etree
        
        element = etree.Element("RULES")
        element.set("BASE_POINTS", str(self.base_points))
        element.set("DISAD_POINTS", str(self.disad_points))
        element.set("AP_PER_END", str(self.ap_per_end))
        element.set("STR_AP_PER_END", str(self.str_ap_per_end))
        element.set("EQUIPMENT_ALLOWED", "Yes" if self.equipment_allowed else "No")
        element.set("NCM_SELECTED", "Yes" if self.ncm_selected else "No")
        element.set("MULTIPLIER_ALLOWED", "Yes" if self._multiplier_allowed else "No")
        element.set("STANDARD_EFFECT_ALLOWED", "Yes" if self.standard_effect_allowed else "No")
        element.set("SKILL_ROLL_BASE", str(self.skill_roll_base))
        element.set("SKILL_ROLL_DENOMINATOR", str(self.skill_roll_denominator))
        element.set("CHAR_ROLL_BASE", str(self.char_roll_base))
        element.set("CHAR_ROLL_DENOMINATOR", str(self.char_roll_denominator))
        element.set("USE_SKILL_MAXIMA", "Yes" if self.use_skill_maxima else "No")
        element.set("SKILL_MAXIMA_LIMIT", str(self.skill_maxima_limit))
        
        return element

