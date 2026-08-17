"""
Plugin System for Custom Power Behaviors

Allows loading custom Python power classes from:
1. A plugins directory (file-based plugins)
2. Database-stored Python code (dynamic plugins)
3. Registered modules (programmatic plugins)

Plugins can provide:
- Full power class implementations
- Extension methods for JSON-defined powers
- Custom calculation functions
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Type, Callable, List, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from kirby_cost.objects.powers.power import Power

logger = logging.getLogger(__name__)


class PluginMetadata:
    """Metadata about a loaded plugin."""
    
    def __init__(self, name: str, version: str = "1.0", 
                 author: str = "", description: str = "",
                 source: str = "file"):
        self.name = name
        self.version = version
        self.author = author
        self.description = description
        self.source = source  # file, database, module
        self.power_classes: List[str] = []
        self.extensions: List[str] = []
        self.calculations: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'version': self.version,
            'author': self.author,
            'description': self.description,
            'source': self.source,
            'power_classes': self.power_classes,
            'extensions': self.extensions,
            'calculations': self.calculations,
        }


class PowerExtension:
    """
    Base class for power extensions.
    
    Extensions add methods to JSON-defined powers without
    requiring a full Python class.
    """
    
    # XMLID(s) this extension applies to
    APPLIES_TO: List[str] = []
    
    @classmethod
    def extension_methods(cls) -> Dict[str, Callable]:
        """
        Return dict of method_name -> callable.
        
        These methods will be available on PowerInstance.
        """
        methods = {}
        for name in dir(cls):
            if name.startswith('_'):
                continue
            attr = getattr(cls, name)
            if callable(attr) and name not in ('get_extension_methods',):
                methods[name] = attr
        return methods


class PluginLoader:
    """
    Loads and manages power plugins.
    """
    
    def __init__(self):
        self._loaded_plugins: Dict[str, PluginMetadata] = {}
        self._power_classes: Dict[str, Type['Power']] = {}
        self._extensions: Dict[str, Dict[str, Callable]] = {}  # xmlid -> {method_name -> callable}
        self._custom_calculations: Dict[str, Callable] = {}
        self._plugin_dirs: List[Path] = []
    
    def add_plugin_directory(self, path: str):
        """Add a directory to search for plugins."""
        plugin_path = Path(path)
        if plugin_path.exists() and plugin_path.is_dir():
            self._plugin_dirs.append(plugin_path)
            logger.info(f"Added plugin directory: {plugin_path}")
    
    def load_all_plugins(self) -> int:
        """
        Load all plugins from registered directories.
        
        Returns:
            Number of plugins loaded
        """
        count = 0
        for plugin_dir in self._plugin_dirs:
            count += self._load_plugins_from_directory(plugin_dir)
        return count
    
    def _load_plugins_from_directory(self, plugin_dir: Path) -> int:
        """Load plugins from a specific directory."""
        count = 0
        
        # Load single-file plugins
        for py_file in plugin_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            try:
                if self._load_plugin_file(py_file):
                    count += 1
            except (ImportError, SyntaxError, AttributeError, OSError) as e:
                logger.error(f"Error loading plugin {py_file}: {e}")

        # Load package plugins (directories with __init__.py)
        for subdir in plugin_dir.iterdir():
            if subdir.is_dir() and (subdir / "__init__.py").exists():
                try:
                    if self._load_plugin_package(subdir):
                        count += 1
                except (ImportError, SyntaxError, AttributeError, OSError) as e:
                    logger.error(f"Error loading plugin package {subdir}: {e}")
        
        return count
    
    def _load_plugin_file(self, py_file: Path) -> bool:
        """Load a single-file plugin."""
        module_name = f"kirby_cost_plugin_{py_file.stem}"
        
        spec = importlib.util.spec_from_file_location(module_name, py_file)
        if spec is None or spec.loader is None:
            return False
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        return self._process_plugin_module(module, py_file.stem, "file")
    
    def _load_plugin_package(self, package_dir: Path) -> bool:
        """Load a package plugin."""
        module_name = f"kirby_cost_plugin_{package_dir.name}"
        
        init_file = package_dir / "__init__.py"
        spec = importlib.util.spec_from_file_location(
            module_name, init_file,
            submodule_search_locations=[str(package_dir)]
        )
        if spec is None or spec.loader is None:
            return False
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        return self._process_plugin_module(module, package_dir.name, "file")
    
    def _process_plugin_module(self, module, name: str, source: str) -> bool:
        """Process a loaded plugin module."""
        # Get metadata
        metadata = PluginMetadata(
            name=getattr(module, 'PLUGIN_NAME', name),
            version=getattr(module, 'PLUGIN_VERSION', '1.0'),
            author=getattr(module, 'PLUGIN_AUTHOR', ''),
            description=getattr(module, 'PLUGIN_DESCRIPTION', ''),
            source=source,
        )
        
        # Look for power classes
        for attr_name in dir(module):
            if attr_name.startswith('_'):
                continue
            
            attr = getattr(module, attr_name)
            
            # Check if it's a Power subclass
            if isinstance(attr, type):
                if self._is_power_class(attr):
                    xmlid = getattr(attr, 'XMLID', attr_name.upper())
                    self._power_classes[xmlid] = attr
                    metadata.power_classes.append(xmlid)
                    logger.info(f"Registered power class: {xmlid}")
                
                # Check if it's a PowerExtension
                elif issubclass(attr, PowerExtension) and attr is not PowerExtension:
                    self._register_extension(attr)
                    metadata.extensions.extend(attr.APPLIES_TO)
        
        # Look for register() function
        if hasattr(module, 'register'):
            module.register(self)
        
        # Look for custom calculations
        if hasattr(module, 'CUSTOM_CALCULATIONS'):
            for calc_name, calc_func in module.CUSTOM_CALCULATIONS.items():
                self._custom_calculations[calc_name] = calc_func
                metadata.calculations.append(calc_name)
        
        self._loaded_plugins[name] = metadata
        logger.info(f"Loaded plugin: {metadata.name} v{metadata.version}")
        return True
    
    def _is_power_class(self, cls) -> bool:
        """Check if a class is a Power subclass."""
        try:
            from kirby_cost.objects.powers.power import Power
            return issubclass(cls, Power) and cls is not Power
        except ImportError:
            # Check for XMLID attribute as fallback
            return hasattr(cls, 'XMLID')
    
    def _register_extension(self, extension_cls: Type[PowerExtension]):
        """Register a power extension."""
        methods = extension_cls.extension_methods()
        for xmlid in extension_cls.APPLIES_TO:
            xmlid = xmlid.upper()
            if xmlid not in self._extensions:
                self._extensions[xmlid] = {}
            self._extensions[xmlid].update(methods)
            logger.info(f"Registered extension for {xmlid}: {list(methods.keys())}")
    
    def load_plugin_from_code(self, code: str, name: str) -> bool:
        """
        Load a plugin from Python code string.
        
        Useful for database-stored plugins.
        
        Args:
            code: Python source code
            name: Plugin name
            
        Returns:
            True if loaded successfully
        """
        module_name = f"kirby_cost_plugin_db_{name}"
        
        # Create module from code
        module = type(sys)(__name__)
        module.__name__ = module_name
        
        try:
            exec(code, module.__dict__)
            sys.modules[module_name] = module
            return self._process_plugin_module(module, name, "database")
        except (SyntaxError, ImportError, AttributeError, TypeError, NameError) as e:
            logger.error(f"Error loading plugin from code: {e}")
            return False
    
    def register_power_class(self, xmlid: str, power_class: Type['Power']):
        """Manually register a power class."""
        self._power_classes[xmlid.upper()] = power_class
        logger.info(f"Manually registered power class: {xmlid}")
    
    def register_extension_method(self, xmlid: str, method_name: str, 
                                   method: Callable):
        """Manually register an extension method."""
        xmlid = xmlid.upper()
        if xmlid not in self._extensions:
            self._extensions[xmlid] = {}
        self._extensions[xmlid][method_name] = method
    
    def register_calculation(self, name: str, func: Callable):
        """Register a custom calculation function."""
        self._custom_calculations[name] = func
    
    def power_class(self, xmlid: str) -> Optional[Type['Power']]:
        """Get a plugin-provided power class."""
        return self._power_classes.get(xmlid.upper())
    
    def extension_methods(self, xmlid: str) -> Dict[str, Callable]:
        """Get extension methods for a power."""
        return self._extensions.get(xmlid.upper(), {})
    
    def calculation(self, name: str) -> Optional[Callable]:
        """Get a custom calculation function."""
        return self._custom_calculations.get(name)
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins."""
        return [p.to_dict() for p in self._loaded_plugins.values()]
    
    def list_power_classes(self) -> List[str]:
        """List all plugin-provided power XMLIDs."""
        return list(self._power_classes.keys())
    
    def list_extensions(self) -> Dict[str, List[str]]:
        """List all extensions by XMLID."""
        return {xmlid: list(methods.keys()) 
                for xmlid, methods in self._extensions.items()}


# Global plugin loader instance
_plugin_loader: Optional[PluginLoader] = None


def get_plugin_loader() -> PluginLoader:
    """Get the global plugin loader."""
    global _plugin_loader
    if _plugin_loader is None:
        _plugin_loader = PluginLoader()
    return _plugin_loader


def load_plugins(plugin_dir: str = None) -> int:
    """
    Convenience function to load plugins.
    
    Args:
        plugin_dir: Directory to load from (optional)
        
    Returns:
        Number of plugins loaded
    """
    loader = get_plugin_loader()
    
    if plugin_dir:
        loader.add_plugin_directory(plugin_dir)
    
    # Default plugin directories
    default_dirs = [
        Path(__file__).parent.parent / "plugins" / "powers",
        Path.home() / ".kirby_cost" / "plugins",
    ]
    
    for d in default_dirs:
        if d.exists():
            loader.add_plugin_directory(str(d))
    
    count = loader.load_all_plugins()
    
    # Link the loader to the registry
    from .registry import get_registry
    get_registry().plugin_loader(loader)
    
    return count

