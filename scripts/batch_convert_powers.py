#!/usr/bin/env python3
"""
Batch power converter script.

Generates Python power classes from templates.
"""

import os
from pathlib import Path

# Simple power classes (just extend Power with XMLID)
SIMPLE_POWERS = [
    ("Swinging", "SWINGING", "Movement power for swinging on lines.", True, True),
    ("Stretching", "STRETCHING", "Power to extend limbs/body.", False, False),
    ("Tunneling", "TUNNELING", "Power to tunnel through materials.", True, False),
    ("ExtraDimensionalMovement", "EXTRADIMENSIONALMOVEMENT", "Power to travel to other dimensions.", False, False),
    ("FTLTravel", "FTL", "Faster-than-light travel power.", False, False),
    ("KBResistance", "KBRESISTANCE", "Resistance to knockback.", False, False),
    ("Luck", "LUCK", "Luck power.", False, False),
    ("ExtraLimbs", "EXTRALIMBS", "Power to have extra limbs.", False, False),
    ("LifeSupport", "LIFESUPPORT", "Life support power.", False, False),
    ("Reflection", "REFLECTION", "Ability to reflect attacks.", False, False),
]

# Powers with movement display
MOVEMENT_POWERS = [
    ("Swinging", "SWINGING", "Movement power for swinging on lines."),
    ("Stretching", "STRETCHING", "Power to extend limbs/body."),
]

# Powers with simple damage display
DAMAGE_POWERS = [
    ("PowerDefense", "POWERDEFENSE", "Defense against power attacks.", "points"),
    ("Reflection", "REFLECTION", "Ability to reflect attacks.", "Active Points' worth"),
]

def generate_simple_power(name, xmlid, description, affects_primary=False, is_summable=False):
    """Generate a simple power class."""
    template = f'''"""
{name} power class for kirby-cost.

Converted from com.hero.objects.powers.{name}.java

{description}
"""

from kirby_cost.objects.powers.power import Power
'''
    
    if affects_primary or is_summable:
        template += "from kirby_cost.util.rounder import round_down\n"
    
    template += f'''

class {name}(Power):
    """
    {name} power.
    
    {description}
    """
    
    XMLID = "{xmlid}"
    
    def __init__(self):
        """Initialize a {name} power."""
        super().__init__()
        self.xmlid = {name}.XMLID
'''
    
    if affects_primary:
        template += "        self.affects_primary = True\n"
    
    if is_summable:
        template += "        self.duration = \"CONSTANT\"\n"
    
    # Add get_damage_display if needed
    if name in ["Swinging", "Stretching"]:
        template += '''    
    def get_damage_display(self) -> str:
        """Get movement display string."""
        movement = int(round_down(float(self.get_levels()) / self.get_level_value())) if self.get_level_value() != 0.0 else self.get_levels()
        is_6e = True  # Stub: would check if 6E
        return f"{movement}m" if is_6e else f'{movement}"'
    
    def is_summable(self) -> bool:
        """Check if can be summed with other movement powers."""
        return True
'''
    elif name == "KBResistance":
        template += '''    
    def get_damage_display(self) -> str:
        """Get KB resistance display."""
        is_6e = True  # Stub: would check if 6E
        return f"-{self.get_levels()}m" if is_6e else f'-{self.get_levels()}"'
'''
    elif name == "FTLTravel":
        template += '''    
    def get_damage_display(self) -> str:
        """Get FTL travel display."""
        from kirby_cost.util.rounder import round_down, round_half_up
        import math
        d = math.pow(self.level_power, round_down(float(self.get_levels()) / self.get_level_value()))
        # Stub: would format time units (year, day, hour, etc.)
        return f"({d} Light Years/year)"
'''
    elif name == "ExtraDimensionalMovement":
        template += '''    
    def get_damage_display(self) -> str:
        """Get damage display (empty for EDM)."""
        return ""
'''
    elif name == "PowerDefense":
        template += '''    
    def get_damage_display(self) -> str:
        """Get defense display."""
        return f"{self.get_levels()} points"
'''
    elif name == "Reflection":
        template += '''    
    def get_damage_display(self) -> str:
        """Get reflection display."""
        return f"{self.get_levels()} Active Points' worth"
'''
    elif name == "ExtraLimbs":
        template += '''    
    def get_damage_display(self) -> str:
        """Get damage display (empty for Extra Limbs)."""
        return ""
    
    def get_column2_output(self) -> str:
        """Get column 2 output with limb count."""
        output = f"{self.alias} {self.get_damage_display()}"
        if self.name and self.name.strip():
            output = f"<i>{self.name}:</i>  {output}"
        if self.get_levels() == 1 and output.upper().endswith("S"):
            output = output[:-1]
        if self.get_levels() > 0:
            output += f" ({self.get_levels()})"
        if self.input and self.input.strip():
            output += f":  {self.input}"
        if self.selected_option:
            output += f" ({self.selected_option.alias})"
        adder_str = self.get_adder_string()
        if adder_str and adder_str.strip():
            output += f", {adder_str}"
        modifier_str = self.get_modifier_string()
        output += modifier_str
        return output
    
    def get_adder_string(self) -> str:
        """Get adder string (stub)."""
        return ""
    
    def get_modifier_string(self) -> str:
        """Get modifier string (stub)."""
        return ""
'''
    elif name == "LifeSupport":
        template += '''    
    def get_damage_display(self) -> str:
        """Get damage display (empty for Life Support)."""
        return ""
'''
    elif name == "Luck":
        template += '''    
    def get_damage_display(self) -> str:
        """Get damage display (empty for Luck)."""
        return ""
'''
    
    return template

def main():
    """Generate all simple power classes."""
    powers_dir = Path("kirby_cost/objects/powers")
    
    for name, xmlid, desc, affects_primary, is_summable in SIMPLE_POWERS:
        content = generate_simple_power(name, xmlid, desc, affects_primary, is_summable)
        filename = powers_dir / f"{name.lower()}.py"
        filename.write_text(content)
        print(f"Generated {filename}")

if __name__ == "__main__":
    main()

