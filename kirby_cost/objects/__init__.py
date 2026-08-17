"""
Objects package for kirby-cost.

Contains all game objects: powers, skills, modifiers, adders, etc.
"""

from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.char_affecting import CharAffectingObject
from kirby_cost.objects.adder import Adder
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.list import List
from kirby_cost.objects.powers.power import Power
from kirby_cost.objects.frameworks.multipower import Multipower
from kirby_cost.objects.frameworks.vpp import VariablePowerPool
from kirby_cost.objects.frameworks.elemental_control import ElementalControl

__all__ = [
    'GenericObject',
    'CharAffectingObject',
    'Adder',
    'Modifier',
    'List',
    'Power',
    'Multipower',
    'VariablePowerPool',
    'ElementalControl',
]

