"""
Power Instance

Represents a power on a character, combining template data with behavior.
Uses JSON behavior if available, falls back to Python class otherwise.
"""

from typing import Dict, Any, Optional, List, Callable, TYPE_CHECKING
from .registry import get_registry, behavior, power_class
from .engine import BehaviorEngine

if TYPE_CHECKING:
    from kirby_cost.objects.powers.power import Power


class PowerInstance:
    """
    A power instance on a character.
    
    This is the main interface for working with powers. It:
    1. Checks for JSON behavior definition
    2. Falls back to Python class if needed
    3. Supports plugin extension methods
    4. Provides unified API regardless of implementation
    """
    
    def __init__(self, xmlid: str, character_data: Dict[str, Any] = None,
                 template_def: Any = None):
        """
        Create a power instance.
        
        Args:
            xmlid: Power XMLID (e.g., 'ENERGYBLAST')
            character_data: Character-specific configuration (levels, adders, etc.)
            template_def: Template definition supplied by the caller (optional)
        """
        self.xmlid = xmlid.upper()
        self.character_data = character_data or {}
        self.template_def = template_def
        
        # Try to get JSON behavior
        self._behavior_engine: Optional[BehaviorEngine] = behavior(self.xmlid)
        
        # If no JSON behavior or it requires fallback, use Python class
        self._python_instance: Optional['Power'] = None
        if self._behavior_engine is None:
            # NOT `power_class = power_class(...)`. Assigning to the name makes
            # it local for the whole function, so the call on the right-hand
            # side raises UnboundLocalError and this fallback — the one the
            # module docstring advertises — could never run.
            cls = power_class(self.xmlid)
            if cls:
                self._python_instance = cls()
                self._apply_character_data_to_instance()
        
        # Track which implementation we're using
        self._using_json = self._behavior_engine is not None
        
        # Load extension methods from plugins
        self._extension_methods = get_registry().extension_methods(self.xmlid)
    
    def _apply_character_data_to_instance(self):
        """Apply character data to Python power instance."""
        if not self._python_instance:
            return
        
        # Set basic attributes
        self._python_instance.levels = self.character_data.get('levels', 0)
        self._python_instance.name = self.character_data.get('name', '')
        self._python_instance.alias = self.character_data.get('alias', '')
        self._python_instance.input = self.character_data.get('input', '')
        
        # Set cost-related attributes
        self._python_instance.base_cost = self.character_data.get('base_cost', 0)
        self._python_instance.level_cost = self.character_data.get('level_cost', 0)
        
        # TODO: Apply adders and modifiers
    
    @property
    def using_json_behavior(self) -> bool:
        """Check if using JSON behavior (vs Python class)."""
        return self._using_json
    
    @property
    def using_python_class(self) -> bool:
        """Check if using Python class fallback."""
        return self._python_instance is not None
    
    # =========================================================================
    # Unified API - works with both JSON and Python implementations
    # =========================================================================
    
    @property
    def display(self) -> str:
        """Get display string for the power."""
        if self._behavior_engine:
            return self._behavior_engine.display(self.character_data)
        elif self._python_instance:
            return self._python_instance.column2_output
        else:
            return self.character_data.get('alias', self.xmlid)
    
    @property
    def damage(self) -> Dict[str, Any]:
        """Get damage calculation."""
        if self._behavior_engine:
            return self._behavior_engine.calculate_damage(self.character_data)
        elif self._python_instance:
            # Extract from Python class
            dice = self._python_instance.levels
            return {
                'dice': dice,
                'pips': 0,
                'damage_type': 'normal',
            }
        else:
            return {'dice': 0, 'pips': 0, 'damage_type': 'normal'}
    
    @property
    def damage_display(self) -> str:
        """Get formatted damage string (e.g., '8d6')."""
        damage = self.damage
        dice = damage.get('dice', 0)
        pips = damage.get('pips', 0)
        
        full_dice = int(dice)
        half_die = dice - full_dice >= 0.5
        
        parts = []
        if full_dice > 0:
            parts.append(f"{full_dice}d6")
        if half_die:
            parts.append("½d6")
        if pips > 0:
            parts.append(f"+{pips}")
        elif pips < 0:
            parts.append(str(pips))
        
        return ''.join(parts) if parts else "0d6"
    
    @property
    def defense(self) -> Dict[str, Any]:
        """Get defense calculation."""
        if self._behavior_engine:
            return self._behavior_engine.calculate_defense(self.character_data)
        elif self._python_instance:
            # Try to extract from Python class
            if hasattr(self._python_instance, 'pd'):
                return {
                    'pd': self._python_instance.get_pd(),
                    'ed': self._python_instance.get_ed() if hasattr(self._python_instance, 'ed') else 0,
                    'md': 0,
                }
        return {'pd': 0, 'ed': 0, 'md': 0}
    
    @property
    def end_cost(self) -> int:
        """Get END cost."""
        if self._behavior_engine:
            return self._behavior_engine.calculate_endurance(self.character_data)
        elif self._python_instance:
            return self._python_instance.end_usage
        else:
            # Default calculation
            active_cost = self.character_data.get('active_cost', 0)
            return max(1, int((active_cost + 5) / 10))
    
    @property
    def active_cost(self) -> float:
        """Get active cost."""
        if self._python_instance:
            return self._python_instance.active_cost
        else:
            return self.character_data.get('active_cost', 0)
    
    @property
    def real_cost(self) -> float:
        """Get real cost."""
        if self._python_instance:
            return self._python_instance.real_cost
        else:
            return self.character_data.get('real_cost', 0)
    
    def validate(self) -> List[str]:
        """
        Validate power configuration.
        
        Returns:
            List of error messages (empty if valid)
        """
        if self._behavior_engine:
            return self._behavior_engine.validate(self.character_data)
        elif self._python_instance:
            # Python classes might have validation
            if hasattr(self._python_instance, 'validate'):
                return self._python_instance.validate()
        return []
    
    def calculate_custom(self, calculation_name: str, 
                         power_data: Dict[str, Any] = None) -> Any:
        """
        Run a custom calculation defined in the behavior.
        
        Args:
            calculation_name: Name of the custom calculation
            power_data: Optional override for character data
            
        Returns:
            Calculated value
        """
        data = power_data or self.character_data
        
        if self._behavior_engine:
            return self._behavior_engine.calculate_custom(
                calculation_name, data
            )
        return 0
    
    def call_extension(self, method_name: str, *args, **kwargs) -> Any:
        """
        Call a plugin extension method.
        
        Args:
            method_name: Name of the extension method
            *args, **kwargs: Arguments to pass to the method
            
        Returns:
            Result from the extension method
        """
        if method_name in self._extension_methods:
            method = self._extension_methods[method_name]
            # Pass self.character_data as first argument
            return method(self.character_data, *args, **kwargs)
        raise AttributeError(f"No extension method '{method_name}' for {self.xmlid}")
    
    def has_extension(self, method_name: str) -> bool:
        """Check if an extension method exists."""
        return method_name in self._extension_methods
    
    def list_extensions(self) -> List[str]:
        """List available extension methods."""
        return list(self._extension_methods.keys())
    
    def __getattr__(self, name: str) -> Any:
        """
        Allow calling extension methods directly on the instance.
        
        Example:
            power.calculate_infection_chance()  # Calls extension method
        """
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")
        
        # Check extension methods
        if hasattr(self, '_extension_methods') and name in self._extension_methods:
            method = self._extension_methods[name]
            # Return a bound method-like callable
            def bound_method(*args, **kwargs):
                return method(self.character_data, *args, **kwargs)
            return bound_method
        
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")
    
    # =========================================================================
    # Data access
    # =========================================================================
    
    @property
    def levels(self) -> int:
        """Get power levels."""
        return self.character_data.get('levels', 0)

    @levels.setter
    def levels(self, levels: int):
        """Set power levels."""
        self.character_data['levels'] = levels
        if self._python_instance:
            self._python_instance.levels = levels

    @property
    def name(self) -> str:
        """Get power name."""
        return self.character_data.get('name', '')

    @name.setter
    def name(self, name: str):
        """Set power name."""
        self.character_data['name'] = name
        if self._python_instance:
            self._python_instance.name = name
    
    @property
    def adders(self) -> List[Dict[str, Any]]:
        """Get assigned adders."""
        return self.character_data.get('adders', [])
    
    @property
    def modifiers(self) -> List[Dict[str, Any]]:
        """Get assigned modifiers."""
        return self.character_data.get('modifiers', [])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'xmlid': self.xmlid,
            'using_json_behavior': self._using_json,
            'character_data': self.character_data,
            'display': self.display,
            'damage': self.damage,
            'end_cost': self.end_cost,
            'active_cost': self.active_cost,
            'real_cost': self.real_cost,
        }
    
    def __repr__(self) -> str:
        impl = "JSON" if self._using_json else "Python" if self._python_instance else "None"
        return f"<PowerInstance {self.xmlid} ({impl}) levels={self.levels}>"


def create_power(xmlid: str, levels: int = 0, name: str = '',
                 adders: List[Dict] = None, modifiers: List[Dict] = None,
                 **kwargs) -> PowerInstance:
    """
    Convenience function to create a power instance.
    
    Args:
        xmlid: Power XMLID
        levels: Number of levels
        name: Custom name for the power
        adders: List of adder configurations
        modifiers: List of modifier configurations
        **kwargs: Additional character data
        
    Returns:
        PowerInstance
    """
    character_data = {
        'levels': levels,
        'name': name,
        'adders': adders or [],
        'modifiers': modifiers or [],
        **kwargs
    }
    return PowerInstance(xmlid, character_data)

