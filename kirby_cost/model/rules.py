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
        #: NOT the figure to read -- use `get_str_ap_per_end()`. This is the
        #: stored value, which Rules.java defaults to 10 (:858, :861, :1951);
        #: the 5 applies only under a heroic template. It was hardcoded 5 here.
        self.str_ap_per_end: int = 10
        
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
        
        # Damage differentiation. Rules.java:1992 (useDefault) and
        # Rules.java:1237-1242 (parse) both settle on False unless the RULES
        # element says "Y" -- HD's own default is off.
        self.use_increased_damage_differentiation_flag: bool = False

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
        self.str_ap_per_end = 10   # Rules.java:1951
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
        """Whether literacy costs nothing for ANY language.

        FALSE. HD's 6E defaults are `literacyFree = false` alongside
        `nativeLiteracyFree = true` (Rules.java:1985) — a character reads their
        own language for nothing and pays for every other one. This returned
        True with a docstring asserting "6E: True", so every non-native
        language with a Literacy adder came out a point cheap, and a character
        with one such language was a point light overall.
        """
        return False

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

    def get_str_ap_per_end(self, active_hero=None) -> int:
        """Active Points per END for STR. ``Rules.getSTRAPPerEND`` (:616-634).

        **5 under a heroic template, 10 otherwise** -- and only when the rules
        are otherwise default. Java tests the active template's id, and every
        parent template's id, for "Heroic" or "Normal".

        The case matters: `indexOf("Heroic")` does NOT match
        "Superheroic6E", whose h is lower case. So Bokor on Heroic6E pays
        STR/5 and Ravel on Superheroic6E pays STR/10 -- which is exactly what
        Hero Designer prints for them, and what this engine got wrong for
        every superheroic character by storing a flat 5.
        """
        template_id = ""
        if active_hero is not None:
            template_id = (getattr(active_hero, "original_template_id", None)
                           or getattr(active_hero, "template_name", "") or "")
        if "Heroic" in template_id or "Normal" in template_id:
            return 5
        return self.str_ap_per_end

    def use_increased_damage_differentiation(self) -> bool:
        """Whether leftover STR resolves to half-dice and pips.

        ``Rules.useIncreasedDamageDifferentiation()`` (Rules.java:2018).

        With it OFF, a STR that is not a multiple of 5 simply loses the
        remainder. With it ON, a remainder of 3 becomes a half-die and 4
        becomes the next die less one -- see
        ``Strength.hth_damage_string``, whose ON branch this makes reachable
        for the first time.

        Java parses it from the character's RULES element and defaults to
        False when the element is absent or does not begin with "Y"
        (Rules.java:1237-1242); ``useDefault()`` sets the same (Rules.java:1992).

        THIS METHOD DID NOT EXIST until 2026-08-24, and
        ``Strength.hth_damage_string`` -- its only caller -- raised
        AttributeError every time it was reached. Nothing reached it, because
        nothing ever instantiated Strength.
        """
        return self.use_increased_damage_differentiation_flag

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

