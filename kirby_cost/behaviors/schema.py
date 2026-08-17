"""
Behavior Definition Schema

Defines the JSON schema for power/skill/modifier behaviors.
This allows behaviors to be stored in the database and modified
without code changes.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class CalculationType(str, Enum):
    """Types of calculations."""
    DICE = "dice"           # Nd6 damage
    POINTS = "points"       # Point values (defense, etc.)
    METERS = "meters"       # Movement
    FORMULA = "formula"     # Custom formula
    LOOKUP = "lookup"       # Table lookup


class RoundingMode(str, Enum):
    """Rounding modes for calculations."""
    UP = "up"
    DOWN = "down"
    HALF_UP = "half_up"
    HALF_DOWN = "half_down"
    NEAREST = "nearest"


@dataclass
class FormulaExpression:
    """
    A safe expression that can be evaluated.
    
    Supports:
    - Variables: levels, active_cost, base_cost, str, dex, etc.
    - Operators: +, -, *, /, //, %
    - Functions: min(), max(), floor(), ceil(), round()
    - Conditionals: if(condition, true_val, false_val)
    """
    expression: str
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'expression': self.expression,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FormulaExpression':
        if isinstance(data, str):
            return cls(expression=data)
        return cls(
            expression=data.get('expression', '0'),
            description=data.get('description')
        )


@dataclass
class AdderBonus:
    """Bonus provided by an adder."""
    adder_xmlid: str
    dice: float = 0
    pips: int = 0
    points: float = 0
    multiplier: float = 1.0
    formula: Optional[str] = None  # Custom formula using adder.levels


@dataclass 
class DamageCalculation:
    """How to calculate damage for attack powers."""
    type: CalculationType = CalculationType.DICE
    formula: str = "levels"  # Base dice formula
    damage_type: str = "normal"  # normal, killing, mental, etc.
    adder_bonuses: Dict[str, AdderBonus] = field(default_factory=dict)
    stun_multiplier: Optional[str] = None  # For killing attacks
    body_formula: Optional[str] = None  # How to count BODY
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type.value,
            'formula': self.formula,
            'damage_type': self.damage_type,
            'adder_bonuses': {k: vars(v) for k, v in self.adder_bonuses.items()},
            'stun_multiplier': self.stun_multiplier,
            'body_formula': self.body_formula
        }


@dataclass
class DefenseCalculation:
    """How to calculate defense values."""
    type: CalculationType = CalculationType.POINTS
    pd_formula: Optional[str] = None
    ed_formula: Optional[str] = None
    md_formula: Optional[str] = None
    pd_resistant: bool = False
    ed_resistant: bool = False
    hardened_levels: int = 0
    impenetrable_levels: int = 0


@dataclass
class EnduranceCalculation:
    """How to calculate END cost."""
    formula: str = "active_cost / 10"
    round: RoundingMode = RoundingMode.UP
    minimum: int = 1
    costs_end: bool = True
    reduced_end_divisor: int = 2  # For Reduced END advantage


@dataclass
class DisplayRule:
    """A rule for generating display text."""
    condition: Optional[str] = None  # Condition to check (None = always)
    format: str = ""  # Format string with {placeholders}
    separator: str = ""  # Separator before this part


@dataclass
class DisplayRules:
    """Rules for generating various display strings."""
    # Main display (column 2 in HD)
    main_display: List[DisplayRule] = field(default_factory=list)
    # Short display for lists
    short_display: Optional[str] = None
    # Full description
    full_display: Optional[str] = None
    # Damage display (e.g., "8d6")
    damage_display: Optional[str] = None


@dataclass
class ValidationRule:
    """A validation rule for the power."""
    rule_type: str  # min_levels, max_levels, requires_input, requires_adder, etc.
    value: Any
    message: Optional[str] = None


@dataclass
class CombatEffect:
    """An effect that occurs in combat."""
    effect_type: str  # damage, healing, adjustment, movement, etc.
    target: str  # STUN, BODY, characteristic, etc.
    formula: str
    conditions: Optional[List[str]] = None


@dataclass
class BehaviorSchema:
    """
    Complete behavior definition for a power/skill/modifier.
    
    This can be serialized to/from JSON and stored in the database.
    """
    xmlid: str
    version: int = 1
    
    # Use Python class instead of this definition?
    use_class_fallback: bool = False
    fallback_reason: Optional[str] = None  # Why fallback is needed
    
    # Display
    display_template: str = "{alias}"
    display_rules: Optional[DisplayRules] = None
    
    # Calculations
    damage_calculation: Optional[DamageCalculation] = None
    defense_calculation: Optional[DefenseCalculation] = None
    endurance_calculation: Optional[EnduranceCalculation] = None
    
    # Custom calculations (key -> formula)
    custom_calculations: Dict[str, str] = field(default_factory=dict)
    
    # Combat effects
    combat_effects: List[CombatEffect] = field(default_factory=list)
    
    # Validation
    validation_rules: List[ValidationRule] = field(default_factory=list)
    
    # Special flags
    is_attack: bool = False
    is_defense: bool = False
    is_movement: bool = False
    is_sense: bool = False
    is_adjustment: bool = False
    is_mental: bool = False
    does_knockback: bool = False
    does_body: bool = True
    
    # Metadata
    description: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'xmlid': self.xmlid,
            'version': self.version,
            'use_class_fallback': self.use_class_fallback,
            'display_template': self.display_template,
            'is_attack': self.is_attack,
            'is_defense': self.is_defense,
            'is_movement': self.is_movement,
            'is_sense': self.is_sense,
            'is_adjustment': self.is_adjustment,
            'is_mental': self.is_mental,
            'does_knockback': self.does_knockback,
            'does_body': self.does_body,
        }
        
        if self.fallback_reason:
            result['fallback_reason'] = self.fallback_reason
        if self.display_rules:
            result['display_rules'] = vars(self.display_rules)
        if self.damage_calculation:
            result['damage_calculation'] = self.damage_calculation.to_dict()
        if self.defense_calculation:
            result['defense_calculation'] = vars(self.defense_calculation)
        if self.endurance_calculation:
            result['endurance_calculation'] = vars(self.endurance_calculation)
        if self.custom_calculations:
            result['custom_calculations'] = self.custom_calculations
        if self.combat_effects:
            result['combat_effects'] = [vars(e) for e in self.combat_effects]
        if self.validation_rules:
            result['validation_rules'] = [vars(r) for r in self.validation_rules]
        if self.description:
            result['description'] = self.description
        if self.notes:
            result['notes'] = self.notes
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BehaviorSchema':
        """Create from dictionary (JSON deserialization)."""
        schema = cls(
            xmlid=data.get('xmlid', ''),
            version=data.get('version', 1),
            use_class_fallback=data.get('use_class_fallback', False),
            fallback_reason=data.get('fallback_reason'),
            display_template=data.get('display_template', '{alias}'),
            is_attack=data.get('is_attack', False),
            is_defense=data.get('is_defense', False),
            is_movement=data.get('is_movement', False),
            is_sense=data.get('is_sense', False),
            is_adjustment=data.get('is_adjustment', False),
            is_mental=data.get('is_mental', False),
            does_knockback=data.get('does_knockback', False),
            does_body=data.get('does_body', True),
            description=data.get('description'),
            notes=data.get('notes'),
        )
        
        # Parse nested structures
        if 'damage_calculation' in data:
            dc = data['damage_calculation']
            schema.damage_calculation = DamageCalculation(
                type=CalculationType(dc.get('type', 'dice')),
                formula=dc.get('formula', 'levels'),
                damage_type=dc.get('damage_type', 'normal'),
                stun_multiplier=dc.get('stun_multiplier'),
                body_formula=dc.get('body_formula'),
            )
            # Parse adder bonuses
            for xmlid, bonus in dc.get('adder_bonuses', {}).items():
                schema.damage_calculation.adder_bonuses[xmlid] = AdderBonus(
                    adder_xmlid=xmlid,
                    dice=bonus.get('dice', 0),
                    pips=bonus.get('pips', 0),
                    points=bonus.get('points', 0),
                    multiplier=bonus.get('multiplier', 1.0),
                    formula=bonus.get('formula'),
                )
        
        if 'endurance_calculation' in data:
            ec = data['endurance_calculation']
            schema.endurance_calculation = EnduranceCalculation(
                formula=ec.get('formula', 'active_cost / 10'),
                round=RoundingMode(ec.get('round', 'up')),
                minimum=ec.get('minimum', 1),
                costs_end=ec.get('costs_end', True),
            )
        
        if 'custom_calculations' in data:
            schema.custom_calculations = data['custom_calculations']
        
        if 'validation_rules' in data:
            schema.validation_rules = [
                ValidationRule(
                    rule_type=r.get('rule_type', ''),
                    value=r.get('value'),
                    message=r.get('message'),
                )
                for r in data['validation_rules']
            ]
        
        if 'combat_effects' in data:
            schema.combat_effects = [
                CombatEffect(
                    effect_type=e.get('effect_type', ''),
                    target=e.get('target', ''),
                    formula=e.get('formula', '0'),
                    conditions=e.get('conditions'),
                )
                for e in data['combat_effects']
            ]
        
        return schema


# Example behavior definitions
EXAMPLE_BEHAVIORS = {
    'ENERGYBLAST': {
        'xmlid': 'ENERGYBLAST',
        'version': 1,
        'display_template': '{name}: {damage_display} {damage_type}',
        'is_attack': True,
        'does_knockback': True,
        'does_body': True,
        'damage_calculation': {
            'type': 'dice',
            'formula': 'levels',
            'damage_type': 'normal',
            'adder_bonuses': {
                'PLUSONEHALFDIE': {'dice': 0.5},
                'PLUSONEPIP': {'pips': 1},
                'MINUSONEPIP': {'pips': -1},
            }
        },
        'endurance_calculation': {
            'formula': 'active_cost / 10',
            'round': 'up',
            'minimum': 1,
        },
        'combat_effects': [
            {
                'effect_type': 'damage',
                'target': 'STUN',
                'formula': 'roll_normal_damage(dice)',
            },
            {
                'effect_type': 'damage',
                'target': 'BODY',
                'formula': 'count_body(dice_results)',
            },
            {
                'effect_type': 'knockback',
                'formula': 'body_dealt - target_kb_resistance',
            }
        ],
        'validation_rules': [
            {'rule_type': 'min_levels', 'value': 1},
        ]
    },
    
    'FORCEFIELD': {
        'xmlid': 'FORCEFIELD',
        'version': 1,
        'display_template': '{name}: {pd_display}/{ed_display}',
        'is_defense': True,
        'defense_calculation': {
            'type': 'points',
            'pd_formula': 'levels',
            'ed_formula': 'levels',
            'pd_resistant': True,
            'ed_resistant': True,
        },
        'endurance_calculation': {
            'formula': 'active_cost / 10',
            'round': 'up',
        },
    },
    
    'FLIGHT': {
        'xmlid': 'FLIGHT',
        'version': 1,
        'display_template': '{name}: {meters}m',
        'is_movement': True,
        'custom_calculations': {
            'meters': 'levels',
            'noncombat_meters': 'meters * noncombat_multiplier',
        },
        'endurance_calculation': {
            'formula': 'active_cost / 10',
            'round': 'up',
        },
    },
    
    # Complex power that needs Python fallback
    'SUMMON': {
        'xmlid': 'SUMMON',
        'version': 1,
        'use_class_fallback': True,
        'fallback_reason': 'Complex summoned creature management and point calculations',
    },
    
    'DUPLICATION': {
        'xmlid': 'DUPLICATION',
        'version': 1,
        'use_class_fallback': True,
        'fallback_reason': 'Complex duplicate tracking and shared damage calculations',
    },
}

