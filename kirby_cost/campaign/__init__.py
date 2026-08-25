"""A campaign's own rules: what this GM changed about the HERO template."""
from kirby_cost.campaign.active import use_campaign_rules
from kirby_cost.campaign.rules import CampaignRules, OVERRIDABLE_FIELDS

__all__ = ["CampaignRules", "OVERRIDABLE_FIELDS", "use_campaign_rules"]
