"""Eager imports to populate the GenericObject._registry.

Import this module once before using the registry (e.g., from the loader).
Every module that declares a class with ``xmlid="..."`` is imported here so
that ``__init_subclass__`` fires and registers the class.
"""
# fmt: off
# ── Powers ──────────────────────────────────────────────────────────
from kirby_cost.objects.powers import (  # noqa: F401
    absorption, active_sonar, adjacent, adjacent_fixed, aid, analyze_sense,
    armor, automaton, change_environment, clairsentience, clinging,
    compound_power, concealed, custom_power, damage_negation, damage_reduction,
    damage_resistance, darkness, density_increase, desolidification, detect,
    differing_modifier, dimensional_all, dimensional_group, dimensional_single,
    discriminatory_sense, dispel, does_not_bleed, drain, duplication,
    ego_attack, endurance_reserve, endurance_reserve_recovery,
    energy_blast, enhanced_perception, entangle, extra_dimensional_movement,
    extra_limbs, find_weakness, fixed_location, flash, flash_defense,
    floating_location, flight, force_field, force_wall, ftl_travel, gliding,
    growth, hand_to_hand_attack, healing, high_range_radio_perception,
    images, infrared_perception, invisibility, kb_resistance,
    killing_attack_hth, killing_attack_ranged, lack_of_weakness,
    life_support, luck, make_a_sense, mental_awareness, mental_defense,
    mental_illusions, microscopic, mind_control, mind_link, mind_scan,
    missile_deflection, multiform, naked_modifier,
    negative_combat_skill_levels, negative_penalty_skill_levels,
    negative_skill_levels, nightvision, no_hit_locations,
    nray_perception, partially_penetrative, penetrative, possession,
    power_defense, presence_defense, radar, radio_perceive_transmit, radio_perception,
    range, rapid, reflection, regeneration, shapeshift, shrinking,
    spatial_awareness, stretching, succor, summon, suppress, swinging,
    targeting_sense, telekinesis, telepathy, teleportation, telescopic,
    tracking_sense, transfer, transmit, transform, tunneling,
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
    activationroll, affectsdesolid, affectsphysicalworld, alwayson,
    alternatecombatvalue, areaeffect, armorpiercing, autofire, avad, avld,
    basedonecv, beam, canbemissiledeflected, cannotescapewithteleport,
    charges, concentration, continuous, costsend, costsendtomaintain,
    costsendonlytoactivate, cumulative, damage_shield, damageovertime,
    delayedeffect, delayedend, delayedreturnrate, difficulttodispel,
    does_body, does_kb, doublekb, doubleendurancecost, dropped,
    endreserveorend, explosion, extratime, feedback, focus, gestures,
    halfrangemodifier, hardened, holeinthemiddle, incantations,
    increasedend, increasedmaxrange, indirect, inherent, instant,
    invisible, limitedarcoffire, limitedrange, lingering, linked,
    lineofsight, megascale, mobile, nnd, no_kb, norange, norangemodifier,
    normalrange, nonpersistent, notthroughmindlink,
    doesnotprovidementalawareness, onlyonappropriateterrain,
    onlytoactivate, onlytostarting, others_only, partialcoverage,
    penetrating, persistent, personalimmunity, physicalmanifestation,
    ranged, rangebasedonstr, realweapon, reducedbyrange, reducedend,
    requiredhands, requiresskillroll, restrainable, self_only,
    semiarmorpiercing, sideeffects, sticky, subjecttorangemodifier,
    timelimit, transdimensional, transparent, trigger, turnmode,
    uncontrolled, usableonothers, variableadvantage, variableeffect,
    variablelimitations, variabletarget, visible,
)

# ── Martial Arts ────────────────────────────────────────────────────
from kirby_cost.objects.martial_arts import (  # noqa: F401
    extra_damage_classes, maneuver, ranged_damage_classes, weapon_element,
)

# ── Plugins ─────────────────────────────────────────────────────────
from kirby_cost.plugins.powers import coughing  # noqa: F401
# fmt: on
