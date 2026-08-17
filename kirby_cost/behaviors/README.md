# Hero Designer Power Behavior System

A hybrid system for defining and executing power mechanics that supports:
1. **JSON-defined behaviors** - Data-driven, easily modifiable
2. **Python class behaviors** - Fallback for complex logic
3. **Plugin extensions** - Custom powers and methods

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PowerInstance                            │
│  Unified API for working with powers                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │    JSON     │   │   Python    │   │   Plugin    │       │
│  │  Behavior   │ → │   Class     │ → │  Extension  │       │
│  │  (Primary)  │   │ (Fallback)  │   │  (Add-ons)  │       │
│  └─────────────┘   └─────────────┘   └─────────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```python
from kirby_cost.behaviors import (
    create_power,
    load_plugins,
    get_registry,
)
from kirby_cost.behaviors.schema import BehaviorSchema

# Load plugins (optional)
load_plugins()

# Create a power instance
blast = create_power('ENERGYBLAST', levels=10, name='Plasma Bolt')

# Use unified API
print(blast.get_damage_display())  # "10d6"
print(blast.get_end_cost())        # 6
print(blast.get_display())         # Full display string
```

## JSON Behavior Definitions

Define power mechanics in JSON:

```python
energy_blast_behavior = {
    "xmlid": "ENERGYBLAST",
    "power_type": "attack",
    "damage": {
        "dice_formula": "levels",  # 1d6 per level
        "damage_type": "normal",
        "stun_multiplier": 1.0,
    },
    "endurance": {
        "formula": "max(1, floor(active_cost / 10))",
    },
    "display": {
        "column2_format": "{name}: {dice}d6",
    },
    "validation": [
        {
            "rule": "levels > 0",
            "message": "Energy Blast requires at least 1 level",
        },
    ],
}

# Register with the system
behavior = BehaviorSchema.from_dict(energy_blast_behavior)
get_registry().register_json_behavior('ENERGYBLAST', behavior)
```

## Python Class Fallback

For complex powers, Python classes provide full flexibility:

```python
from kirby_cost.objects.powers.power import Power

class Aid(Power):
    XMLID = "AID"
    
    def get_column2_output(self):
        return f"{self.name}: Aid {self.input} {self.get_levels()}d6"
    
    def get_end_usage(self):
        # Complex calculation with modifiers
        ...
```

The system automatically uses Python classes when:
- No JSON behavior is defined
- The JSON behavior specifies `use_class_fallback: true`

## Plugin System

### Creating a Plugin

Place Python files in `kirby_cost/plugins/powers/`:

```python
# my_power.py

PLUGIN_NAME = "My Custom Powers"
PLUGIN_VERSION = "1.0"
PLUGIN_AUTHOR = "Your Name"

from kirby_cost.objects.powers.power import Power
from kirby_cost.behaviors.plugins import PowerExtension

# Full power class
class MyPower(Power):
    XMLID = "MYPOWER"
    
    def get_column2_output(self):
        return f"{self.name}: Custom effect"

# Extension for existing powers
class BlastExtension(PowerExtension):
    APPLIES_TO = ["ENERGYBLAST", "RKA"]
    
    @staticmethod
    def calculate_armor_piercing(power_data: dict) -> int:
        return power_data.get('levels', 0) * 2

# Custom calculations
CUSTOM_CALCULATIONS = {
    'special_damage': lambda data: data.get('levels', 0) * 3,
}
```

### Loading Plugins

```python
from kirby_cost.behaviors import load_plugins, get_plugin_loader

# Load from default directories
count = load_plugins()

# Load from custom directory
count = load_plugins('/path/to/plugins')

# List loaded plugins
loader = get_plugin_loader()
for plugin in loader.list_plugins():
    print(f"{plugin['name']} v{plugin['version']}")
```

### Using Extension Methods

```python
power = create_power('COUGHING', levels=8)

# Check for extensions
if power.has_extension('calculate_contagion_chance'):
    chance = power.calculate_contagion_chance()

# List available extensions
print(power.list_extensions())
```

## Priority Order

When creating a `PowerInstance`, the system checks in order:

1. **JSON Behavior** - If defined in the registry
2. **Plugin Power Class** - If provided by a loaded plugin
3. **Built-in Python Class** - From `kirby_cost.objects.powers`
4. **Generic Fallback** - Basic functionality for unknown powers

## Expression Engine

JSON behaviors can use expressions:

```python
{
    "endurance": {
        "formula": "max(1, floor(active_cost / 10))",
    },
    "damage": {
        "dice_formula": "levels + bonus_dice",
    },
}
```

Supported operations:
- Arithmetic: `+`, `-`, `*`, `/`, `//`
- Comparison: `<`, `>`, `<=`, `>=`, `==`, `!=`
- Functions: `min`, `max`, `floor`, `ceil`, `abs`, `round`
- Variables: Any key from `power_data` dictionary

## Files

- `schema.py` - JSON behavior schema definitions
- `engine.py` - Expression evaluation engine
- `registry.py` - Behavior registration and lookup
- `power_instance.py` - Unified power API
- `plugins.py` - Plugin loading system

