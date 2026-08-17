"""
HDT (Hero Designer Template) Parser

This module parses Hero Designer Template (.hdt) files which contain the
definitions for all powers, skills, modifiers, characteristics, etc.
that can be used in Hero Designer.

The main template file is Main6E.hdt which contains all 6th Edition definitions.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from lxml import etree


class HDTParser:
    """Parser for Hero Designer Template (.hdt) files."""
    
    def __init__(self):
        self._id_counter = 0
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse an HDT file and return a structured dictionary.
        
        Args:
            file_path: Path to the .hdt file
            
        Returns:
            Dictionary containing all template definitions
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"HDT file not found: {file_path}")
        
        # Read raw content to preserve exact formatting for round-trip
        with open(path, 'rb') as f:
            raw_content = f.read()
        
        tree = etree.parse(path)
        root = tree.getroot()
        
        if root.tag != "TEMPLATE":
            raise ValueError(f"Invalid HDT file: root element must be TEMPLATE, found {root.tag}")
        
        result = self._parse_template(root)
        
        # Store raw content for byte-identical export
        result['_raw_content'] = raw_content
        result['_file_path'] = str(path)
        
        return result
    
    def _parse_template(self, root: etree.Element) -> Dict[str, Any]:
        """Parse the TEMPLATE root element."""
        template_data = {
            'version': root.get('version', ''),
            'name': root.get('name', ''),
            # <TEMPLATE extends="builtIn.Main6E.hdt"> — every specialised
            # template (Vehicle6E, Computer6E, Automaton6E, Superheroic6E, …)
            # extends Main6E and overrides only what differs. Main6E itself
            # declares no parent. The provider follows this chain so a
            # character built on a specialised template gets that template's
            # rates on top of Main6E's.
            'extends': root.get('extends', ''),
            'mainapp': self._parse_mainapp(root.find('MAINAPP')),
            'characteristics': self._parse_characteristics(root.find('CHARACTERISTICS')),
            'skills': self._parse_skills(root.find('SKILLS')),
            'skill_enhancers': self._parse_skill_enhancers(root.find('SKILL_ENHANCERS')),
            'martial_arts': self._parse_martial_arts(root.find('MARTIAL_ARTS')),
            'perks': self._parse_perks(root.find('PERKS')),
            'talents': self._parse_talents(root.find('TALENTS')),
            'powers': self._parse_powers(root.find('POWERS')),
            'modifiers': self._parse_modifiers(root.find('MODIFIERS')),
            'disadvantages': self._parse_disadvantages(root.find('DISADVANTAGES')),
        }
        return template_data
    
    def _parse_mainapp(self, elem: Optional[etree.Element]) -> Dict[str, Any]:
        """Parse MAINAPP section containing template settings."""
        if elem is None:
            return {}
        
        data = {
            'background_tab': elem.get('BACKGROUND_TAB', 'Yes'),
            'height': elem.get('HEIGHT', 'Yes'),
            'weight': elem.get('WEIGHT', 'Yes'),
            'ncm_cost_multiplier': int(elem.get('NCM_COST_MULTIPLIER', '2')),
            'general_level': int(elem.get('GENERAL_LEVEL', '10')),
            'labels': {}
        }
        
        # Parse label elements
        label_elements = [
            ('NAME1', 'character_name'),
            ('NAME2', 'alternate_ids'),
            ('CAMPAIGN', 'campaign'),
            ('GENRE', 'genre'),
            ('PLAYER', 'player'),
            ('GM', 'gm'),
            ('EYE_COLOR', 'eye_color'),
            ('HAIR_COLOR', 'hair_color'),
            ('BACKGROUND', 'background'),
            ('PERSONALITY', 'personality'),
            ('QUOTE', 'quote'),
            ('TACTICS', 'tactics'),
            ('USE', 'campaign_use'),
            ('APPEARANCE', 'appearance'),
        ]
        
        for xml_name, key in label_elements:
            child = elem.find(xml_name)
            if child is not None and child.text:
                data['labels'][key] = child.text.strip()
        
        return data
    
    def _parse_characteristics(self, elem: Optional[etree.Element]) -> List[Dict[str, Any]]:
        """Parse CHARACTERISTICS section."""
        if elem is None:
            return []
        
        characteristics = []
        for child in elem:
            char_data = self._parse_generic_object(child)
            char_data['xmlid'] = child.tag  # STR, DEX, CON, etc.
            characteristics.append(char_data)
        
        return characteristics
    
    def _parse_skills(self, elem: Optional[etree.Element]) -> List[Dict[str, Any]]:
        """Parse SKILLS section."""
        if elem is None:
            return []
        
        skills = []
        for child in elem:
            if child.tag == 'REMOVE':
                # Handle removal of parent template skills
                continue
            
            # All skill types (SKILL, ANIMAL_HANDLER, COMBAT_LEVELS, etc.)
            skill_data = self._parse_generic_object(child)
            skill_data['tag'] = child.tag  # Preserve the original tag
            skill_data['xmlid'] = child.get('XMLID', child.tag)
            
            # Skill-specific attributes
            skill_data['characteristic_choice'] = self._parse_characteristic_choice(child)
            skill_data['familiarity_roll'] = child.get('FAMILIARITYROLL', '')
            skill_data['familiarity_cost'] = child.get('FAMILIARITYCOST', '')
            skill_data['proficiency_cost'] = child.get('PROFICIENCYCOST', '')
            skill_data['show_dialog'] = child.get('SHOWDIALOG', 'No')
            
            skills.append(skill_data)
        
        return skills
    
    def _parse_characteristic_choice(self, elem: etree.Element) -> List[Dict[str, Any]]:
        """Parse CHARACTERISTIC_CHOICE items for skills.

        A skill's cost lives here, not on the skill element: each

            <ITEM CHARACTERISTIC="DEX" BASECOST="3" LVLCOST="2" LVLVAL="1" />

        gives the cost of buying that skill against that characteristic, and a
        skill offering several (Knowledge Skill: GENERAL 2/1, INT 3/1) costs
        differently depending on which the character chose. Returning the item
        tags alone — always the literal "ITEM" — discarded every one of those
        numbers.
        """
        choices: List[Dict[str, Any]] = []
        choice_elem = elem.find('CHARACTERISTIC_CHOICE')
        if choice_elem is not None:
            for char_elem in choice_elem:
                choices.append({
                    'characteristic': char_elem.get('CHARACTERISTIC', ''),
                    'base_cost': self._parse_float(char_elem.get('BASECOST', '0')),
                    'level_cost': self._parse_float(char_elem.get('LVLCOST', '0')),
                    'level_value': self._parse_float(char_elem.get('LVLVAL', '0')),
                    'attributes': dict(char_elem.attrib),
                })
        return choices
    
    def _parse_skill_enhancers(self, elem: Optional[etree.Element]) -> List[Dict[str, Any]]:
        """Parse SKILL_ENHANCERS section."""
        if elem is None:
            return []
        
        enhancers = []
        for child in elem:
            if child.tag == 'ENHANCER':
                enhancer_data = self._parse_generic_object(child)
                enhancer_data['tag'] = 'ENHANCER'
                enhancers.append(enhancer_data)
        
        return enhancers
    
    def _parse_martial_arts(self, elem: Optional[etree.Element]) -> List[Dict[str, Any]]:
        """Parse MARTIAL_ARTS section."""
        if elem is None:
            return []
        
        maneuvers = []
        for child in elem:
            if child.tag in ('EXTRADC', 'RANGEDDC', 'WEAPON_ELEMENT', 'MANEUVER'):
                ma_data = self._parse_generic_object(child)
                ma_data['tag'] = child.tag
                maneuvers.append(ma_data)
        
        return maneuvers
    
    def _parse_perks(self, elem: Optional[etree.Element]) -> List[Dict[str, Any]]:
        """Parse PERKS section."""
        if elem is None:
            return []
        
        perks = []
        for child in elem:
            if child.tag == 'REMOVE':
                continue
            
            # All perk types (PERK, CONTACT, FRINGE_BENEFIT, etc.)
            perk_data = self._parse_generic_object(child)
            perk_data['tag'] = child.tag
            perk_data['xmlid'] = child.get('XMLID', child.tag)
            perks.append(perk_data)
        
        return perks
    
    def _parse_talents(self, elem: Optional[etree.Element]) -> List[Dict[str, Any]]:
        """Parse TALENTS section."""
        if elem is None:
            return []
        
        talents = []
        for child in elem:
            if child.tag == 'REMOVE':
                continue
            
            # All talent types (TALENT, DANGER_SENSE, COMBAT_LUCK, etc.)
            talent_data = self._parse_generic_object(child)
            talent_data['tag'] = child.tag
            talent_data['xmlid'] = child.get('XMLID', child.tag)
            talents.append(talent_data)
        
        return talents
    
    def _parse_powers(self, elem: Optional[etree.Element]) -> List[Dict[str, Any]]:
        """Parse POWERS section."""
        if elem is None:
            return []
        
        powers = []
        for child in elem:
            # Each power has its own tag (ABSORPTION, AID, FORCEWALL, etc.)
            power_data = self._parse_generic_object(child)
            power_data['xmlid'] = child.tag
            power_data['tag'] = 'POWER'
            powers.append(power_data)
        
        return powers
    
    def _parse_modifiers(self, elem: Optional[etree.Element]) -> List[Dict[str, Any]]:
        """Parse MODIFIERS section (global modifiers)."""
        if elem is None:
            return []
        
        modifiers = []
        for child in elem:
            if child.tag == 'MODIFIER':
                mod_data = self._parse_modifier(child)
                modifiers.append(mod_data)
        
        return modifiers
    
    def _parse_disadvantages(self, elem: Optional[etree.Element]) -> List[Dict[str, Any]]:
        """Parse DISADVANTAGES section."""
        if elem is None:
            return []
        
        disads = []
        for child in elem:
            if child.tag == 'DISAD':
                disad_data = self._parse_generic_object(child)
                disad_data['tag'] = 'DISAD'
                disads.append(disad_data)
        
        return disads
    
    def _parse_generic_object(self, elem: etree.Element) -> Dict[str, Any]:
        """
        Parse a generic object element (power, skill, modifier, etc.)
        
        This captures all the common attributes and nested elements.
        Importantly, it also stores ALL child elements in their original order
        to enable byte-identical round-trip.
        """
        self._id_counter += 1
        
        data = {
            'id': self._id_counter,
            'xmlid': elem.get('XMLID', elem.tag),
            'display': elem.get('DISPLAY', ''),
            'alias': elem.get('ALIAS', ''),

            # CHARACTERISTIC_CHOICE is not a skills-only construct: Combat
            # Sense is a TALENT priced entirely through it
            # (<ITEM CHARACTERISTIC="INT" BASECOST="15" LVLCOST="1"/>), and
            # reading it only for the SKILLS section left every such talent
            # with no cost at all.
            'characteristic_choice': self._parse_characteristic_choice(elem),

            # Cost attributes
            'base_cost': self._parse_float(elem.get('BASECOST', '0')),
            'level_cost': self._parse_float(elem.get('LVLCOST', '0')),
            'level_value': self._parse_float(elem.get('LVLVAL', '1')),
            'min_val': self._parse_int(elem.get('MINVAL', '0')),
            'max_val': self._parse_int(elem.get('MAXVAL', '999')),
            'min_cost': self._parse_float(elem.get('MINCOST', '0')),
            'max_cost': self._parse_float(elem.get('MAXCOST', '')),
            'level_start': self._parse_int(elem.get('LEVELSTART', '0')),
            
            # Common flags
            'exclusive': elem.get('EXCLUSIVE', 'No').upper().startswith('Y'),
            'visible': elem.get('VISIBLE', 'Yes').upper().startswith('Y'),
            'uses_end': elem.get('USESEND', 'No').upper().startswith('Y'),
            'standard_effect_allowed': elem.get('STANDARDEFFECTALLOWED', 'No').upper().startswith('Y'),
            
            # Power-specific
            'duration': elem.get('DURATION', ''),
            'target': elem.get('TARGET', ''),
            'range': elem.get('RANGE', ''),
            'defense': elem.get('DEFENSE', ''),
            
            # Input/option labels
            'input_label': elem.get('INPUTLABEL', ''),
            'option_label': elem.get('OPTIONLABEL', ''),
            'other_input': elem.get('OTHERINPUT', 'No').upper().startswith('Y'),
            
            # Position for ordering
            'position': self._parse_int(elem.get('POSITION', '0')),
            
            # Store all original attributes
            'attributes': dict(elem.attrib),
            
            # Nested elements (parsed for easy access)
            'definition': self._get_text(elem.find('DEFINITION')),
            'types': self._parse_types(elem),
            'options': self._parse_options(elem),
            'adders': self._parse_adders(elem),
            'modifiers': self._parse_nested_modifiers(elem),
            'excludes': self._parse_excludes(elem),
            
            # Store ALL child elements in order for round-trip (including ones we don't parse specially)
            'child_elements': self._parse_all_children(elem),
        }
        
        return data
    
    def _parse_all_children(self, elem: etree.Element) -> List[Dict[str, Any]]:
        """
        Parse ALL child elements of an element, preserving order and structure.
        This enables byte-identical round-trip by capturing everything.
        """
        children = []
        for child in elem:
            child_data = {
                'tag': child.tag,
                'attributes': dict(child.attrib),
                'text': child.text,  # Text content (may include whitespace)
                'tail': child.tail,  # Text after this element
                'children': self._parse_all_children(child),  # Recursive
            }
            children.append(child_data)
        return children
    
    def _parse_modifier(self, elem: etree.Element) -> Dict[str, Any]:
        """Parse a MODIFIER element."""
        self._id_counter += 1
        
        # Determine if advantage or limitation based on cost sign
        base_cost = self._parse_float(elem.get('BASECOST', '0'))
        level_cost = self._parse_float(elem.get('LVLCOST', '0'))
        # Positive cost = advantage, negative = limitation
        # If both are 0, check if explicitly marked as limitation
        is_lim_attr = elem.get('ISLIMITATION', '').upper().startswith('Y')
        is_advantage = (base_cost > 0 or level_cost > 0) and not is_lim_attr
        is_limitation = (base_cost < 0 or level_cost < 0) or is_lim_attr
        
        data = {
            'id': self._id_counter,
            'xmlid': elem.get('XMLID', ''),
            'display': elem.get('DISPLAY', ''),
            'alias': elem.get('ALIAS', ''),
            
            # Cost
            'base_cost': base_cost,
            'level_cost': level_cost,
            'level_value': self._parse_float(elem.get('LVLVAL', '1')),
            'min_cost': self._parse_float(elem.get('MINCOST', '')),
            'max_cost': self._parse_float(elem.get('MAXCOST', '')),
            'min_val': self._parse_int(elem.get('MINVAL', '0')),
            'level_start': self._parse_int(elem.get('LEVELSTART', '0')),
            
            # Flags
            'exclusive': elem.get('EXCLUSIVE', 'No').upper().startswith('Y'),
            'is_advantage': is_advantage,
            'is_limitation': is_limitation,
            'include_in_base': elem.get('INCLUDEINBASE', 'No').upper().startswith('Y'),
            'fixed_value': elem.get('FIXEDVALUE', 'No').upper().startswith('Y'),
            'warn_sign': elem.get('WARNSIGN', 'No').upper().startswith('Y'),
            'show_option_in_parens': elem.get('SHOWOPTIONINPARENS', 'No').upper().startswith('Y'),
            'multiplier': elem.get('MULTIPLIER', 'No').upper().startswith('Y'),
            
            # Input
            'input_label': elem.get('INPUTLABEL', ''),
            'other_input': elem.get('OTHERINPUT', 'No').upper().startswith('Y'),
            
            # Store all original attributes
            'attributes': dict(elem.attrib),
            
            # Nested elements
            'definition': self._get_text(elem.find('DEFINITION')),
            'types': self._parse_types(elem),
            'options': self._parse_options(elem),
            'adders': self._parse_adders(elem),
            'excludes': self._parse_excludes(elem),
            
            # Store ALL child elements for round-trip
            'child_elements': self._parse_all_children(elem),
        }
        
        return data
    
    def _parse_adders(self, elem: etree.Element) -> List[Dict[str, Any]]:
        """Parse ADDER child elements."""
        adders = []
        for adder_elem in elem.findall('ADDER'):
            adder_data = self._parse_adder(adder_elem)
            adders.append(adder_data)
        return adders
    
    def _parse_adder(self, elem: etree.Element) -> Dict[str, Any]:
        """Parse a single ADDER element."""
        self._id_counter += 1
        
        data = {
            'id': self._id_counter,
            'xmlid': elem.get('XMLID', ''),
            'display': elem.get('DISPLAY', ''),
            'alias': elem.get('ALIAS', ''),
            
            # Cost
            'base_cost': self._parse_float(elem.get('BASECOST', '0')),
            'level_cost': self._parse_float(elem.get('LVLCOST', '0')),
            'level_value': self._parse_float(elem.get('LVLVAL', '1')),
            'min_cost': self._parse_float(elem.get('MINCOST', '')),
            'max_cost': self._parse_float(elem.get('MAXCOST', '')),
            'min_val': self._parse_int(elem.get('MINVAL', '0')),
            'level_start': self._parse_int(elem.get('LEVELSTART', '0')),
            
            # Flags
            'exclusive': elem.get('EXCLUSIVE', 'No').upper().startswith('Y'),
            'required': elem.get('REQUIRED', 'No').upper().startswith('Y'),
            'include_in_base': elem.get('INCLUDEINBASE', 'No').upper().startswith('Y'),
            
            # Store all original attributes
            'attributes': dict(elem.attrib),
            
            # Nested elements
            'definition': self._get_text(elem.find('DEFINITION')),
            'types': self._parse_types(elem),
            'options': self._parse_options(elem),
            'excludes': self._parse_excludes(elem),
            
            # Nested adders (adders can contain adders)
            'adders': [],
            
            # Store ALL child elements for round-trip
            'child_elements': self._parse_all_children(elem),
        }
        
        # Parse nested adders recursively
        for nested_adder in elem.findall('ADDER'):
            data['adders'].append(self._parse_adder(nested_adder))
        
        return data
    
    def _parse_nested_modifiers(self, elem: etree.Element) -> List[Dict[str, Any]]:
        """Parse MODIFIER child elements within a power/skill."""
        modifiers = []
        for mod_elem in elem.findall('MODIFIER'):
            mod_data = self._parse_modifier(mod_elem)
            modifiers.append(mod_data)
        return modifiers
    
    def _parse_options(self, elem: etree.Element) -> List[Dict[str, Any]]:
        """Parse OPTION child elements."""
        options = []
        for opt_elem in elem.findall('OPTION'):
            self._id_counter += 1
            opt_data = {
                'id': self._id_counter,
                'xmlid': opt_elem.get('XMLID', ''),
                'display': opt_elem.get('DISPLAY', ''),
                'alias': opt_elem.get('ALIAS', ''),
                'base_cost': self._parse_float(opt_elem.get('BASECOST', '0')),
                'level_cost': self._parse_float(opt_elem.get('LVLCOST', '0')),
                'level_value': self._parse_float(opt_elem.get('LVLVAL', '1')),
                'attributes': dict(opt_elem.attrib),
                # An option can carry its own adders — Area Of Effect keeps
                # ACCURATE under RADIUS, THINCONE under CONE, DOUBLEHEIGHT and
                # DOUBLEWIDTH under LINE, FIXEDSHAPE under ANY. They are
                # buyable on the object like any other adder, and dropping them
                # silently loses whatever they are worth.
                'adders': self._parse_adders(opt_elem),
            }
            options.append(opt_data)
        return options
    
    def _parse_types(self, elem: etree.Element) -> List[str]:
        """Parse TYPE child elements."""
        types = []
        for type_elem in elem.findall('TYPE'):
            if type_elem.text:
                types.append(type_elem.text.strip())
        return types
    
    def _parse_excludes(self, elem: etree.Element) -> List[str]:
        """Parse EXCLUDES child elements."""
        excludes = []
        for exc_elem in elem.findall('EXCLUDES'):
            if exc_elem.text:
                excludes.append(exc_elem.text.strip())
        return excludes
    
    def _get_text(self, elem: Optional[etree.Element]) -> str:
        """Get text content from an element."""
        if elem is None:
            return ''
        return (elem.text or '').strip()
    
    def _parse_float(self, value: str) -> float:
        """Parse a string to float, returning 0.0 on error."""
        if not value:
            return 0.0
        try:
            return float(value)
        except ValueError:
            return 0.0
    
    def _parse_int(self, value: str) -> int:
        """Parse a string to int, returning 0 on error."""
        if not value:
            return 0
        try:
            return int(float(value))
        except ValueError:
            return 0
    
    def write_file(self, template_data: Dict[str, Any], file_path: str, 
                   preserve_format: bool = True, as_base_template: bool = False) -> None:
        """
        Write template data to an HDT file, matching the original format exactly.
        
        Args:
            template_data: Dictionary containing template data (from parse_file)
            file_path: Path where the .hdt file should be written
            preserve_format: If True and raw content is available, write byte-identical copy
            as_base_template: If True, create a standalone base template without 'extends' attribute.
                             This allows defining completely custom powers that Hero Designer
                             will recognize without needing a parent template.
        """
        # If we have the original raw content, write it directly for byte-identical output
        if preserve_format and '_raw_content' in template_data:
            with open(file_path, 'wb') as f:
                f.write(template_data['_raw_content'])
            return
        
        # Otherwise, generate new XML
        root = etree.Element('TEMPLATE')
        if template_data.get('version'):
            root.set('version', template_data['version'])
        
        # Handle extends attribute based on template type
        if not as_base_template:
            # Add extends attribute to reference built-in parent template
            # This is required for Hero Designer to recognize it as a v2+ template
            # Without this, HD thinks it's a "Version 1" template
            extends_value = template_data.get('extends')
            if extends_value:
                root.set('extends', extends_value)
            elif template_data.get('template_id'):
                # Default to extending the built-in version of this template
                root.set('extends', f"builtIn.{template_data['template_id']}")
        
        # Write MAINAPP section
        self._write_mainapp(root, template_data.get('mainapp', {}))
        
        # Write CHARACTERISTICS section
        chars_elem = etree.SubElement(root, 'CHARACTERISTICS')
        for char in template_data.get('characteristics', []):
            self._write_characteristic(chars_elem, char)
        
        # Write SKILLS section
        skills_elem = etree.SubElement(root, 'SKILLS')
        for skill in template_data.get('skills', []):
            self._write_template_object(skills_elem, skill)
        
        # Write SKILL_ENHANCERS section
        enhancers_elem = etree.SubElement(root, 'SKILL_ENHANCERS')
        for enhancer in template_data.get('skill_enhancers', []):
            self._write_template_object(enhancers_elem, enhancer)
        
        # Write MARTIAL_ARTS section
        ma_elem = etree.SubElement(root, 'MARTIAL_ARTS')
        for ma in template_data.get('martial_arts', []):
            self._write_template_object(ma_elem, ma)
        
        # Write PERKS section
        perks_elem = etree.SubElement(root, 'PERKS')
        for perk in template_data.get('perks', []):
            self._write_template_object(perks_elem, perk)
        
        # Write TALENTS section
        talents_elem = etree.SubElement(root, 'TALENTS')
        for talent in template_data.get('talents', []):
            self._write_template_object(talents_elem, talent)
        
        # Write POWERS section
        powers_elem = etree.SubElement(root, 'POWERS')
        for power in template_data.get('powers', []):
            self._write_power(powers_elem, power)
        
        # Write MODIFIERS section (global modifiers)
        mods_elem = etree.SubElement(root, 'MODIFIERS')
        for mod in template_data.get('modifiers', []):
            self._write_modifier(mods_elem, mod)
        
        # Write DISADVANTAGES section
        disads_elem = etree.SubElement(root, 'DISADVANTAGES')
        for disad in template_data.get('disadvantages', []):
            self._write_disad(disads_elem, disad)
        
        # Convert to string with HDT-style formatting
        xml_bytes = etree.tostring(
            root,
            encoding='UTF-8',
            xml_declaration=False,  # HDT files don't have XML declaration
            pretty_print=True
        )
        xml_str = xml_bytes.decode('utf-8')
        
        # Convert 2-space indentation to tabs (HDT style)
        lines = xml_str.split('\n')
        tab_lines = []
        for line in lines:
            # Count leading spaces
            stripped = line.lstrip(' ')
            spaces = len(line) - len(stripped)
            # Convert every 2 spaces to a tab
            tabs = '\t' * (spaces // 2)
            tab_lines.append(tabs + stripped)
        xml_str = '\n'.join(tab_lines)
        
        # Convert to CRLF line endings (HDT style)
        xml_str = xml_str.replace('\n', '\r\n')
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            f.write(xml_str)
    
    def _write_mainapp(self, parent: etree.Element, mainapp: Dict[str, Any]) -> None:
        """Write MAINAPP section."""
        if not mainapp:
            return
        
        elem = etree.SubElement(parent, 'MAINAPP')
        
        # Attributes
        if mainapp.get('background_tab'):
            elem.set('BACKGROUND_TAB', 'Yes' if mainapp['background_tab'] else 'No')
        if mainapp.get('height'):
            elem.set('HEIGHT', 'Yes' if mainapp['height'] else 'No')
        if mainapp.get('weight'):
            elem.set('WEIGHT', 'Yes' if mainapp['weight'] else 'No')
        if mainapp.get('ncm_cost_multiplier'):
            elem.set('NCM_COST_MULTIPLIER', str(mainapp['ncm_cost_multiplier']))
        if mainapp.get('general_level'):
            elem.set('GENERAL_LEVEL', str(mainapp['general_level']))
        
        # Label elements
        labels = mainapp.get('labels', {})
        label_mapping = [
            ('character_name', 'NAME1'),
            ('alternate_ids', 'NAME2'),
            ('campaign', 'CAMPAIGN'),
            ('genre', 'GENRE'),
            ('player', 'PLAYER'),
            ('gm', 'GM'),
            ('eye_color', 'EYE_COLOR'),
            ('hair_color', 'HAIR_COLOR'),
            ('background', 'BACKGROUND'),
            ('personality', 'PERSONALITY'),
            ('quote', 'QUOTE'),
            ('tactics', 'TACTICS'),
            ('campaign_use', 'USE'),
            ('appearance', 'APPEARANCE'),
        ]
        
        for key, xml_name in label_mapping:
            if key in labels:
                label_elem = etree.SubElement(elem, xml_name)
                label_elem.text = labels[key]
    
    def _write_children_from_data(self, parent: etree.Element, children: List[Dict[str, Any]]) -> None:
        """
        Write child elements from stored child_elements data.
        This preserves the exact structure and order for round-trip.
        """
        for child_data in children:
            child_elem = etree.SubElement(parent, child_data['tag'])
            
            # Set attributes
            for key, value in child_data.get('attributes', {}).items():
                child_elem.set(key, value)
            
            # Set text content
            if child_data.get('text'):
                child_elem.text = child_data['text']
            
            # Set tail (text after element)
            if child_data.get('tail'):
                child_elem.tail = child_data['tail']
            
            # Recursively write nested children
            if child_data.get('children'):
                self._write_children_from_data(child_elem, child_data['children'])
    
    def _write_characteristic(self, parent: etree.Element, char: Dict[str, Any]) -> None:
        """Write a characteristic element."""
        # Characteristics use their XMLID as the tag name (STR, DEX, etc.)
        tag = char.get('xmlid', 'CHAR')
        elem = etree.SubElement(parent, tag)
        
        # Write attributes from original_attributes if available
        attrs = char.get('attributes', {})
        for key, value in attrs.items():
            if value is not None and str(value).strip():
                elem.set(key, str(value))
        
        # If we have child_elements, use those for exact round-trip
        if char.get('child_elements'):
            self._write_children_from_data(elem, char['child_elements'])
        else:
            # Fallback to structured data
            # Write TYPE elements
            for type_name in char.get('types', []):
                type_elem = etree.SubElement(elem, 'TYPE')
                type_elem.text = type_name
            
            # Write DEFINITION
            if char.get('definition'):
                def_elem = etree.SubElement(elem, 'DEFINITION')
                def_elem.text = char['definition']
            
            # Write nested adders
            for adder in char.get('adders', []):
                self._write_adder(elem, adder)
            
            # Write nested modifiers
            for mod in char.get('modifiers', []):
                self._write_modifier(elem, mod)
    
    def _write_template_object(self, parent: etree.Element, obj: Dict[str, Any]) -> None:
        """Write a generic template object (skill, perk, talent, etc.)."""
        tag = obj.get('tag', 'SKILL')
        elem = etree.SubElement(parent, tag)
        
        # Write attributes from original_attributes
        attrs = obj.get('attributes', {})
        for key, value in attrs.items():
            if value is not None and str(value).strip():
                elem.set(key, str(value))
        
        # If we have child_elements, use those for exact round-trip
        if obj.get('child_elements'):
            self._write_children_from_data(elem, obj['child_elements'])
        else:
            # Fallback to structured data
            # Write CHARACTERISTIC_CHOICE for skills
            char_choices = obj.get('characteristic_choice', [])
            if char_choices:
                choice_elem = etree.SubElement(elem, 'CHARACTERISTIC_CHOICE')
                for char in char_choices:
                    etree.SubElement(choice_elem, char)
            
            # Write TYPE elements
            for type_name in obj.get('types', []):
                type_elem = etree.SubElement(elem, 'TYPE')
                type_elem.text = type_name
            
            # Write DEFINITION
            if obj.get('definition'):
                def_elem = etree.SubElement(elem, 'DEFINITION')
                def_elem.text = obj['definition']
            
            # Write nested adders
            for adder in obj.get('adders', []):
                self._write_adder(elem, adder)
            
            # Write nested modifiers
            for mod in obj.get('modifiers', []):
                self._write_modifier(elem, mod)
            
            # Write options
            for opt in obj.get('options', []):
                self._write_option(elem, opt)
            
            # Write EXCLUDES
            for exc in obj.get('excludes', []):
                exc_elem = etree.SubElement(elem, 'EXCLUDES')
                exc_elem.text = exc
    
    def _write_power(self, parent: etree.Element, power: Dict[str, Any]) -> None:
        """Write a power element."""
        # Powers use their XMLID as the tag name (ABSORPTION, AID, etc.)
        tag = power.get('xmlid', 'POWER')
        elem = etree.SubElement(parent, tag)
        
        # Write attributes from original_attributes
        attrs = power.get('attributes', {})
        for key, value in attrs.items():
            if value is not None and str(value).strip():
                elem.set(key, str(value))
        
        # If we have child_elements, use those for exact round-trip
        if power.get('child_elements'):
            self._write_children_from_data(elem, power['child_elements'])
        else:
            # Fallback to structured data
            # Write TYPE elements
            for type_name in power.get('types', []):
                type_elem = etree.SubElement(elem, 'TYPE')
                type_elem.text = type_name
            
            # Write DEFINITION
            if power.get('definition'):
                def_elem = etree.SubElement(elem, 'DEFINITION')
                def_elem.text = power['definition']
            
            # Write OPTIONS before ADDERS and MODIFIERS (match original order)
            for opt in power.get('options', []):
                self._write_option(elem, opt)
            
            # Write nested adders
            for adder in power.get('adders', []):
                self._write_adder(elem, adder)
            
            # Write nested modifiers
            for mod in power.get('modifiers', []):
                self._write_modifier(elem, mod)
            
            # Write EXCLUDES
            for exc in power.get('excludes', []):
                exc_elem = etree.SubElement(elem, 'EXCLUDES')
                exc_elem.text = exc
    
    def _write_modifier(self, parent: etree.Element, mod: Dict[str, Any]) -> None:
        """Write a modifier element."""
        elem = etree.SubElement(parent, 'MODIFIER')
        
        # Write attributes from original_attributes
        attrs = mod.get('attributes', {})
        for key, value in attrs.items():
            if value is not None and str(value).strip():
                elem.set(key, str(value))
        
        # If we have child_elements, use those for exact round-trip
        if mod.get('child_elements'):
            self._write_children_from_data(elem, mod['child_elements'])
        else:
            # Fallback to structured data
            # Write TYPE elements
            for type_name in mod.get('types', []):
                type_elem = etree.SubElement(elem, 'TYPE')
                type_elem.text = type_name
            
            # Write DEFINITION
            if mod.get('definition'):
                def_elem = etree.SubElement(elem, 'DEFINITION')
                def_elem.text = mod['definition']
            
            # Write OPTIONS
            for opt in mod.get('options', []):
                self._write_option(elem, opt)
            
            # Write nested adders
            for adder in mod.get('adders', []):
                self._write_adder(elem, adder)
            
            # Write EXCLUDES
            for exc in mod.get('excludes', []):
                exc_elem = etree.SubElement(elem, 'EXCLUDES')
                exc_elem.text = exc
    
    def _write_adder(self, parent: etree.Element, adder: Dict[str, Any]) -> None:
        """Write an adder element."""
        elem = etree.SubElement(parent, 'ADDER')
        
        # Write attributes from original_attributes
        attrs = adder.get('attributes', {})
        for key, value in attrs.items():
            if value is not None and str(value).strip():
                elem.set(key, str(value))
        
        # If we have child_elements, use those for exact round-trip
        if adder.get('child_elements'):
            self._write_children_from_data(elem, adder['child_elements'])
        else:
            # Fallback to structured data
            # Write TYPE elements
            for type_name in adder.get('types', []):
                type_elem = etree.SubElement(elem, 'TYPE')
                type_elem.text = type_name
            
            # Write DEFINITION
            if adder.get('definition'):
                def_elem = etree.SubElement(elem, 'DEFINITION')
                def_elem.text = adder['definition']
            
            # Write OPTIONS
            for opt in adder.get('options', []):
                self._write_option(elem, opt)
            
            # Write nested adders (adders can contain adders)
            for nested_adder in adder.get('adders', []):
                self._write_adder(elem, nested_adder)
            
            # Write EXCLUDES
            for exc in adder.get('excludes', []):
                exc_elem = etree.SubElement(elem, 'EXCLUDES')
                exc_elem.text = exc
    
    def _write_option(self, parent: etree.Element, opt: Dict[str, Any]) -> None:
        """Write an option element."""
        elem = etree.SubElement(parent, 'OPTION')
        
        # Write attributes from original_attributes
        attrs = opt.get('attributes', {})
        for key, value in attrs.items():
            if value is not None and str(value).strip():
                elem.set(key, str(value))
    
    def _write_disad(self, parent: etree.Element, disad: Dict[str, Any]) -> None:
        """Write a disadvantage element."""
        elem = etree.SubElement(parent, 'DISAD')
        
        # Write attributes from original_attributes
        attrs = disad.get('attributes', {})
        for key, value in attrs.items():
            if value is not None and str(value).strip():
                elem.set(key, str(value))
        
        # If we have child_elements, use those for exact round-trip
        if disad.get('child_elements'):
            self._write_children_from_data(elem, disad['child_elements'])
        else:
            # Fallback to structured data
            # Write TYPE elements
            for type_name in disad.get('types', []):
                type_elem = etree.SubElement(elem, 'TYPE')
                type_elem.text = type_name
            
            # Write DEFINITION
            if disad.get('definition'):
                def_elem = etree.SubElement(elem, 'DEFINITION')
                def_elem.text = disad['definition']
            
            # Write nested adders
            for adder in disad.get('adders', []):
                self._write_adder(elem, adder)
            
            # Write nested modifiers
            for mod in disad.get('modifiers', []):
                self._write_modifier(elem, mod)
            
            # Write EXCLUDES
            for exc in disad.get('excludes', []):
                exc_elem = etree.SubElement(elem, 'EXCLUDES')
                exc_elem.text = exc
    
    def summary(self, template_data: Dict[str, Any]) -> Dict[str, int]:
        """Get a summary of counts for each section."""
        return {
            'characteristics': len(template_data.get('characteristics', [])),
            'skills': len(template_data.get('skills', [])),
            'skill_enhancers': len(template_data.get('skill_enhancers', [])),
            'martial_arts': len(template_data.get('martial_arts', [])),
            'perks': len(template_data.get('perks', [])),
            'talents': len(template_data.get('talents', [])),
            'powers': len(template_data.get('powers', [])),
            'modifiers': len(template_data.get('modifiers', [])),
            'disadvantages': len(template_data.get('disadvantages', [])),
        }


def main():
    """Test the HDT parser."""
    import json
    
    parser = HDTParser()
    
    # Test with Main6E.hdt
    hdt_path = "/tmp/hdt_files/Main6E.hdt"
    print(f"Parsing {hdt_path}...")
    
    template_data = parser.parse_file(hdt_path)
    
    # Print summary
    print("\nTemplate Summary:")
    summary = parser.summary(template_data)
    for section, count in summary.items():
        print(f"  {section}: {count}")
    
    # Print some sample data
    print("\n--- Sample Powers ---")
    for power in template_data['powers'][:5]:
        print(f"  {power['xmlid']}: {power['display']}")
        print(f"    Base Cost: {power['base_cost']}, Level Cost: {power['level_cost']}")
        print(f"    Types: {power['types']}")
        print(f"    Adders: {len(power['adders'])}, Modifiers: {len(power['modifiers'])}, Options: {len(power['options'])}")
    
    print("\n--- Sample Skills ---")
    for skill in template_data['skills'][:5]:
        print(f"  {skill['xmlid']}: {skill['display']}")
        print(f"    Characteristic Choice: {skill.get('characteristic_choice', [])}")
    
    print("\n--- Sample Global Modifiers ---")
    for mod in template_data['modifiers'][:5]:
        print(f"  {mod['xmlid']}: {mod['display']}")
        print(f"    Base Cost: {mod['base_cost']}")
        print(f"    Types: {mod['types']}")
        print(f"    Options: {len(mod['options'])}")


if __name__ == "__main__":
    main()

