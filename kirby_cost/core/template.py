"""
Template class for kirby-cost.

Represents a character template (HDT file) that defines available
powers, skills, modifiers, and their costs.
"""

from typing import List, Optional
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.adder import Adder


class Template:
    """
    Character template containing available game elements.
    
    Templates define what powers, skills, modifiers, and adders
    are available for character creation.
    """
    
    def __init__(self):
        """Initialize an empty template."""
        self._modifiers: List[Modifier] = []
        self._adders: List[Adder] = []
        self._powers: List[GenericObject] = []
        self._skills: List[GenericObject] = []
        self._name: str = ""
        self._version: str = "6.0"
    
    @property
    def modifiers(self) -> List[Modifier]:
        """Get list of available modifiers."""
        return list(self._modifiers)
    
    def add_modifier(self, modifier: Modifier) -> None:
        """Add a modifier to the template."""
        if modifier not in self._modifiers:
            self._modifiers.append(modifier)
    
    @property
    def adders(self) -> List[Adder]:
        """Get list of available adders."""
        return list(self._adders)
    
    def add_adder(self, adder: Adder) -> None:
        """Add an adder to the template."""
        if adder not in self._adders:
            self._adders.append(adder)
    
    @property
    def powers(self) -> List[GenericObject]:
        """Get list of available power definitions."""
        return list(self._powers)
    
    def add_power(self, power: GenericObject) -> None:
        """Add a power definition to the template."""
        if power not in self._powers:
            self._powers.append(power)
    
    @property
    def skills(self) -> List[GenericObject]:
        """Get list of available skill definitions."""
        return list(self._skills)
    
    def add_skill(self, skill: GenericObject) -> None:
        """Add a skill definition to the template."""
        if skill not in self._skills:
            self._skills.append(skill)
    
    @property
    def name(self) -> str:
        """Get template name."""
        return self._name
    
    def name(self, name: str) -> None:
        """Set template name."""
        self._name = name
    
    @property
    def version(self) -> str:
        """Get template version."""
        return self._version
    
    @version.setter
    def version(self, version: str) -> None:
        """Set template version."""
        self._version = version



