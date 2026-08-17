"""
Hero character model class for kirby-cost.

Converted from com.hero.Hero.java

This is the main character model that contains all character data.
"""

from typing import List, Optional, Dict
from pathlib import Path

from kirby_cost.objects.base import GenericObject
from kirby_cost.model.rules import Rules


class Hero:
    """
    Hero character model.
    
    Contains:
    - All character components (powers, skills, characteristics, etc.)
    - Character information (name, appearance, background, etc.)
    - Rules and template references
    - Point totals and calculations
    """
    
    def __init__(self, rules: Optional[Rules] = None):
        """Initialize a new Hero character."""
        # Rules
        self.rules: Rules = rules or Rules()
        
        # Character lists
        self.characteristics: List[GenericObject] = []
        self.skills: List[GenericObject] = []
        self.perks: List[GenericObject] = []
        self.talents: List[GenericObject] = []
        self.maneuvers: List[GenericObject] = []
        self.powers: List[GenericObject] = []
        self.disads: List[GenericObject] = []
        self.equipment: List[GenericObject] = []
        
        # Character information
        self.character_name: str = ""
        self.player_name: str = ""
        self.alternate_identities: str = ""
        self.appearance: str = ""
        self.background: str = ""
        self.personality: str = ""
        self.quote: str = ""
        self.tactics: str = ""
        
        # Physical description
        self.height: float = 78.74  # inches (default ~6'6")
        self._weight: float = 220.46  # pounds (default)
        self.hair_color: str = "Brown"
        self.eye_color: str = "Brown"
        self.gender: str = ""
        
        # Campaign information
        self.campaign_name: str = ""
        self.genre: str = ""
        self.gm: str = ""
        self.role: str = ""
        self.use: str = ""
        
        # Points
        self.base_points: int = self.rules.base_points
        self.disad_points: int = self.rules.disad_points
        self.experience: int = 0
        
        # Notes
        self.notes1: str = ""
        self.notes2: str = ""
        self.notes3: str = ""
        self.notes4: str = ""
        self.notes5: str = ""
        
        # Image data
        self.image_file_name: str = ""
        self.image_file_path: str = ""
        self.image_data: str = ""  # Base64 encoded image data
        
        # File information
        self.save_file: Optional[Path] = None
        self.open_file: Optional[Path] = None
        self.template_path: Optional[str] = None
        self.original_template_id: Optional[str] = None
        
        # State
        self.dirty: bool = False
        self.is_loading: bool = False
        self.last_tab: int = 0

        # Calculated totals
        self._total: float = -999999999999.0
    
    @property
    def characteristics_total(self) -> float:
        """Calculate total cost of characteristics."""
        return sum(char.real_cost for char in self.characteristics)

    @property
    def disads_used(self) -> int:
        """Calculate total disadvantage points used."""
        return sum(int(disad.real_cost) for disad in self.disads)
    
    @property
    def total_points(self) -> float:
        """
        Calculate total character points spent.
        
        Includes:
        - Characteristics
        - Skills
        - Perks
        - Talents
        - Maneuvers
        - Powers
        """
        total = 0.0
        
        # Characteristics
        for char in self.characteristics:
            total += char.real_cost
        
        # Skills
        for skill in self.skills:
            total += skill.real_cost
        
        # Perks
        for perk in self.perks:
            total += perk.real_cost
        
        # Talents
        for talent in self.talents:
            total += talent.real_cost
        
        # Maneuvers
        for maneuver in self.maneuvers:
            total += maneuver.real_cost
        
        # Powers
        for power in self.powers:
            total += power.real_cost
        
        self._total = total
        return total
    
    @property
    def available_points(self) -> float:
        """Calculate available points (base + disads + experience - spent)."""
        spent = self.total_points
        available = (self.base_points + 
                    self.disads_used + 
                    self.experience - 
                    spent)
        return available
    
    @property
    def weight(self) -> float:
        """Get weight in pounds."""
        return self._weight

    @weight.setter
    def weight(self, weight: float) -> None:
        """Set weight in pounds."""
        if self._weight == weight:
            return
        self._weight = weight
        self.dirty = True
    
    def add_power(self, power: GenericObject) -> None:
        """Add a power to the character."""
        self.powers.append(power)
        self.dirty = True
    
    def remove_power(self, power: GenericObject) -> None:
        """Remove a power from the character."""
        if power in self.powers:
            self.powers.remove(power)
            self.dirty = True
    
    def add_skill(self, skill: GenericObject) -> None:
        """Add a skill to the character."""
        self.skills.append(skill)
        self.dirty = True
    
    def remove_skill(self, skill: GenericObject) -> None:
        """Remove a skill from the character."""
        if skill in self.skills:
            self.skills.remove(skill)
            self.dirty = True
    
    def add_characteristic(self, char: GenericObject) -> None:
        """Add a characteristic to the character."""
        self.characteristics.append(char)
    
    def characteristic(self, char_type: int) -> Optional[GenericObject]:
        """
        Get a characteristic by type.
        
        Args:
            char_type: Characteristic type (from CharacteristicType enum)
                1=STR, 2=DEX, 3=CON, 4=INT, 5=EGO, 6=PRE,
                7=OCV, 8=DCV, 9=OMCV, 10=DMCV, 11=SPD,
                12=PD, 13=ED, 14=REC, 15=END, 16=BODY, 17=STUN
            
        Returns:
            The characteristic object, or None if not found
        """
        # Map type to XMLID for lookup
        type_to_xmlid = {
            1: 'STR', 2: 'DEX', 3: 'CON', 4: 'INT', 5: 'EGO', 6: 'PRE',
            7: 'OCV', 8: 'DCV', 9: 'OMCV', 10: 'DMCV', 11: 'SPD',
            12: 'PD', 13: 'ED', 14: 'REC', 15: 'END', 16: 'BODY', 17: 'STUN',
            18: 'RUNNING', 19: 'SWIMMING', 20: 'LEAPING'
        }
        
        xmlid = type_to_xmlid.get(char_type)
        if xmlid:
            for char in self.characteristics:
                if hasattr(char, 'xmlid') and char.xmlid == xmlid:
                    return char
        
        # Fallback to get_type() method
        for char in self.characteristics:
            if hasattr(char, 'type') and char.type == char_type:
                return char
        return None
    
    def remove_characteristic(self, char: GenericObject) -> None:
        """Remove a characteristic from the character."""
        if char in self.characteristics:
            self.characteristics.remove(char)
            self.dirty = True
    
    def add_disad(self, disad: GenericObject) -> None:
        """Add a disadvantage to the character."""
        self.disads.append(disad)
        self.dirty = True
    
    def remove_disad(self, disad: GenericObject) -> None:
        """Remove a disadvantage from the character."""
        if disad in self.disads:
            self.disads.remove(disad)
            self.dirty = True
    
    def mark_edited(self) -> None:
        """Mark character as edited."""
        self.dirty = True
    
    def get_save_xml(self):
        """
        Get XML element for saving this character.
        
        Converted from com.hero.Hero.getSaveXML()
        
        Returns:
            lxml.etree.Element representing the complete character for saving
        """
        from lxml import etree
        import base64
        
        # Create root CHARACTER element
        root = etree.Element("CHARACTER")
        root.set("version", "6.0")
        
        # BASIC_CONFIGURATION
        basic_config = etree.SubElement(root, "BASIC_CONFIGURATION")
        basic_config.set("BASE_POINTS", str(self.base_points))
        basic_config.set("DISAD_POINTS", str(self.disad_points))
        basic_config.set("EXPERIENCE", str(self.experience))
        
        # Export template if set
        if self.template_path:
            basic_config.set("EXPORT_TEMPLATE", self.template_path)
        
        # Rules - if default, just set attribute, otherwise include full rules XML
        if self.rules and self.rules.default:
            basic_config.set("RULES", "Default")
        elif self.rules:
            rules_elem = self.rules.rules_xml
            if rules_elem is not None:
                root.append(rules_elem)
        
        # CHARACTER_INFO
        char_info = etree.SubElement(root, "CHARACTER_INFO")
        char_info.set("CHARACTER_NAME", self.character_name)
        char_info.set("ALTERNATE_IDENTITIES", self.alternate_identities)
        char_info.set("PLAYER_NAME", self.player_name)
        char_info.set("HEIGHT", str(self.height))
        char_info.set("WEIGHT", str(self._weight))
        char_info.set("HAIR_COLOR", self.hair_color)
        char_info.set("EYE_COLOR", self.eye_color)
        char_info.set("CAMPAIGN_NAME", self.campaign_name)
        char_info.set("GENRE", self.genre)
        char_info.set("GM", self.gm)
        
        # Text elements as child elements (not attributes)
        background_elem = etree.SubElement(char_info, "BACKGROUND")
        background_elem.text = self.background
        
        personality_elem = etree.SubElement(char_info, "PERSONALITY")
        personality_elem.text = self.personality
        
        quote_elem = etree.SubElement(char_info, "QUOTE")
        quote_elem.text = self.quote
        
        tactics_elem = etree.SubElement(char_info, "TACTICS")
        tactics_elem.text = self.tactics
        
        campaign_use_elem = etree.SubElement(char_info, "CAMPAIGN_USE")
        campaign_use_elem.text = self.use
        
        appearance_elem = etree.SubElement(char_info, "APPEARANCE")
        appearance_elem.text = self.appearance
        
        notes1_elem = etree.SubElement(char_info, "NOTES1")
        notes1_elem.text = self.notes1
        
        notes2_elem = etree.SubElement(char_info, "NOTES2")
        notes2_elem.text = self.notes2
        
        notes3_elem = etree.SubElement(char_info, "NOTES3")
        notes3_elem.text = self.notes3
        
        notes4_elem = etree.SubElement(char_info, "NOTES4")
        notes4_elem.text = self.notes4
        
        notes5_elem = etree.SubElement(char_info, "NOTES5")
        notes5_elem.text = self.notes5
        
        # CHARACTERISTICS
        chars_elem = etree.SubElement(root, "CHARACTERISTICS")
        for char_obj in self.characteristics:
            if hasattr(char_obj, 'get_save_xml'):
                chars_elem.append(char_obj.get_save_xml())
        
        # SKILLS
        skills_elem = etree.SubElement(root, "SKILLS")
        for skill in self.skills:
            if hasattr(skill, 'get_save_xml'):
                skills_elem.append(skill.get_save_xml())
        
        # PERKS
        perks_elem = etree.SubElement(root, "PERKS")
        for perk in self.perks:
            if hasattr(perk, 'get_save_xml'):
                perks_elem.append(perk.get_save_xml())
        
        # TALENTS
        talents_elem = etree.SubElement(root, "TALENTS")
        for talent in self.talents:
            if hasattr(talent, 'get_save_xml'):
                talents_elem.append(talent.get_save_xml())
        
        # MARTIALARTS
        ma_elem = etree.SubElement(root, "MARTIALARTS")
        for maneuver in self.maneuvers:
            if hasattr(maneuver, 'get_save_xml'):
                ma_elem.append(maneuver.get_save_xml())
        
        # POWERS
        powers_elem = etree.SubElement(root, "POWERS")
        for power in self.powers:
            if hasattr(power, 'get_save_xml'):
                powers_elem.append(power.get_save_xml())
        
        # DISADVANTAGES
        disads_elem = etree.SubElement(root, "DISADVANTAGES")
        for disad in self.disads:
            if hasattr(disad, 'get_save_xml'):
                disads_elem.append(disad.get_save_xml())
        
        # EQUIPMENT
        if self.equipment:
            equip_elem = etree.SubElement(root, "EQUIPMENT")
            for equip in self.equipment:
                if hasattr(equip, 'get_save_xml'):
                    equip_elem.append(equip.get_save_xml())
        
        # IMAGE (if present)
        if self.image_data and self.image_file_name and len(self.image_data) > 0:
            try:
                image_elem = etree.SubElement(root, "IMAGE")
                # Image data should already be base64 encoded
                image_elem.text = etree.CDATA(self.image_data)
                image_elem.set("FileName", self.image_file_name)
                image_elem.set("FilePath", self.image_file_path or "")
            except (etree.LxmlError, ValueError, TypeError):
                # Skip image if encoding fails
                pass
        
        # Template attribute (if built-in)
        if self.original_template_id and self.original_template_id.startswith("builtIn"):
            root.set("TEMPLATE", self.original_template_id)
        
        return root
    
    def save_to_file(self, file_path: str, encoding: str = 'utf-8') -> None:
        """
        Save character to an HDC file.
        
        Args:
            file_path: Path to save the file
            encoding: Character encoding (default: utf-8)
        """
        from lxml import etree
        from pathlib import Path
        
        xml_element = self.get_save_xml()
        
        # Create XML tree with declaration
        tree = etree.ElementTree(xml_element)
        
        # Write to file
        path = Path(file_path)
        with open(path, 'wb') as f:
            tree.write(f, encoding=encoding, xml_declaration=True, pretty_print=True)
        
        # Update save file reference
        self.save_file = path
        self.dirty = False

