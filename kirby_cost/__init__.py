"""
kirby-cost Implementation

A Python library for HERO System 6E build and cost calculation.
Provides cost calculations, power system, and character management.
"""

__version__ = "0.1.0"

# Core system
from kirby_cost.core.context import EngineContext
from kirby_cost.core.preferences import Preferences
from kirby_cost.core.template import Template

# Base classes
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.adder import Adder

# Character model
from kirby_cost.model.hero import Hero
from kirby_cost.model.rules import Rules

# I/O
from kirby_cost.io.xml_utility import XMLUtility

__all__ = [
    # Core
    'EngineContext',
    'Preferences',
    'Template',
    # Base classes
    'GenericObject',
    'Modifier',
    'Adder',
    # Character model
    'Hero',
    'Rules',
    # I/O
    'XMLUtility',
]



