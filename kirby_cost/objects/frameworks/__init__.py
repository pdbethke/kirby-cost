"""
Frameworks package for kirby-cost.

Contains framework classes: Multipower, VPP, Elemental Control. Also exposes
module-level ``is_multipower``, ``is_vpp``, ``is_elemental_control`` predicates
used throughout the cost engine in place of the old duck-typed
``self._is_multipower(x)`` helpers.

The predicates are pure ``isinstance`` checks against the real framework
classes — faster and safer than the old
``obj.xmlid == "MULTIPOWER" or type(obj).__name__ == "Multipower"`` pattern.
The ``hdc_loader`` instantiates the real framework classes (see
``_FRAMEWORK_CLASSES`` in ``io/hdc_loader.py``), so no xmlid-string fallback
is needed.
"""

from kirby_cost.objects.frameworks.multipower import Multipower
from kirby_cost.objects.frameworks.vpp import VariablePowerPool
from kirby_cost.objects.frameworks.elemental_control import ElementalControl


def is_multipower(obj) -> bool:
    """True if ``obj`` is a Multipower framework instance."""
    return obj is not None and isinstance(obj, Multipower)


def is_vpp(obj) -> bool:
    """True if ``obj`` is a Variable Power Pool framework instance."""
    return obj is not None and isinstance(obj, VariablePowerPool)


def is_elemental_control(obj) -> bool:
    """True if ``obj`` is an Elemental Control framework instance."""
    return obj is not None and isinstance(obj, ElementalControl)


__all__ = [
    'Multipower',
    'VariablePowerPool',
    'ElementalControl',
    'is_multipower',
    'is_vpp',
    'is_elemental_control',
]
