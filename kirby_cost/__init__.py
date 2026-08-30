"""
kirby-cost Implementation

A Python library for HERO System 6E build and cost calculation.
Provides cost calculations, power system, and character management.
"""

# Read from the installed distribution rather than restated here. A literal
# drifted: it still said 0.1.0 across the 0.2.0 and 0.2.1 releases, so anything
# version-gating on kirby_cost.__version__ was told the wrong thing by PyPI.
# pyproject.toml is now the only place the number is written.
from importlib.metadata import PackageNotFoundError, version as _dist_version

try:
    __version__ = _dist_version("kirby-cost")
except PackageNotFoundError:  # running from a source tree that was never installed
    __version__ = "0.0.0.dev0"

del _dist_version, PackageNotFoundError

# Core system
from kirby_cost.core.context import EngineContext
from kirby_cost.core.preferences import Preferences
from kirby_cost.core.template import Template

# Base classes
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.adder import Adder

# Character model
from kirby_cost.model.rules import Rules

# I/O
from kirby_cost.io.xml_utility import XMLUtility

# Validation
from kirby_cost.validation import Verdict, check, allowed_modifiers, exclusive_conflict

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
    'Rules',
    # I/O
    'XMLUtility',
    # Validation -- the three doors a builder walks through (validation.py)
    'Verdict', 'check', 'allowed_modifiers', 'exclusive_conflict',
]



