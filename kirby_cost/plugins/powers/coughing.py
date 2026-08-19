"""
Coughing Power Plugin

A custom power that demonstrates the plugin system.
This power causes area-effect damage and can spread contagion.
"""

PLUGIN_NAME = "Coughing Power"
PLUGIN_VERSION = "1.0"
PLUGIN_AUTHOR = "Hero Designer"
PLUGIN_DESCRIPTION = "A devastating coughing attack power with contagion effects"

from kirby_cost.objects.powers.power import Power
from kirby_cost.behaviors.plugins import PowerExtension


class Coughing(Power, xmlid="COUGHING"):
    """
    Coughing Attack Power
    
    The character can cough with devastating effect, projecting a cloud 
    of germs and irritants at their foes.
    """
    
    def __init__(self):
        super().__init__()
        self.xmlid = Coughing.XMLID
        self._duration = "INSTANT"
        self.is_area_effect = True
        self.contagion_chance = 0
    
    @property
    def alias(self) -> str:
        """Get power alias."""
        return self._alias or "Coughing Attack"
    
    @property
    def damage_display(self) -> str:
        """Get damage dice display."""
        dice = self._levels
        half_die = ""
        
        for adder in self.assigned_adders:
            if adder.xmlid == "PLUSONEHALFDIE":
                half_die = "½d6"
        
        return f"{dice}d6{half_die}"
    
    @property
    def column2_output(self) -> str:
        """Get display string for character sheet."""
        output = self._alias
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i> {output}"
        
        output += f" {self.damage_display}"
        
        # Add area effect indicator
        output += " (Area Effect: Cone)"
        
        # Add contagion info if applicable
        contagion = self.calculate_contagion_chance()
        if contagion > 0:
            output += f", {contagion}% Contagion"
        
        # Add modifier string
        modifier_str = self.modifier_string
        if modifier_str:
            output += modifier_str
        
        return output
    
    def calculate_contagion_chance(self) -> int:
        """
        Calculate the chance of spreading contagion.
        
        Base: 5% per die
        With Contagious adder: doubles the chance
        """
        base_chance = self._levels * 5
        
        for adder in self.assigned_adders:
            if adder.xmlid == "CONTAGIOUS":
                base_chance *= 2
        
        return min(base_chance, 100)  # Cap at 100%
    
    @property
    def area_effect_radius(self) -> int:
        """Calculate area effect radius in meters."""
        # 2m per die
        return self._levels * 2
    


class CoughingExtension(PowerExtension):
    """
    Extension methods for Coughing power.
    
    These methods are available even when using JSON behavior.
    """
    
    APPLIES_TO = ["COUGHING"]
    
    @staticmethod
    def calculate_contagion_chance(power_data: dict) -> int:
        """
        Calculate contagion spread chance.
        
        Args:
            power_data: Power configuration dictionary
            
        Returns:
            Percentage chance (0-100)
        """
        levels = power_data.get('levels', 0)
        base_chance = levels * 5
        
        # Check for Contagious adder
        for adder in power_data.get('adders', []):
            if adder.get('xmlid', '').upper() == 'CONTAGIOUS':
                base_chance *= 2
                break
        
        return min(base_chance, 100)
    
    @staticmethod
    def calculate_area_radius(power_data: dict) -> int:
        """
        Calculate area effect radius.
        
        Args:
            power_data: Power configuration dictionary
            
        Returns:
            Radius in meters
        """
        return power_data.get('levels', 0) * 2
    
    @staticmethod
    def apply_contagion_effect(power_data: dict, target: dict) -> dict:
        """
        Apply contagion effect to a target.
        
        Args:
            power_data: Power configuration
            target: Target character data
            
        Returns:
            Effect result dictionary
        """
        import random
        
        chance = CoughingExtension.calculate_contagion_chance(power_data)
        roll = random.randint(1, 100)
        
        infected = roll <= chance
        
        return {
            'infected': infected,
            'roll': roll,
            'chance': chance,
            'duration_turns': power_data.get('levels', 0) if infected else 0,
        }


# Custom calculations that can be used in JSON behaviors
CUSTOM_CALCULATIONS = {
    'contagion_chance': lambda data: min(data.get('levels', 0) * 5, 100),
    'area_radius': lambda data: data.get('levels', 0) * 2,
}

