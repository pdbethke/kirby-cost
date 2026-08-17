"""Configuration for the de-Java-ify CST transformation script."""

# Methods to never touch (keep as-is)
EXCLUDE_METHODS: set[str] = {
    "get_save_xml",
    "get_general_save_xml",
    "get_instance",
}

# Attributes in GenericObject.__init__ that conflict with the property name
# after removing the get_ prefix.  Phase 2 renames self.X → self._X before
# converting get_X → @property X.
#
# Do NOT rename these in TemplateData / AdderTemplate / OptionTemplate
# dataclasses (kirby_cost/template/dataclasses.py).
ATTRIBUTE_RENAMES: dict[str, str] = {
    "base_cost": "_base_cost",
    "levels": "_levels",
    "level_cost": "_level_cost",
    "level_value": "_level_value",
    "minimum_level": "_minimum_level",
    "minimum_cost": "_minimum_cost",
    "max_cost": "_max_cost",
    "max_level": "_max_level",
    "assigned_modifiers": "_assigned_modifiers",
    "assigned_adders": "_assigned_adders",
    "available_adders": "_available_adders",
    "available_modifiers": "_available_modifiers",
    "options": "_options",
    "selected_option": "_selected_option",
    "types": "_types",
    "display": "_display",
    "name": "_name",
    "alias": "_alias",
    "defense": "_defense",
    "duration": "_duration",
    "parent": "_parent",
    "quantity": "_quantity",
    "sources": "_sources",
    "use_end_reserve": "_use_end_reserve",
    "weight": "_weight",
}

# Getter → setter pairs that should become @property + @X.setter
# (applies in the phase where the getter is converted)
SETTER_PAIRS: dict[str, str] = {
    "get_base_cost": "set_base_cost",
    "get_selected_option": "set_selected_option",
    "get_parent": "set_parent",
}
