"""
HDC Parser for Hero Designer Character files.

HDC (Hero Designer Character) files are UTF-16 encoded XML files containing
complete character builds for the Hero System.

Converted from Java XML parsing logic in Hero Designer.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
from lxml import etree
from kirby_cost.io.xml_utility import XMLUtility


class HDCParser:
    """
    Parser for Hero Designer Character (.hdc) files.
    
    HDC files are UTF-16 encoded XML with the following structure:
    
    <CHARACTER version="6.0">
      <BASIC_CONFIGURATION BASE_POINTS="400" DISAD_POINTS="75" EXPERIENCE="0"/>
      <CHARACTER_INFO CHARACTER_NAME="..." PLAYER_NAME="..."/>
      <CHARACTERISTICS>...</CHARACTERISTICS>
      <POWERS>...</POWERS>
      <SKILLS>...</SKILLS>
      <COMPLICATIONS>...</COMPLICATIONS>
    </CHARACTER>
    """
    
    def __init__(self):
        """Initialize the HDC parser."""
        self.xml_utility = XMLUtility()
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse an HDC file and return a dictionary of character data.
        
        Args:
            file_path: Path to the .hdc file
            
        Returns:
            Dictionary containing parsed character data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            etree.XMLSyntaxError: If the XML is malformed
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"HDC file not found: {file_path}")
        
        # HDC files can be UTF-16 or UTF-8 encoded
        # Detect encoding and line ending style from file
        with open(path, 'rb') as f:
            raw_data = f.read()
        
        # Detect encoding from BOM
        if raw_data[:2] == b'\xff\xfe':  # UTF-16 LE BOM
            encoding = 'UTF-16-LE'
            bom = 'le'
        elif raw_data[:2] == b'\xfe\xff':  # UTF-16 BE BOM
            encoding = 'UTF-16-BE'
            bom = 'be'
        elif raw_data[:4] == b'<\x00?\x00':  # UTF-16 LE without BOM
            encoding = 'UTF-16LE'
            bom = 'le'
        elif raw_data[:4] == b'\x00<\x00?':  # UTF-16 BE without BOM
            encoding = 'UTF-16BE'
            bom = 'be'
        else:
            encoding = 'UTF-8'
            bom = None
        
        # Detect line ending style
        # For UTF-16, check for CRLF (0d 00 0a 00 for LE, 00 0d 00 0a for BE)
        if 'UTF-16' in encoding:
            if bom == 'le':
                has_crlf = b'\r\x00\n\x00' in raw_data
            else:
                has_crlf = b'\x00\r\x00\n' in raw_data
        else:
            has_crlf = b'\r\n' in raw_data
        
        # Let lxml auto-detect encoding from XML declaration when possible
        try:
            # First try: let lxml auto-detect from XML declaration
            tree = etree.parse(path)
        except etree.XMLSyntaxError:
            # Fallback: try with explicit encoding
            tree = etree.parse(path, parser=etree.XMLParser(encoding=encoding.replace('-', '')))
        
        root = tree.getroot()
        
        # HDC files use <CHARACTER>; HDP "prefab" files (e.g. HSEG-style
        # equipment libraries) use <PREFAB> but are structurally identical
        # (same children: BASIC_CONFIGURATION, CHARACTER_INFO, POWERS, ...).
        # Accept either so prefab equipment files parse via this code path.
        if root.tag not in ("CHARACTER", "PREFAB"):
            raise ValueError(
                f"Invalid HDC/HDP file: root element must be CHARACTER or "
                f"PREFAB, found {root.tag}"
            )
        
        # Store detected encoding and line ending style in the result
        result = self._parse_character(root)
        result['_encoding'] = encoding
        result['_bom'] = bom
        result['_crlf'] = has_crlf
        return result
    
    def _parse_character(self, root: etree.Element) -> Dict[str, Any]:
        """Parse the CHARACTER root element."""
        character = {
            'version': root.get('version', '6.0'),
            'template': root.get('TEMPLATE', ''),
            'basic_configuration': self._parse_basic_configuration(root),
            'character_info': self._parse_character_info(root),
            'image': self._parse_image(root),
            'characteristics': self._parse_characteristics(root),
            'powers': self._parse_powers(root),
            'skills': self._parse_skills(root),
            'complications': self._parse_complications(root),
            'perks': self._parse_perks(root),
            'talents': self._parse_talents(root),
            'martial_arts': self._parse_martial_arts(root),
            'equipment': self._parse_equipment(root),
            'rules': self._parse_rules(root),
        }
        return character
    
    def _parse_rules(self, root: etree.Element) -> Optional[Dict[str, str]]:
        """Parse RULES section (stores all attributes as-is)."""
        rules_elem = root.find('RULES')
        if rules_elem is None:
            return None
        return dict(rules_elem.attrib)
    
    def _parse_basic_configuration(self, root: etree.Element) -> Dict[str, Any]:
        """Parse BASIC_CONFIGURATION section."""
        config_elem = root.find('BASIC_CONFIGURATION')
        if config_elem is None:
            return {}
        
        config = {
            'base_points': float(config_elem.get('BASE_POINTS', '0')),
            'disad_points': float(config_elem.get('DISAD_POINTS', '0')),
            'experience': float(config_elem.get('EXPERIENCE', '0')),
            'rules': config_elem.get('RULES'),  # None if not present
            'export_template': config_elem.get('EXPORT_TEMPLATE', ''),
        }
        
        # Parse NCM (Non-Combat Movement) if present
        ncm_elem = config_elem.find('NCM')
        if ncm_elem is not None:
            config['ncm'] = {
                'xmlid': ncm_elem.get('XMLID', ''),
                'levels': int(ncm_elem.get('LEVELS', '0')),
            }
        
        return config
    
    def _parse_adders_recursive(self, parent_elem: etree.Element) -> List[Dict[str, Any]]:
        """
        Parse ADDER elements recursively (since adders can contain nested adders).
        
        Args:
            parent_elem: The parent element to search for ADDER children
            
        Returns:
            List of adder data dictionaries
        """
        adders = []
        for adder_elem in parent_elem.findall('ADDER'):
            adder_data = {
                'xmlid': adder_elem.get('XMLID', ''),
                'attributes': dict(adder_elem.attrib),
            }
            adder_data['basecost'] = float(adder_elem.get('BASECOST', '0'))
            adder_data['levels'] = int(adder_elem.get('LEVELS', '0'))
            
            # Parse NOTES subelement
            notes_elem = adder_elem.find('NOTES')
            if notes_elem is not None:
                adder_data['notes'] = notes_elem.text.strip() if notes_elem.text else ''
                adder_data['has_notes'] = True
            else:
                adder_data['notes'] = ''
                adder_data['has_notes'] = False
            
            # Recursively parse nested adders
            adder_data['adders'] = self._parse_adders_recursive(adder_elem)
            
            adders.append(adder_data)
        return adders
    
    def _parse_character_info(self, root: etree.Element) -> Dict[str, Any]:
        """Parse CHARACTER_INFO section."""
        info_elem = root.find('CHARACTER_INFO')
        if info_elem is None:
            return {}
        
        info = {
            'character_name': info_elem.get('CHARACTER_NAME', ''),
            'player_name': info_elem.get('PLAYER_NAME', ''),
            'alternate_identities': info_elem.get('ALTERNATE_IDENTITIES', ''),
            'height': info_elem.get('HEIGHT', ''),
            'weight': info_elem.get('WEIGHT', ''),
            'hair_color': info_elem.get('HAIR_COLOR', ''),
            'eye_color': info_elem.get('EYE_COLOR', ''),
            'campaign_name': info_elem.get('CAMPAIGN_NAME', ''),
            'genre': info_elem.get('GENRE', ''),
            'gm': info_elem.get('GM', ''),
        }
        
        # Parse optional text elements (even if empty - Hero Designer preserves them)
        background = info_elem.find('BACKGROUND')
        if background is not None:
            info['background'] = background.text.strip() if background.text else ''
        
        personality = info_elem.find('PERSONALITY')
        if personality is not None:
            info['personality'] = personality.text.strip() if personality.text else ''
        
        quote = info_elem.find('QUOTE')
        if quote is not None:
            info['quote'] = quote.text.strip() if quote.text else ''
        
        tactics = info_elem.find('TACTICS')
        if tactics is not None:
            info['tactics'] = tactics.text.strip() if tactics.text else ''
        
        campaign_use = info_elem.find('CAMPAIGN_USE')
        if campaign_use is not None:
            info['campaign_use'] = campaign_use.text.strip() if campaign_use.text else ''
        
        appearance = info_elem.find('APPEARANCE')
        if appearance is not None:
            info['appearance'] = appearance.text.strip() if appearance.text else ''
        
        # Parse notes
        for i in range(1, 6):
            notes_elem = info_elem.find(f'NOTES{i}')
            if notes_elem is not None:
                info[f'notes{i}'] = notes_elem.text.strip() if notes_elem.text else ''
        
        return info
    
    def _parse_image(self, root: etree.Element) -> Dict[str, Any]:
        """Parse IMAGE section."""
        image_elem = root.find('IMAGE')
        if image_elem is None:
            return {}
        
        image_data = {
            'file_name': image_elem.get('FileName', ''),
            'file_path': image_elem.get('FilePath', ''),
        }
        
        # Image data is base64 encoded in the element text
        if image_elem.text:
            image_data['data'] = image_elem.text.strip()
        
        return image_data
    
    def _parse_characteristics(self, root: etree.Element) -> List[Dict[str, Any]]:
        """Parse CHARACTERISTICS section."""
        chars_elem = root.find('CHARACTERISTICS')
        if chars_elem is None:
            return []
        
        characteristics = []
        for char_elem in chars_elem:
            char_data = {
                'xmlid': char_elem.get('XMLID', ''),
                'tag': char_elem.tag,
                'attributes': dict(char_elem.attrib),  # Preserve all attributes
            }
            
            # Parse common attributes for easy access
            char_data['levels'] = int(char_elem.get('LEVELS', '0'))
            char_data['id'] = char_elem.get('ID', '')
            
            # Parse NOTES subelement (even if empty)
            notes_elem = char_elem.find('NOTES')
            if notes_elem is not None:
                char_data['notes'] = notes_elem.text.strip() if notes_elem.text else ''
                char_data['has_notes'] = True
            else:
                char_data['notes'] = ''
                char_data['has_notes'] = False
            
            characteristics.append(char_data)
        
        return characteristics
    
    def _parse_powers(self, root: etree.Element) -> List[Dict[str, Any]]:
        """Parse POWERS section."""
        powers_elem = root.find('POWERS')
        if powers_elem is None:
            return []
        
        powers = []
        for power_elem in powers_elem:
            power_data = self._parse_power_element(power_elem)
            powers.append(power_data)
        
        return powers
    
    def _parse_power_element(self, elem: etree.Element) -> Dict[str, Any]:
        """Parse a single power element (can be POWER, MULTIPOWER, VPP, etc.)."""
        power_data = {
            'xmlid': elem.get('XMLID', ''),
            'tag': elem.tag,
        }
        
        # Store ALL attributes (preserve original case for round-trip compatibility)
        power_data['attributes'] = dict(elem.attrib)
        
        # Parse common attributes for easy access
        power_data['levels'] = int(elem.get('LEVELS', '0'))
        power_data['alias'] = elem.get('ALIAS', '')
        power_data['display'] = elem.get('DISPLAY', '')
        power_data['id'] = elem.get('ID', '')
        power_data['parentid'] = elem.get('PARENTID', '')
        
        # Parse NOTES subelement (even if empty - Hero Designer preserves it)
        notes_elem = elem.find('NOTES')
        if notes_elem is not None:
            power_data['notes'] = notes_elem.text.strip() if notes_elem.text else ''
            power_data['has_notes'] = True
        else:
            power_data['notes'] = ''
            power_data['has_notes'] = False
        
        # Parse modifiers (preserve all attributes)
        modifiers = []
        for mod_elem in elem.findall('MODIFIER'):
            mod_data = {
                'xmlid': mod_elem.get('XMLID', ''),
                'attributes': dict(mod_elem.attrib),
            }
            # Parse common attributes for easy access
            mod_data['basecost'] = float(mod_elem.get('BASECOST', '0'))
            mod_data['levels'] = int(mod_elem.get('LEVELS', '0'))
            # Parse NOTES subelement
            notes_elem = mod_elem.find('NOTES')
            if notes_elem is not None:
                mod_data['notes'] = notes_elem.text.strip() if notes_elem.text else ''
                mod_data['has_notes'] = True
            else:
                mod_data['notes'] = ''
                mod_data['has_notes'] = False
            # Parse nested adders in modifier (recursively)
            mod_data['adders'] = self._parse_adders_recursive(mod_elem)
            modifiers.append(mod_data)
        power_data['modifiers'] = modifiers
        
        # Parse adders (recursively)
        power_data['adders'] = self._parse_adders_recursive(elem)
        
        # Parse nested powers (for frameworks and compound powers)
        # This includes POWER, framework types, and characteristics (STR, DEX, PD, ED, etc.)
        nested_powers = []
        excluded_tags = ['NOTES', 'MODIFIER', 'ADDER']  # Already handled above
        for nested_elem in elem:
            if nested_elem.tag not in excluded_tags:
                nested_powers.append(self._parse_power_element(nested_elem))
        power_data['nested_powers'] = nested_powers
        
        return power_data
    
    def _parse_skills(self, root: etree.Element) -> List[Dict[str, Any]]:
        """Parse SKILLS section."""
        skills_elem = root.find('SKILLS')
        if skills_elem is None:
            return []
        
        skills = []
        for skill_elem in skills_elem:
            skill_data = {
                'xmlid': skill_elem.get('XMLID', ''),
                'tag': skill_elem.tag,
                'attributes': dict(skill_elem.attrib),  # Preserve all attributes
            }
            
            # Parse common attributes for easy access
            skill_data['characteristic'] = skill_elem.get('CHARACTERISTIC', '')
            skill_data['levels'] = int(skill_elem.get('LEVELS', '0'))
            skill_data['id'] = skill_elem.get('ID', '')
            
            # Parse NOTES subelement (even if empty)
            notes_elem = skill_elem.find('NOTES')
            if notes_elem is not None:
                skill_data['notes'] = notes_elem.text.strip() if notes_elem.text else ''
                skill_data['has_notes'] = True
            else:
                skill_data['notes'] = ''
                skill_data['has_notes'] = False
            
            # Parse modifiers
            modifiers = []
            for mod_elem in skill_elem.findall('MODIFIER'):
                mod_data = {
                    'xmlid': mod_elem.get('XMLID', ''),
                    'attributes': dict(mod_elem.attrib),
                }
                mod_data['basecost'] = float(mod_elem.get('BASECOST', '0'))
                modifiers.append(mod_data)
            skill_data['modifiers'] = modifiers
            
            # Parse adders (recursively, since adders can contain nested adders)
            skill_data['adders'] = self._parse_adders_recursive(skill_elem)
            
            skills.append(skill_data)
        
        return skills
    
    def _parse_complications(self, root: etree.Element) -> List[Dict[str, Any]]:
        """Parse COMPLICATIONS or DISADVANTAGES section."""
        # HDC files can use either COMPLICATIONS or DISADVANTAGES
        comps_elem = root.find('COMPLICATIONS') or root.find('DISADVANTAGES')
        if comps_elem is None:
            return []
        
        complications = []
        for comp_elem in comps_elem:
            comp_data = {
                'xmlid': comp_elem.get('XMLID', ''),
                'name': comp_elem.get('NAME', ''),
                'tag': comp_elem.tag,
                'attributes': dict(comp_elem.attrib),  # Preserve all attributes
            }
            
            # Parse common attributes for easy access
            comp_data['id'] = comp_elem.get('ID', '')
            
            # Parse NOTES subelement (even if empty)
            notes_elem = comp_elem.find('NOTES')
            if notes_elem is not None:
                comp_data['notes'] = notes_elem.text.strip() if notes_elem.text else ''
                comp_data['has_notes'] = True
            else:
                comp_data['notes'] = ''
                comp_data['has_notes'] = False
            
            # Parse adders (recursively)
            comp_data['adders'] = self._parse_adders_recursive(comp_elem)

            # Parse modifiers — VULNERABILITY's MULTIPLIER (TWICEBODY/
            # ONEANDAHALFBODY) and similar mechanics live here. Was
            # previously dropped during parse, leaving the engine
            # blind to vulnerability damage multipliers.
            modifiers = []
            for mod_elem in comp_elem.findall('MODIFIER'):
                mod_data = {
                    'xmlid': mod_elem.get('XMLID', ''),
                    'attributes': dict(mod_elem.attrib),
                    'basecost': float(mod_elem.get('BASECOST', '0')),
                }
                # Modifiers can carry their own ADDERs (rare but
                # legal in HD). Capture them too.
                mod_adders = self._parse_adders_recursive(mod_elem)
                if mod_adders:
                    mod_data['adders'] = mod_adders
                modifiers.append(mod_data)
            comp_data['modifiers'] = modifiers

            complications.append(comp_data)

        return complications
    
    def _parse_perks(self, root: etree.Element) -> List[Dict[str, Any]]:
        """Parse PERKS section."""
        perks_elem = root.find('PERKS')
        if perks_elem is None:
            return []
        
        perks = []
        for perk_elem in perks_elem:
            perk_data = {
                'xmlid': perk_elem.get('XMLID', ''),
                'tag': perk_elem.tag,
                'attributes': dict(perk_elem.attrib),  # Preserve all attributes
            }
            
            # Parse common attributes for easy access
            perk_data['levels'] = int(perk_elem.get('LEVELS', '0'))
            perk_data['id'] = perk_elem.get('ID', '')
            
            # Parse NOTES subelement
            notes_elem = perk_elem.find('NOTES')
            if notes_elem is not None:
                perk_data['notes'] = notes_elem.text.strip() if notes_elem.text else ''
                perk_data['has_notes'] = True
            else:
                perk_data['notes'] = ''
                perk_data['has_notes'] = False
            
            # Parse modifiers and adders (perks can have them)
            modifiers = []
            for mod_elem in perk_elem.findall('MODIFIER'):
                mod_data = {
                    'xmlid': mod_elem.get('XMLID', ''),
                    'attributes': dict(mod_elem.attrib),
                }
                mod_data['basecost'] = float(mod_elem.get('BASECOST', '0'))
                modifiers.append(mod_data)
            perk_data['modifiers'] = modifiers
            
            perk_data['adders'] = self._parse_adders_recursive(perk_elem)
            
            perks.append(perk_data)
        
        return perks
    
    def _parse_talents(self, root: etree.Element) -> List[Dict[str, Any]]:
        """Parse TALENTS section."""
        talents_elem = root.find('TALENTS')
        if talents_elem is None:
            return []
        
        talents = []
        for talent_elem in talents_elem:
            talent_data = {
                'xmlid': talent_elem.get('XMLID', ''),
                'tag': talent_elem.tag,
                'attributes': dict(talent_elem.attrib),  # Preserve all attributes
            }
            
            # Parse common attributes for easy access
            talent_data['levels'] = int(talent_elem.get('LEVELS', '0'))
            talent_data['id'] = talent_elem.get('ID', '')
            
            # Parse NOTES subelement
            notes_elem = talent_elem.find('NOTES')
            if notes_elem is not None:
                talent_data['notes'] = notes_elem.text.strip() if notes_elem.text else ''
                talent_data['has_notes'] = True
            else:
                talent_data['notes'] = ''
                talent_data['has_notes'] = False
            
            # Parse modifiers and adders
            modifiers = []
            for mod_elem in talent_elem.findall('MODIFIER'):
                mod_data = {
                    'xmlid': mod_elem.get('XMLID', ''),
                    'attributes': dict(mod_elem.attrib),
                }
                mod_data['basecost'] = float(mod_elem.get('BASECOST', '0'))
                modifiers.append(mod_data)
            talent_data['modifiers'] = modifiers
            
            talent_data['adders'] = self._parse_adders_recursive(talent_elem)
            
            talents.append(talent_data)
        
        return talents
    
    def _parse_martial_arts(self, root: etree.Element) -> List[Dict[str, Any]]:
        """Parse MARTIALARTS section."""
        # Note: HDC uses MARTIALARTS (no underscore), not MARTIAL_ARTS
        ma_elem = root.find('MARTIALARTS')
        if ma_elem is None:
            return []
        
        martial_arts = []
        for ma_elem_item in ma_elem:
            ma_data = {
                'xmlid': ma_elem_item.get('XMLID', ''),
                'tag': ma_elem_item.tag,
                'attributes': dict(ma_elem_item.attrib),  # Preserve all attributes
            }
            
            # Parse common attributes for easy access
            ma_data['levels'] = int(ma_elem_item.get('LEVELS', '0'))
            ma_data['id'] = ma_elem_item.get('ID', '')
            
            # Parse NOTES subelement
            notes_elem = ma_elem_item.find('NOTES')
            if notes_elem is not None:
                ma_data['notes'] = notes_elem.text.strip() if notes_elem.text else ''
                ma_data['has_notes'] = True
            else:
                ma_data['notes'] = ''
                ma_data['has_notes'] = False
            
            # Parse modifiers and adders
            modifiers = []
            for mod_elem in ma_elem_item.findall('MODIFIER'):
                mod_data = {
                    'xmlid': mod_elem.get('XMLID', ''),
                    'attributes': dict(mod_elem.attrib),
                }
                mod_data['basecost'] = float(mod_elem.get('BASECOST', '0'))
                modifiers.append(mod_data)
            ma_data['modifiers'] = modifiers
            
            ma_data['adders'] = self._parse_adders_recursive(ma_elem_item)
            
            martial_arts.append(ma_data)
        
        return martial_arts
    
    def _parse_equipment(self, root: etree.Element) -> List[Dict[str, Any]]:
        """Parse EQUIPMENT section."""
        equip_elem = root.find('EQUIPMENT')
        if equip_elem is None:
            return []
        
        equipment = []
        for equip_item in equip_elem:
            equip_data = {
                'xmlid': equip_item.get('XMLID', ''),
                'tag': equip_item.tag,
                'attributes': dict(equip_item.attrib),  # Preserve all attributes
            }
            
            # Parse common attributes for easy access
            equip_data['levels'] = int(equip_item.get('LEVELS', '0'))
            equip_data['id'] = equip_item.get('ID', '')
            
            # Parse NOTES subelement
            notes_elem = equip_item.find('NOTES')
            if notes_elem is not None:
                equip_data['notes'] = notes_elem.text.strip() if notes_elem.text else ''
                equip_data['has_notes'] = True
            else:
                equip_data['notes'] = ''
                equip_data['has_notes'] = False
            
            # Parse modifiers and adders
            modifiers = []
            for mod_elem in equip_item.findall('MODIFIER'):
                mod_data = {
                    'xmlid': mod_elem.get('XMLID', ''),
                    'attributes': dict(mod_elem.attrib),
                }
                mod_data['basecost'] = float(mod_elem.get('BASECOST', '0'))
                modifiers.append(mod_data)
            equip_data['modifiers'] = modifiers
            
            equip_data['adders'] = self._parse_adders_recursive(equip_item)
            
            equipment.append(equip_data)
        
        return equipment
    
    def write_file(self, character_data: Dict[str, Any], file_path: str) -> None:
        """
        Write character data to an HDC file.
        
        Converted from Java Hero.getSaveXML() format.
        
        Args:
            character_data: Dictionary containing character data
            file_path: Path where the .hdc file should be written
        """
        root = etree.Element('CHARACTER')
        root.set('version', character_data.get('version', '6.0'))
        
        # Template attribute if present
        if character_data.get('template'):
            root.set('TEMPLATE', character_data['template'])
        
        # Write BASIC_CONFIGURATION
        config = character_data.get('basic_configuration', {})
        config_elem = etree.SubElement(root, 'BASIC_CONFIGURATION')
        # Use integers for point values (the HDC format expects this)
        config_elem.set('BASE_POINTS', str(int(float(config.get('base_points', 0)))))
        config_elem.set('DISAD_POINTS', str(int(float(config.get('disad_points', 0)))))
        config_elem.set('EXPERIENCE', str(int(float(config.get('experience', 0)))))
        
        # Add EXPORT_TEMPLATE before RULES (preserve original attribute order)
        if config.get('export_template'):
            config_elem.set('EXPORT_TEMPLATE', config['export_template'])
        # Add RULES attribute if present (some files have it, some don't)
        rules = config.get('rules', '')
        if rules:
            config_elem.set('RULES', rules)
        
        # Write CHARACTER_INFO with all attributes
        info = character_data.get('character_info', {})
        info_elem = etree.SubElement(root, 'CHARACTER_INFO')
        info_elem.set('CHARACTER_NAME', info.get('character_name', ''))
        info_elem.set('ALTERNATE_IDENTITIES', info.get('alternate_identities', ''))
        info_elem.set('PLAYER_NAME', info.get('player_name', ''))
        info_elem.set('HEIGHT', str(info.get('height', '')))
        info_elem.set('WEIGHT', str(info.get('weight', '')))
        info_elem.set('HAIR_COLOR', info.get('hair_color', ''))
        info_elem.set('EYE_COLOR', info.get('eye_color', ''))
        info_elem.set('CAMPAIGN_NAME', info.get('campaign_name', ''))
        info_elem.set('GENRE', info.get('genre', ''))
        info_elem.set('GM', info.get('gm', ''))
        
        # Text elements as child elements
        bg_elem = etree.SubElement(info_elem, 'BACKGROUND')
        bg_elem.text = info.get('background', '')
        
        pers_elem = etree.SubElement(info_elem, 'PERSONALITY')
        pers_elem.text = info.get('personality', '')
        
        quote_elem = etree.SubElement(info_elem, 'QUOTE')
        quote_elem.text = info.get('quote', '')
        
        tactics_elem = etree.SubElement(info_elem, 'TACTICS')
        tactics_elem.text = info.get('tactics', '')
        
        use_elem = etree.SubElement(info_elem, 'CAMPAIGN_USE')
        use_elem.text = info.get('campaign_use', '')
        
        appear_elem = etree.SubElement(info_elem, 'APPEARANCE')
        appear_elem.text = info.get('appearance', '')
        
        for i in range(1, 6):
            notes_elem = etree.SubElement(info_elem, f'NOTES{i}')
            notes_elem.text = info.get(f'notes{i}', '')
        
        # Write CHARACTERISTICS
        chars_elem = etree.SubElement(root, 'CHARACTERISTICS')
        for char in character_data.get('characteristics', []):
            self._write_object_element(chars_elem, char)
        
        # Write SKILLS
        skills_elem = etree.SubElement(root, 'SKILLS')
        for skill in character_data.get('skills', []):
            self._write_object_element(skills_elem, skill)
        
        # Write PERKS
        perks_elem = etree.SubElement(root, 'PERKS')
        for perk in character_data.get('perks', []):
            self._write_object_element(perks_elem, perk)
        
        # Write TALENTS
        talents_elem = etree.SubElement(root, 'TALENTS')
        for talent in character_data.get('talents', []):
            self._write_object_element(talents_elem, talent)
        
        # Write MARTIALARTS
        ma_elem = etree.SubElement(root, 'MARTIALARTS')
        for maneuver in character_data.get('martial_arts', []):
            self._write_object_element(ma_elem, maneuver)
        
        # Write POWERS
        powers_elem = etree.SubElement(root, 'POWERS')
        for power in character_data.get('powers', []):
            self._write_object_element(powers_elem, power)
        
        # Write DISADVANTAGES (or COMPLICATIONS for 6E)
        disads_elem = etree.SubElement(root, 'DISADVANTAGES')
        for comp in character_data.get('complications', []):
            self._write_object_element(disads_elem, comp)
        
        # Write EQUIPMENT (always include, even if empty)
        equip_elem = etree.SubElement(root, 'EQUIPMENT')
        for equip in character_data.get('equipment', []):
            self._write_object_element(equip_elem, equip)
        
        # Write RULES section if present
        rules = character_data.get('rules')
        if rules:
            rules_elem = etree.SubElement(root, 'RULES')
            for key, value in rules.items():
                if value is not None:
                    rules_elem.set(key, str(value))
        
        # Write IMAGE section if present
        image_data = character_data.get('image', {})
        if image_data and image_data.get('data'):
            image_elem = etree.SubElement(root, 'IMAGE')
            if image_data.get('file_name'):
                image_elem.set('FileName', image_data['file_name'])
            if image_data.get('file_path'):
                image_elem.set('FilePath', image_data['file_path'])
            # Use CDATA for image data
            image_elem.text = etree.CDATA(image_data['data'])
        
        # Determine output encoding (preserve original if available)
        output_encoding = character_data.get('_encoding', 'UTF-8')
        bom_type = character_data.get('_bom')  # 'le', 'be', or None
        use_crlf = character_data.get('_crlf', True)  # Default to CRLF
        
        # Write to file matching the HDC format exactly:
        # - Preserve original encoding (UTF-8 or UTF-16)
        # - Preserve original line endings (LF or CRLF)
        # - Self-closing empty tags with space before />
        # - Trailing blank line
        
        # Determine the encoding string for lxml
        if 'UTF-16' in output_encoding.upper():
            # Use UTF-16 without specifying endianness - lxml will add appropriate BOM
            lxml_encoding = 'UTF-16'
        else:
            lxml_encoding = 'UTF-8'
        
        xml_bytes = etree.tostring(
            root,
            encoding=lxml_encoding,
            xml_declaration=True,
            pretty_print=True
        )
        
        # Decode for post-processing
        if 'UTF-16' in output_encoding.upper():
            xml_str = xml_bytes.decode('utf-16')
        else:
            xml_str = xml_bytes.decode('utf-8')
        
        # Fix XML declaration to use double quotes (lxml uses single quotes)
        # Handle both UTF-8 and UTF-16 declarations
        import re
        xml_str = re.sub(r"<\?xml version='1\.0' encoding='([^']+)'\?>",
                         r'<?xml version="1.0" encoding="\1"?>', xml_str)
        
        # Convert empty tags to self-closing format: <TAG></TAG> -> <TAG />
        # Also handle tags with attributes: <TAG attr="val"></TAG> -> <TAG attr="val" />
        xml_str = re.sub(r'<(\w+)></\1>', r'<\1 />', xml_str)
        xml_str = re.sub(r'<(\w+)([^>]*)></\1>', r'<\1\2 />', xml_str)
        # Also add space before /> for self-closing tags that don't have it
        xml_str = re.sub(r'([^/\s])/>',  r'\1 />', xml_str)
        
        # Handle line endings based on original file
        if use_crlf:
            xml_str = xml_str.replace('\n', '\r\n')
            line_end = '\r\n'
        else:
            # Keep LF only
            line_end = '\n'
        
        # Add trailing blank line (Hero Designer format)
        if not xml_str.endswith(line_end + line_end):
            xml_str += line_end
        
        # Write to file with appropriate encoding
        if 'UTF-16' in output_encoding.upper():
            # For UTF-16, need to handle BOM correctly
            # Python's utf-16 codec adds LE BOM by default
            # For BE, we need utf-16-be but add BOM manually
            if bom_type == 'be':
                # Write UTF-16 BE with BOM
                with open(file_path, 'wb') as f:
                    f.write(b'\xfe\xff')  # UTF-16 BE BOM
                    f.write(xml_str.encode('utf-16-be'))
            else:
                # Write UTF-16 LE with BOM (default)
                with open(file_path, 'w', encoding='utf-16', newline='') as f:
                    f.write(xml_str)
        else:
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                f.write(xml_str)
    
    def _write_object_element(self, parent: etree.Element, obj_data: Dict[str, Any]) -> None:
        """
        Write a generic object element (power, skill, etc.) with all attributes preserved.
        
        This method preserves all original attributes from the parsed HDC file,
        which is crucial for round-trip compatibility.
        """
        # Determine tag name
        tag = obj_data.get('tag', 'POWER')
        if obj_data.get('xmlid'):
            # Use XMLID as tag for characteristics
            if tag in ('CHARACTERISTIC', 'CHAR') or obj_data.get('attributes', {}).get('XMLID', '').upper() in (
                'STR', 'DEX', 'CON', 'INT', 'EGO', 'PRE', 'OCV', 'DCV', 'OMCV', 'DMCV',
                'SPD', 'PD', 'ED', 'REC', 'END', 'BODY', 'STUN', 'RUNNING', 'SWIMMING', 'LEAPING'
            ):
                tag = obj_data.get('xmlid', tag)
        
        obj_elem = etree.SubElement(parent, tag)
        
        # First, copy all original attributes if available
        # Important: preserve empty string attributes (Hero Designer is strict about this)
        attrs = obj_data.get('attributes', {})
        for key, value in attrs.items():
            if value is not None:
                obj_elem.set(key, str(value))
        
        # Ensure critical attributes are set
        if obj_data.get('xmlid'):
            obj_elem.set('XMLID', obj_data['xmlid'])
        if 'levels' in obj_data:
            obj_elem.set('LEVELS', str(obj_data['levels']))
        if obj_data.get('id'):
            obj_elem.set('ID', str(obj_data['id']))
        if obj_data.get('alias'):
            obj_elem.set('ALIAS', obj_data['alias'])
        if obj_data.get('display'):
            obj_elem.set('DISPLAY', obj_data['display'])
        
        # Write NOTES as child element if present
        if obj_data.get('notes') or obj_data.get('has_notes'):
            notes_elem = etree.SubElement(obj_elem, 'NOTES')
            notes_elem.text = obj_data.get('notes', '')
        
        # Write adders BEFORE modifiers (HDC order)
        for adder in obj_data.get('adders', []):
            self._write_adder_element(obj_elem, adder)
        
        # Write modifiers
        for mod in obj_data.get('modifiers', []):
            self._write_modifier_element(obj_elem, mod)
        
        # Write nested powers (for frameworks)
        for nested in obj_data.get('nested_powers', []):
            self._write_object_element(obj_elem, nested)
    
    def _write_modifier_element(self, parent: etree.Element, mod_data: Dict[str, Any]) -> None:
        """Write a modifier element with all attributes preserved."""
        mod_elem = etree.SubElement(parent, 'MODIFIER')
        
        # Copy all original attributes (preserve empty strings)
        attrs = mod_data.get('attributes', {})
        for key, value in attrs.items():
            if value is not None:
                mod_elem.set(key, str(value))
        
        # Ensure critical attributes are set
        if mod_data.get('xmlid'):
            mod_elem.set('XMLID', mod_data['xmlid'])
        if 'basecost' in mod_data:
            mod_elem.set('BASECOST', str(mod_data['basecost']))
        if mod_data.get('alias'):
            mod_elem.set('ALIAS', mod_data['alias'])
        
        # Write NOTES as child element if present
        if mod_data.get('notes') or mod_data.get('has_notes'):
            notes_elem = etree.SubElement(mod_elem, 'NOTES')
            notes_elem.text = mod_data.get('notes', '')
        
        # Write nested adders
        for adder in mod_data.get('adders', []):
            self._write_adder_element(mod_elem, adder)
    
    def _write_adder_element(self, parent: etree.Element, adder_data: Dict[str, Any]) -> None:
        """Write an adder element with all attributes preserved."""
        adder_elem = etree.SubElement(parent, 'ADDER')
        
        # Copy all original attributes (preserve empty strings)
        attrs = adder_data.get('attributes', {})
        for key, value in attrs.items():
            if value is not None:
                adder_elem.set(key, str(value))
        
        # Ensure critical attributes are set
        if adder_data.get('xmlid'):
            adder_elem.set('XMLID', adder_data['xmlid'])
        if 'basecost' in adder_data:
            adder_elem.set('BASECOST', str(adder_data['basecost']))
        if adder_data.get('alias'):
            adder_elem.set('ALIAS', adder_data['alias'])
        
        # Write NOTES as child element if present
        if adder_data.get('notes') or adder_data.get('has_notes'):
            notes_elem = etree.SubElement(adder_elem, 'NOTES')
            notes_elem.text = adder_data.get('notes', '')
        
        # Write nested adders (recursively)
        for nested_adder in adder_data.get('adders', []):
            self._write_adder_element(adder_elem, nested_adder)
    
    def _write_power_element(self, parent: etree.Element, power: Dict[str, Any]) -> None:
        """Write a power element (legacy method, calls _write_object_element)."""
        self._write_object_element(parent, power)
    
    def create_hero_from_file(self, file_path: str) -> 'Hero':
        """
        Parse an HDC file and create a Hero object with all components.
        
        This is the "proper" way to import an HDC file - it creates actual
        Hero Designer objects (Hero, Power, Skill, etc.) from the XML data.
        
        Args:
            file_path: Path to the .hdc file
            
        Returns:
            Hero object with all character data loaded
        """
        from kirby_cost.model.hero import Hero
        from kirby_cost.model.rules import Rules
        from kirby_cost.core.context import EngineContext
        
        # Parse the file
        hdc_data = self.parse_file(file_path)
        
        # Create Hero object
        rules = Rules()
        hero = Hero(rules)
        
        # Set basic configuration
        config = hdc_data.get('basic_configuration', {})
        hero.base_points = int(config.get('base_points', 400))
        hero.disad_points = int(config.get('disad_points', 75))
        hero.experience = int(config.get('experience', 0))
        
        # Set character info
        info = hdc_data.get('character_info', {})
        hero.character_name = info.get('character_name', '')
        hero.player_name = info.get('player_name', '')
        hero.alternate_identities = info.get('alternate_identities', '')
        hero.background = info.get('background', '')
        hero.personality = info.get('personality', '')
        hero.quote = info.get('quote', '')
        hero.tactics = info.get('tactics', '')
        hero.appearance = info.get('appearance', '')
        
        # Physical description
        height_str = info.get('height', '')
        if height_str:
            try:
                hero.height = float(height_str)
            except (ValueError, TypeError):
                pass
        
        weight_str = info.get('weight', '')
        if weight_str:
            try:
                hero.weight = float(weight_str)
            except (ValueError, TypeError):
                pass
        
        hero.hair_color = info.get('hair_color', '')
        hero.eye_color = info.get('eye_color', '')
        
        # Campaign information
        hero.campaign_name = info.get('campaign_name', '')
        hero.genre = info.get('genre', '')
        hero.gm = info.get('gm', '')
        hero.use = info.get('campaign_use', '')
        
        # Notes
        hero.notes1 = info.get('notes1', '')
        hero.notes2 = info.get('notes2', '')
        hero.notes3 = info.get('notes3', '')
        hero.notes4 = info.get('notes4', '')
        hero.notes5 = info.get('notes5', '')
        
        # Image data
        image_data = hdc_data.get('image', {})
        if image_data:
            hero.image_file_name = image_data.get('file_name', '')
            hero.image_file_path = image_data.get('file_path', '')
            hero.image_data = image_data.get('data', '')
        
        # Load characteristics
        for char_data in hdc_data.get('characteristics', []):
            char_obj = self._create_characteristic_from_data(char_data)
            if char_obj:
                hero.characteristics.append(char_obj)
        
        # Load powers
        for power_data in hdc_data.get('powers', []):
            power_obj = self._create_power_from_data(power_data)
            if power_obj:
                hero.powers.append(power_obj)
        
        # Load skills
        for skill_data in hdc_data.get('skills', []):
            skill_obj = self._create_skill_from_data(skill_data)
            if skill_obj:
                hero.skills.append(skill_obj)
        
        # Load complications
        for comp_data in hdc_data.get('complications', []):
            comp_obj = self._create_complication_from_data(comp_data)
            if comp_obj:
                hero.disads.append(comp_obj)
        
        # Load perks
        for perk_data in hdc_data.get('perks', []):
            perk_obj = self._create_perk_from_data(perk_data)
            if perk_obj:
                hero.perks.append(perk_obj)
        
        # Load talents
        for talent_data in hdc_data.get('talents', []):
            talent_obj = self._create_talent_from_data(talent_data)
            if talent_obj:
                hero.talents.append(talent_obj)
        
        # Load martial arts
        for ma_data in hdc_data.get('martial_arts', []):
            ma_obj = self._create_martial_art_from_data(ma_data)
            if ma_obj:
                hero.maneuvers.append(ma_obj)
        
        # Load equipment
        for equip_data in hdc_data.get('equipment', []):
            equip_obj = self._create_equipment_from_data(equip_data)
            if equip_obj:
                hero.equipment.append(equip_obj)
        
        # Set as active hero
        EngineContext.active_hero(hero)
        
        return hero
    
    def _create_characteristic_from_data(self, char_data: Dict[str, Any]) -> Optional['GenericObject']:
        """Create a Characteristic object from parsed data."""
        from kirby_cost.objects.characteristics.characteristic import Characteristic
        from kirby_cost.util.constants import characteristic_integer
        
        xmlid = char_data.get('xmlid', '').upper()
        if not xmlid:
            return None
        
        # Map XMLID to characteristic class
        # For now, create a generic Characteristic
        # In full implementation, would create specific types (Strength, Dexterity, etc.)
        char = Characteristic()
        char.xmlid = xmlid
        char.levels = char_data.get('levels', 0)
        
        return char
    
    def _create_power_from_data(self, power_data: Dict[str, Any]) -> Optional['GenericObject']:
        """Create a Power object from parsed data."""
        from kirby_cost.objects.powers.power import Power
        from lxml import etree
        
        xmlid = power_data.get('xmlid', '').upper()
        if not xmlid:
            return None
        
        # Create a generic Power object
        # In full implementation, would create specific power types
        power = Power()
        power.xmlid = xmlid
        power.levels = power_data.get('levels', 0)
        power.alias = power_data.get('alias', '')
        power.display = power_data.get('display', '')
        
        # Create a temporary XML element to restore modifiers/adders
        # This allows restore_from_save() to work properly
        temp_elem = etree.Element(power_data.get('tag', 'POWER'))
        temp_elem.set('XMLID', xmlid)
        temp_elem.set('LEVELS', str(power_data.get('levels', 0)))
        
        # Add modifiers
        for mod_data in power_data.get('modifiers', []):
            mod_elem = etree.SubElement(temp_elem, 'MODIFIER')
            mod_elem.set('XMLID', mod_data.get('xmlid', ''))
            mod_elem.set('BASECOST', str(mod_data.get('basecost', 0)))
        
        # Add adders
        for adder_data in power_data.get('adders', []):
            adder_elem = etree.SubElement(temp_elem, 'ADDER')
            adder_elem.set('XMLID', adder_data.get('xmlid', ''))
            adder_elem.set('BASECOST', str(adder_data.get('basecost', 0)))
        
        # Restore from XML (this will parse modifiers/adders)
        power.restore_from_save(temp_elem)
        
        # Handle nested powers (frameworks)
        nested_powers = power_data.get('nested_powers', [])
        if nested_powers:
            # If this is a framework, would need to add nested powers
            # For now, just store the data
            pass
        
        return power
    
    def _create_skill_from_data(self, skill_data: Dict[str, Any]) -> Optional['GenericObject']:
        """Create a Skill object from parsed data."""
        from kirby_cost.objects.skills.skill import Skill
        from lxml import etree
        
        xmlid = skill_data.get('xmlid', '').upper()
        if not xmlid:
            return None
        
        # Create a generic Skill object
        skill = Skill()
        skill.xmlid = xmlid
        skill.levels = skill_data.get('levels', 0)
        
        # Set characteristic
        char_str = skill_data.get('characteristic', '')
        if char_str:
            from kirby_cost.util.constants import characteristic_integer
            skill.characteristic = characteristic_integer(char_str)
        
        # Create temp XML element for restore
        temp_elem = etree.Element(skill_data.get('tag', 'SKILL'))
        temp_elem.set('XMLID', xmlid)
        temp_elem.set('LEVELS', str(skill_data.get('levels', 0)))
        if char_str:
            temp_elem.set('CHARACTERISTIC', char_str)
        
        skill.restore_from_save(temp_elem)
        
        return skill
    
    def _create_complication_from_data(self, comp_data: Dict[str, Any]) -> Optional['GenericObject']:
        """Create a Complication/Disadvantage object from parsed data."""
        from kirby_cost.objects.disads.disadvantage import Disadvantage
        from lxml import etree
        
        xmlid = comp_data.get('xmlid', '').upper()
        if not xmlid:
            return None
        
        # Create temp XML element
        temp_elem = etree.Element('COMPLICATION')
        temp_elem.set('XMLID', xmlid)
        temp_elem.set('NAME', comp_data.get('name', ''))
        
        # Add adders
        for adder_data in comp_data.get('adders', []):
            adder_elem = etree.SubElement(temp_elem, 'ADDER')
            adder_elem.set('XMLID', adder_data.get('xmlid', ''))
            adder_elem.set('BASECOST', str(adder_data.get('basecost', 0)))
        
        # Use factory method to create appropriate type
        comp = Disadvantage.get_instance(temp_elem)
        
        return comp
    
    def _create_perk_from_data(self, perk_data: Dict[str, Any]) -> Optional['GenericObject']:
        """Create a Perk object from parsed data."""
        from kirby_cost.objects.perks.perk import Perk
        from lxml import etree
        
        xmlid = perk_data.get('xmlid', '').upper()
        if not xmlid:
            return None
        
        # Create temp XML element
        temp_elem = etree.Element(perk_data.get('tag', 'PERK'))
        temp_elem.set('XMLID', xmlid)
        temp_elem.set('LEVELS', str(perk_data.get('levels', 0)))
        
        # Add modifiers and adders
        for mod_data in perk_data.get('modifiers', []):
            mod_elem = etree.SubElement(temp_elem, 'MODIFIER')
            mod_elem.set('XMLID', mod_data.get('xmlid', ''))
            mod_elem.set('BASECOST', str(mod_data.get('basecost', 0)))
        
        for adder_data in perk_data.get('adders', []):
            adder_elem = etree.SubElement(temp_elem, 'ADDER')
            adder_elem.set('XMLID', adder_data.get('xmlid', ''))
            adder_elem.set('BASECOST', str(adder_data.get('basecost', 0)))
        
        # Create Perk object
        perk = Perk(temp_elem, xmlid)
        
        return perk
    
    def _create_talent_from_data(self, talent_data: Dict[str, Any]) -> Optional['GenericObject']:
        """Create a Talent object from parsed data."""
        from kirby_cost.objects.talents.talent import Talent
        from lxml import etree
        
        xmlid = talent_data.get('xmlid', '').upper()
        if not xmlid:
            return None
        
        # Create temp XML element
        temp_elem = etree.Element(talent_data.get('tag', 'TALENT'))
        temp_elem.set('XMLID', xmlid)
        temp_elem.set('LEVELS', str(talent_data.get('levels', 0)))
        
        # Add modifiers and adders
        for mod_data in talent_data.get('modifiers', []):
            mod_elem = etree.SubElement(temp_elem, 'MODIFIER')
            mod_elem.set('XMLID', mod_data.get('xmlid', ''))
            mod_elem.set('BASECOST', str(mod_data.get('basecost', 0)))
        
        for adder_data in talent_data.get('adders', []):
            adder_elem = etree.SubElement(temp_elem, 'ADDER')
            adder_elem.set('XMLID', adder_data.get('xmlid', ''))
            adder_elem.set('BASECOST', str(adder_data.get('basecost', 0)))
        
        # Create Talent object
        talent = Talent(temp_elem, xmlid)
        
        return talent
    
    def _create_martial_art_from_data(self, ma_data: Dict[str, Any]) -> Optional['GenericObject']:
        """Create a Martial Art object from parsed data."""
        from kirby_cost.objects.martial_arts.maneuver import Maneuver
        from lxml import etree
        
        xmlid = ma_data.get('xmlid', '').upper()
        if not xmlid:
            return None
        
        # Create temp XML element
        temp_elem = etree.Element(ma_data.get('tag', 'MARTIALART'))
        temp_elem.set('XMLID', xmlid)
        temp_elem.set('LEVELS', str(ma_data.get('levels', 0)))
        
        # Add modifiers and adders
        for mod_data in ma_data.get('modifiers', []):
            mod_elem = etree.SubElement(temp_elem, 'MODIFIER')
            mod_elem.set('XMLID', mod_data.get('xmlid', ''))
            mod_elem.set('BASECOST', str(mod_data.get('basecost', 0)))
        
        for adder_data in ma_data.get('adders', []):
            adder_elem = etree.SubElement(temp_elem, 'ADDER')
            adder_elem.set('XMLID', adder_data.get('xmlid', ''))
            adder_elem.set('BASECOST', str(adder_data.get('basecost', 0)))
        
        # Create Maneuver object (or other martial art type based on XMLID)
        if xmlid == "MANEUVER":
            ma = Maneuver(temp_elem)
        else:
            # For other martial art types, use base GenericObject for now
            from kirby_cost.objects.base import GenericObject
            ma = GenericObject()
            ma._init(temp_elem)
            ma.restore_from_save(temp_elem)
        
        return ma
    
    def _create_equipment_from_data(self, equip_data: Dict[str, Any]) -> Optional['GenericObject']:
        """
        Create an Equipment object from parsed data.
        
        Equipment items are Power objects (or frameworks) marked as equipment.
        They can be:
        - Regular POWER elements
        - MULTIPOWER frameworks
        - ELEMENTAL_CONTROL frameworks
        - VPP (Variable Power Pool) frameworks
        - LIST elements
        
        Args:
            equip_data: Dictionary containing equipment data from HDC file
            
        Returns:
            GenericObject (Power, Multipower, VPP, etc.) marked as equipment
        """
        # Equipment items are created the same way as powers
        # They're just Power objects marked with is_equipment=True and is_power=True
        power_obj = self._create_power_from_data(equip_data)
        
        if power_obj:
            # Mark as equipment (matches Java: setPower(true) and setIsEquipment(true))
            power_obj._is_power = True
            power_obj._is_equipment = True
        
        return power_obj

