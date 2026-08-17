"""
I/O package for kirby-cost.

This package contains utilities for reading and writing Hero Designer files.

Spec-1 public surface (build doc + cost) is importable directly from
this package. Imports are deferred via __getattr__ to break the circular dependency:
  kirby_cost.objects.base → kirby_cost.io.xml_utility
which is hit when kirby_cost/__init__.py loads the objects package at startup.
Deferring means `import kirby_cost.io` (the package) does NOT immediately pull
build_json/hdc_loader, so the cycle never forms.
"""

from kirby_cost.io.xml_utility import XMLUtility

__all__ = [
    # Always eagerly available (no cycle risk)
    'XMLUtility',
    # The primary entry point: read an .hdc into costed objects
    'HDCLoader',
    # Spec-1: build doc (JSON) <-> build engine
    'build_from_json',
    'to_build_json',
    'BuildDocError',
    # Spec-1: cost service
    'cost_build',
    'extract_costs',
    'CostResult',
    # Spec-1: build node (build tree primitive)
    'BuildNode',
]

# Lazy import map: attribute name -> (module, attribute)
_LAZY = {
    'build_from_json': ('kirby_cost.io.build_json', 'build_from_json'),
    'to_build_json':   ('kirby_cost.io.build_json', 'to_build_json'),
    'BuildDocError':   ('kirby_cost.io.build_json', 'BuildDocError'),
    'cost_build':      ('kirby_cost.io.build_cost', 'cost_build'),
    'extract_costs':   ('kirby_cost.io.build_cost', 'extract_costs'),
    'CostResult':      ('kirby_cost.io.build_cost', 'CostResult'),
    'BuildNode':       ('kirby_cost.io.hdc_loader', 'BuildNode'),
    'HDCLoader':       ('kirby_cost.io.hdc_loader', 'HDCLoader'),
}


def __getattr__(name: str):
    if name in _LAZY:
        mod_path, attr = _LAZY[name]
        import importlib
        mod = importlib.import_module(mod_path)
        return getattr(mod, attr)
    raise AttributeError(f"module 'kirby_cost.io' has no attribute {name!r}")
