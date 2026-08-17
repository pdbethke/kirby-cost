"""
Behavior Registry

Manages the mapping between power XMLIDs and their behavior implementations.
Supports both JSON-defined behaviors and Python class fallbacks.
"""

from typing import Dict, Any, Optional, Type, Callable, TYPE_CHECKING
from .schema import BehaviorSchema
from .engine import BehaviorEngine

if TYPE_CHECKING:
    from kirby_cost.objects.powers.power import Power
    from .plugins import PluginLoader


class BehaviorRegistry:
    """
    Registry for power behaviors.
    
    Behaviors can be:
    1. JSON definitions (stored in database, evaluated by BehaviorEngine)
    2. Python classes (fallback for complex behaviors)
    
    The registry checks for JSON behavior first, then falls back to Python class.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        
        # JSON behavior definitions (registered at runtime)
        self._json_behaviors: Dict[str, BehaviorSchema] = {}
        
        # Python class fallbacks
        self._class_behaviors: Dict[str, Type['Power']] = {}
        
        # Cache of instantiated engines
        self._engine_cache: Dict[str, BehaviorEngine] = {}
        
        # Plugin loader reference
        self._plugin_loader: Optional['PluginLoader'] = None
        
        # Load default Python class mappings
        self._load_class_fallbacks()
    
    def _load_class_fallbacks(self):
        """Load Python class fallbacks for complex powers."""
        # Import classes individually to handle missing ones gracefully
        self._class_behaviors = {}
        
        # Map of XMLID to module.class name
        class_mappings = {
            'ABSORPTION': ('absorption', 'Absorption'),
            'AID': ('aid', 'Aid'),
            'ARMOR': ('armor', 'Armor'),
            'CHANGEENVIRONMENT': ('change_environment', 'ChangeEnvironment'),
            'CLAIRSENTIENCE': ('clairsentience', 'Clairsentience'),
            'CLINGING': ('clinging', 'Clinging'),
            'COMPOUNDPOWER': ('compound_power', 'CompoundPower'),
            'CUSTOMPOWER': ('custom_power', 'CustomPower'),
            'DAMAGENEGATION': ('damage_negation', 'DamageNegation'),
            'DAMAGEREDUCTION': ('damage_reduction', 'DamageReduction'),
            'DAMAGERESISTANCE': ('damage_resistance', 'DamageResistance'),
            'DARKNESS': ('darkness', 'Darkness'),
            'DENSITYINCREASE': ('density_increase', 'DensityIncrease'),
            'DESOLIDIFICATION': ('desolidification', 'Desolidification'),
            'DISPEL': ('dispel', 'Dispel'),
            'DRAIN': ('drain', 'Drain'),
            'DUPLICATION': ('duplication', 'Duplication'),
            'EGOATTACK': ('ego_attack', 'EgoAttack'),
            'ENDURANCERESERVE': ('endurance_reserve', 'EnduranceReserve'),
            'ENERGYBLAST': ('energy_blast', 'EnergyBlast'),
            'ENTANGLE': ('entangle', 'Entangle'),
            'EXTRADIMENSIONALMOVEMENT': ('extra_dimensional_movement', 'ExtraDimensionalMovement'),
            'EXTRALIMBS': ('extra_limbs', 'ExtraLimbs'),
            'FLASH': ('flash', 'Flash'),
            'FLASHDEFENSE': ('flash_defense', 'FlashDefense'),
            'FLIGHT': ('flight', 'Flight'),
            'FORCEFIELD': ('force_field', 'ForceField'),
            'FORCEWALL': ('force_wall', 'ForceWall'),
            'GROWTH': ('growth', 'Growth'),
            'HANDTOHANDATTACK': ('hand_to_hand_attack', 'HandToHandAttack'),
            'HEALING': ('healing', 'Healing'),
            'IMAGES': ('images', 'Images'),
            'INVISIBILITY': ('invisibility', 'Invisibility'),
            'HKA': ('killing_attack_hth', 'KillingAttackHTH'),
            'RKA': ('killing_attack_ranged', 'KillingAttackRanged'),
            'KBRESISTANCE': ('knockback_resistance', 'KnockbackResistance'),
            'LIFESUPPORT': ('life_support', 'LifeSupport'),
            'LUCK': ('luck', 'Luck'),
            'MENTALDEFENSE': ('mental_defense', 'MentalDefense'),
            'MENTALILLUSIONS': ('mental_illusions', 'MentalIllusions'),
            'MINDCONTROL': ('mind_control', 'MindControl'),
            'MINDLINK': ('mind_link', 'MindLink'),
            'MINDSCAN': ('mind_scan', 'MindScan'),
            'MISSILEDEFLECTION': ('missile_deflection', 'MissileDeflection'),
            'MULTIFORM': ('multiform', 'Multiform'),
            'POSSESSION': ('possession', 'Possession'),
            'POWERDEFENSE': ('power_defense', 'PowerDefense'),
            'REFLECTION': ('reflection', 'Reflection'),
            'REGENERATION': ('regeneration', 'Regeneration'),
            'RUNNING': ('running', 'Running'),
            'SENSE': ('sense', 'Sense'),
            'SENSEGROUP': ('sense_group', 'SenseGroup'),
            'SHAPESHIFT': ('shape_shift', 'ShapeShift'),
            'SHRINKING': ('shrinking', 'Shrinking'),
            'STRETCHING': ('stretching', 'Stretching'),
            'SUMMON': ('summon', 'Summon'),
            'SWIMMING': ('swimming', 'Swimming'),
            'SWINGING': ('swinging', 'Swinging'),
            'TELEKINESIS': ('telekinesis', 'Telekinesis'),
            'TELEPATHY': ('telepathy', 'Telepathy'),
            'TELEPORTATION': ('teleportation', 'Teleportation'),
            'TRANSFORM': ('transform', 'Transform'),
            'TUNNELING': ('tunneling', 'Tunneling'),
        }
        
        for xmlid, (module_name, class_name) in class_mappings.items():
            try:
                module = __import__(
                    f'kirby_cost.objects.powers.{module_name}',
                    fromlist=[class_name]
                )
                power_class = getattr(module, class_name)
                self._class_behaviors[xmlid] = power_class
            except (ImportError, AttributeError):
                # Class not available - will use JSON behavior or generic
                pass
    
    def register_json_behavior(self, xmlid: str, behavior: BehaviorSchema):
        """Register a JSON behavior definition."""
        self._json_behaviors[xmlid.upper()] = behavior
        # Clear engine cache for this power
        if xmlid.upper() in self._engine_cache:
            del self._engine_cache[xmlid.upper()]
    
    def register_class_behavior(self, xmlid: str, power_class: Type['Power']):
        """Register a Python class behavior."""
        self._class_behaviors[xmlid.upper()] = power_class
    
    def behavior(self, xmlid: str) -> Optional[BehaviorEngine]:
        """
        Get behavior engine for a power.
        
        Returns BehaviorEngine if JSON behavior exists and doesn't require fallback.
        Returns None if should use Python class.
        """
        xmlid = xmlid.upper()
        
        # Check cache first
        if xmlid in self._engine_cache:
            return self._engine_cache[xmlid]
        
        # Check for JSON behavior
        if xmlid in self._json_behaviors:
            behavior = self._json_behaviors[xmlid]
            
            # Check if it requires class fallback
            if behavior.use_class_fallback:
                return None
            
            # Create and cache engine
            engine = BehaviorEngine(behavior)
            self._engine_cache[xmlid] = engine
            return engine
        
        # No JSON behavior - will use class fallback
        return None
    
    def get_class(self, xmlid: str) -> Optional[Type['Power']]:
        """Get Python class for a power."""
        xmlid = xmlid.upper()
        
        # Check plugin-provided classes first
        if self._plugin_loader:
            plugin_class = self._plugin_loader.power_class(xmlid)
            if plugin_class:
                return plugin_class
        
        # Fall back to built-in classes
        return self._class_behaviors.get(xmlid)
    
    def extension_methods(self, xmlid: str) -> Dict[str, Callable]:
        """Get plugin extension methods for a power."""
        if self._plugin_loader:
            return self._plugin_loader.extension_methods(xmlid)
        return {}
    
    def load_plugins(self, plugin_dir: str = None) -> int:
        """
        Load plugins from directory.
        
        Args:
            plugin_dir: Directory to load from (optional)
            
        Returns:
            Number of plugins loaded
        """
        from .plugins import get_plugin_loader, load_plugins
        
        self._plugin_loader = get_plugin_loader()
        return load_plugins(plugin_dir)
    
    def plugin_loader(self, loader: 'PluginLoader'):
        """Set the plugin loader reference."""
        self._plugin_loader = loader
    
    def has_behavior(self, xmlid: str) -> bool:
        """Check if any behavior (JSON or class) exists for this power."""
        xmlid = xmlid.upper()
        return xmlid in self._json_behaviors or xmlid in self._class_behaviors
    
    def list_json_behaviors(self) -> list:
        """List all registered JSON behaviors."""
        return list(self._json_behaviors.keys())
    
    def list_class_behaviors(self) -> list:
        """List all registered class behaviors."""
        return list(self._class_behaviors.keys())


# Global registry instance
_registry = None


def get_registry() -> BehaviorRegistry:
    """Get the global behavior registry."""
    global _registry
    if _registry is None:
        _registry = BehaviorRegistry()
    return _registry


def behavior(xmlid: str) -> Optional[BehaviorEngine]:
    """Convenience function to get behavior for a power."""
    return get_registry().behavior(xmlid)


def power_class(xmlid: str) -> Optional[Type['Power']]:
    """Convenience function to get Python class for a power."""
    return get_registry().get_class(xmlid)

