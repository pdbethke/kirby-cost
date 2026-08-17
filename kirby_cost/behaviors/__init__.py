"""
Power Behavior System

A hybrid system that supports:
1. JSON-defined behaviors (data-driven, easily modifiable)
2. Python class behaviors (fallback for complex logic)
3. Plugin-based custom powers and extensions

The system checks for a JSON behavior definition first. If not found
or if the definition specifies 'use_class_fallback': true, it falls
back to the corresponding Python class.

Plugins can provide:
- Full power class implementations
- Extension methods for JSON-defined powers
- Custom calculation functions
"""

from .schema import BehaviorSchema
from .engine import BehaviorEngine
from .registry import BehaviorRegistry, behavior, get_registry
from .power_instance import PowerInstance, create_power
from .plugins import (
    PluginLoader,
    PluginMetadata,
    PowerExtension,
    get_plugin_loader,
    load_plugins,
)

__all__ = [
    # Schema and engine
    'BehaviorSchema',
    'BehaviorEngine', 
    
    # Registry
    'BehaviorRegistry',
    'behavior',
    'get_registry',
    
    # Power instances
    'PowerInstance',
    'create_power',
    
    # Plugin system
    'PluginLoader',
    'PluginMetadata',
    'PowerExtension',
    'get_plugin_loader',
    'load_plugins',
]

