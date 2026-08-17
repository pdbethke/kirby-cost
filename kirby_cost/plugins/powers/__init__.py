"""
Custom Power Plugins

Place your custom power classes here. Each .py file will be loaded as a plugin.

Example plugin structure:

    # my_power.py
    
    PLUGIN_NAME = "My Custom Powers"
    PLUGIN_VERSION = "1.0"
    PLUGIN_AUTHOR = "Your Name"
    PLUGIN_DESCRIPTION = "Custom powers for my campaign"
    
    from kirby_cost.objects.powers.power import Power
    from kirby_cost.behaviors.plugins import PowerExtension
    
    class MyPower(Power):
        XMLID = "MYPOWER"
        
        def get_column2_output(self):
            return f"{self.name}: Custom power effect"
    
    # Or create an extension for existing powers:
    class BlastExtension(PowerExtension):
        APPLIES_TO = ["ENERGYBLAST", "RKA"]
        
        @staticmethod
        def calculate_armor_piercing(power_data: dict) -> int:
            # Custom calculation
            return power_data.get('levels', 0) * 2
"""

