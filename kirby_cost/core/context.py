"""
EngineContext singleton class.

Provides access to active hero, template, and preferences.
Converted from Java HeroDesigner.getInstance() pattern.
"""

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero
    from kirby_cost.core.preferences import Preferences
    from kirby_cost.core.template import Template
    from kirby_cost.campaign.rules import CampaignRules


class EngineContext:
    """
    Singleton class providing access to Hero Designer state.
    
    This replaces the Java HeroDesigner.getInstance() pattern.
    """
    
    _instance: Optional['EngineContext'] = None
    _active_hero: Optional['Hero'] = None
    _active_template: Optional['Template'] = None
    _preferences: Optional['Preferences'] = None
    _campaign_rules: Optional['CampaignRules'] = None
    
    def __init__(self):
        """Initialize EngineContext instance."""
        from kirby_cost.core.preferences import Preferences
        self._preferences = Preferences()
    
    @classmethod
    def get_instance(cls) -> 'EngineContext':
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def active_hero(cls) -> Optional['Hero']:
        """Get the currently active hero."""
        instance = cls.get_instance()
        return instance._active_hero

    @classmethod
    def set_active_hero(cls, hero: Optional['Hero']) -> None:
        """Set the currently active hero."""
        instance = cls.get_instance()
        instance._active_hero = hero

    @classmethod
    def active_template(cls) -> Optional['Template']:
        """Get the currently active template."""
        instance = cls.get_instance()
        return instance._active_template

    @classmethod
    def set_active_template(cls, template: Optional['Template']) -> None:
        """Set the currently active template."""
        instance = cls.get_instance()
        instance._active_template = template

    @classmethod
    def campaign_rules(cls) -> Optional['CampaignRules']:
        """The active campaign's rule overrides, or None.

        DELIBERATELY separate from `active_template`. That slot has EIGHT
        readers whose branches were never finished -- they only ever ran their
        None side -- so populating it would switch eight stubs on at once
        (counted 2026-08-25: continuous, nonpersistent, norangemodifier,
        persistent, disadvantage, combat_sense, simulate_death,
        universal_translator; base.py:1814 mentions the slot in prose and does
        not read it). See the campaign-rule-overrides spec, section 7.
        """
        return cls.get_instance()._campaign_rules

    @classmethod
    def set_campaign_rules(cls, rules: Optional['CampaignRules']) -> None:
        """Set the active campaign's rule overrides. Prefer the
        `kirby_cost.campaign.use_campaign_rules` context manager, which restores
        the previous value."""
        cls.get_instance()._campaign_rules = rules

    @classmethod
    def prefs(cls) -> 'Preferences':
        """Get preferences."""
        instance = cls.get_instance()
        if instance._preferences is None:
            from kirby_cost.core.preferences import Preferences
            instance._preferences = Preferences()
        return instance._preferences
    
    @property
    def preferences(self) -> 'Preferences':
        """Get preferences (instance method)."""
        if self._preferences is None:
            from kirby_cost.core.preferences import Preferences
            self._preferences = Preferences()
        return self._preferences



