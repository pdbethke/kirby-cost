"""
Preferences system for kirby-cost.

Converted from Java preferences system.
Provides settings for display and behavior.
"""

from typing import List, Optional


class Preferences:
    """
    Preferences/settings for kirby-cost.
    
    Provides configuration for:
    - Display options (abbreviations, WG mode)
    - Source filtering
    - UI behavior
    """
    
    def __init__(self):
        """Initialize preferences with defaults."""
        self._use_abbreviations: bool = True
        #: HD's 6E default is ON (AppPrefs.useWG() returns true), and the
        #: oracle runs with it. It suppresses the 5E "(vs. ED)" defence note
        #: and the "(uses Personal END)" tail, and selects wg abbreviations
        #: in getAlias(). This port defaulted it OFF, so every attack power
        #: printed a defence HD has not shown since 5th edition.
        self._use_wg: bool = True
        self._display_active_points: bool = True
        self._sources: List[str] = []
        self._native_literacy_free: bool = False
        self._literacy_free: bool = False
    
    @property
    def use_abbreviations(self) -> bool:
        """Check if abbreviations should be used."""
        return self._use_abbreviations

    @use_abbreviations.setter
    def use_abbreviations(self, value: bool) -> None:
        """Set whether to use abbreviations."""
        self._use_abbreviations = value

    @property
    def use_wg(self) -> bool:
        """Check if WG (Writers Guide) mode is enabled."""
        return self._use_wg

    @use_wg.setter
    def use_wg(self, value: bool) -> None:
        """Set WG mode."""
        self._use_wg = value

    @property
    def display_active_points(self) -> bool:
        """Check if active points should be displayed."""
        return self._display_active_points

    @display_active_points.setter
    def display_active_points(self, value: bool) -> None:
        """Set whether to display active points."""
        self._display_active_points = value

    @property
    def sources(self) -> List[str]:
        """Get list of enabled sources."""
        return list(self._sources)

    @sources.setter
    def sources(self, sources: List[str]) -> None:
        self._sources = list(sources) if sources else []
    
    @property
    def native_literacy_free(self) -> bool:
        """Check if native literacy is free."""
        return self._native_literacy_free
    
    @native_literacy_free.setter
    def native_literacy_free(self, value: bool) -> None:
        """Set whether native literacy is free."""
        self._native_literacy_free = value
    
    @property
    def literacy_free(self) -> bool:
        """Check if literacy is free."""
        return self._literacy_free
    
    @literacy_free.setter
    def literacy_free(self, value: bool) -> None:
        """Set whether literacy is free."""
        self._literacy_free = value



