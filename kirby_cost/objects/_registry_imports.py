"""Eager imports to populate the GenericObject._registry.

Import this module once before using the registry (e.g., from the loader).
Every module that declares a class with ``xmlid="..."`` is imported here so
that ``__init_subclass__`` fires and registers the class.
"""
# fmt: off
# ── Powers ──────────────────────────────────────────────────────────
from kirby_cost.objects.powers import (  # noqa: F401
    absorption, active_sonar, adjacent, adjacent_fixed, aid, analyze_sense,
    automaton, change_environment, clairsentience, clinging,
    compound_power, concealed, custom_power, damage_negation, damage_reduction,
    darkness, density_increase, desolidification, detect,
    differing_modifier, dimensional_all, dimensional_group, dimensional_single,
    discriminatory_sense, dispel, does_not_bleed, drain, duplication,
    ego_attack, endurance_reserve, endurance_reserve_recovery,
    energy_blast, enhanced_perception, entangle, extra_dimensional_movement,
    extra_limbs, fixed_location, flash, flash_defense,
    floating_location, flight, force_field, force_wall, ftl_travel, gliding,
    growth, hand_to_hand_attack, healing, high_range_radio_perception,
    images, infrared_perception, invisibility, kb_resistance,
    killing_attack_hth, killing_attack_ranged, life_support, luck, make_a_sense, mental_awareness, mental_defense,
    mental_illusions, microscopic, mind_control, mind_link, mind_scan,
    missile_deflection, multiform, naked_modifier,
    nightvision, no_hit_locations,
    partially_penetrative, penetrative, possession,
    power_defense, presence_defense, radar, radio_perceive_transmit, radio_perception,
    range, rapid, reflection, regeneration, shapeshift, shrinking,
    spatial_awareness, stretching, summon, swinging,
    targeting_sense, telekinesis, telepathy, teleportation, telescopic,
    tracking_sense, transmit, transform, tunneling,
    ultrasonic_perception, ultraviolet_perception,
)

# ── Skills ──────────────────────────────────────────────────────────
from kirby_cost.objects.skills import (  # noqa: F401
    accumulator_skill, adder_based_skill, autofire_skills, combat_levels,
    cramming, custom_skill, defense_maneuver, enhancer, knowledge_skill,
    language,
    mental_combat_levels, n_counter_skill, penalty_skill_levels,
    professional_skill, rapid_attack_hth, rapid_attack_ranged,
    skill_levels, transport_familiarity, two_weapon_fighting_hth,
    two_weapon_fighting_ranged, weapon_familiarity,
)

# ── Perks ───────────────────────────────────────────────────────────
from kirby_cost.objects.perks import (  # noqa: F401
    access, contact, custom_perk, favor, follower, fringe_benefit, money,
    reputation, resource_pool, vehicle,
)

# ── Talents ─────────────────────────────────────────────────────────
from kirby_cost.objects.talents import (  # noqa: F401
    bump_of_direction, combat_luck, combat_sense, custom_talent, danger_sense,
    environmental_movement, lightning_reflexes_all,
    lightning_reflexes_single, mage_sight, resistance, simulate_death,
    speed_reading, striking_appearance, universal_translator,
)

# ── Characteristics ─────────────────────────────────────────────────
from kirby_cost.objects.characteristics import (  # noqa: F401
    base_size, body, constitution, custom1, custom2, custom3, custom4,
    custom5, custom6, custom7, custom8, custom9, custom10, dcv, def_char,
    dexterity, dmcv, ego, endurance, energy_defense, intelligence,
    leaping, ocv, omcv, physical_defense, presence, recovery, running,
    size, speed, strength, stun, swimming,
)

# ── Modifiers ───────────────────────────────────────────────────────
from kirby_cost.objects.modifiers import (  # noqa: F401
    affectsdesolid, affectsphysicalworld, alwayson,
    alternatecombatvalue, areaeffect, armorpiercing, autofire, avad, beam, canbemissiledeflected, cannotescapewithteleport,
    charges, concentration, continuous, costsend, costsendtomaintain,
    costsendonlytoactivate, cumulative, damageovertime,
    delayedeffect, delayedreturnrate, difficulttodispel,
    does_body, does_kb, doublekb, explosion, extratime, feedback, focus, gestures,
    halfrangemodifier, hardened, holeinthemiddle, incantations,
    increasedend, increasedmaxrange, indirect, inherent, instant,
    invisible, limitedarcoffire, limitedrange, linked,
    lineofsight, megascale, mobile, nnd, no_kb, norange, norangemodifier,
    normalrange, nonpersistent, notthroughmindlink,
    onlyonappropriateterrain,
    onlytoactivate, onlytostarting, partialcoverage,
    penetrating, persistent, personalimmunity, physicalmanifestation,
    ranged, rangebasedonstr, reducedbyrange, reducedend,
    requiresskillroll, restrainable, self_only,
    sideeffects, sticky, subjecttorangemodifier,
    timelimit, transdimensional, trigger, turnmode,
    uncontrolled, usableonothers, variableadvantage, variableeffect,
    variablelimitations, visible,
)

# ── Martial Arts ────────────────────────────────────────────────────
from kirby_cost.objects.martial_arts import (  # noqa: F401
    extra_damage_classes, maneuver, ranged_damage_classes, weapon_element,
)

# fmt: on
