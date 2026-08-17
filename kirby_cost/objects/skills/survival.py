"""Backward compatibility -- Survival is now AdderBasedSkill."""
from kirby_cost.objects.skills.adder_based_skill import AdderBasedSkill, AdderBasedSkill as Survival

__all__ = ["Survival", "AdderBasedSkill"]
