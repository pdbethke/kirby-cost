"""
Behavior Engine

Evaluates behavior definitions to calculate power effects,
generate display strings, and validate configurations.
"""

import re
import math
from typing import Dict, Any, Optional, List, Union
from .schema import BehaviorSchema, RoundingMode


class SafeExpressionEvaluator:
    """
    Safely evaluates mathematical expressions without using eval().
    
    Supports:
    - Basic math: +, -, *, /, //, %
    - Comparisons: <, >, <=, >=, ==, !=
    - Functions: min, max, floor, ceil, round, abs, if
    - Variables from context
    """
    
    # Allowed functions
    SAFE_FUNCTIONS = {
        'min': min,
        'max': max,
        'floor': math.floor,
        'ceil': math.ceil,
        'round': round,
        'abs': abs,
        'int': int,
        'float': float,
    }
    
    def __init__(self):
        self._token_pattern = re.compile(
            r'(\d+\.?\d*|'  # Numbers
            r'[a-zA-Z_][a-zA-Z0-9_]*|'  # Identifiers
            r'<=|>=|==|!=|//|'  # Multi-char operators (must be before single-char)
            r'[+\-*/%()<>=!,])'  # Single-char operators
        )
    
    def evaluate(self, expression: str, context: Dict[str, Any]) -> Union[int, float, bool]:
        """
        Evaluate an expression with the given context.
        
        Args:
            expression: Mathematical expression string
            context: Dictionary of variable values
            
        Returns:
            Evaluated result
        """
        if not expression or not expression.strip():
            return 0
            
        try:
            # Tokenize
            tokens = self._tokenize(expression)
            # Parse and evaluate
            result, _ = self._parse_expression(tokens, 0, context)
            return result
        except (ValueError, TypeError, ZeroDivisionError, IndexError, AttributeError) as e:
            # Return 0 on error (safe default)
            print(f"Expression evaluation error: {e} in '{expression}'")
            return 0
    
    def _tokenize(self, expression: str) -> List[str]:
        """Tokenize an expression."""
        tokens = self._token_pattern.findall(expression)
        return [t for t in tokens if t.strip()]
    
    def _parse_expression(self, tokens: List[str], pos: int, 
                          context: Dict[str, Any]) -> tuple:
        """Parse and evaluate an expression."""
        return self._parse_comparison(tokens, pos, context)
    
    def _parse_comparison(self, tokens: List[str], pos: int,
                          context: Dict[str, Any]) -> tuple:
        """Parse comparison operators."""
        left, pos = self._parse_additive(tokens, pos, context)
        
        while pos < len(tokens) and tokens[pos] in ('<', '>', '<=', '>=', '==', '!='):
            op = tokens[pos]
            pos += 1
            right, pos = self._parse_additive(tokens, pos, context)
            
            if op == '<':
                left = left < right
            elif op == '>':
                left = left > right
            elif op == '<=':
                left = left <= right
            elif op == '>=':
                left = left >= right
            elif op == '==':
                left = left == right
            elif op == '!=':
                left = left != right
        
        return left, pos
    
    def _parse_additive(self, tokens: List[str], pos: int,
                        context: Dict[str, Any]) -> tuple:
        """Parse + and - operators."""
        left, pos = self._parse_multiplicative(tokens, pos, context)
        
        while pos < len(tokens) and tokens[pos] in ('+', '-'):
            op = tokens[pos]
            pos += 1
            right, pos = self._parse_multiplicative(tokens, pos, context)
            
            if op == '+':
                left = left + right
            else:
                left = left - right
        
        return left, pos
    
    def _parse_multiplicative(self, tokens: List[str], pos: int,
                              context: Dict[str, Any]) -> tuple:
        """Parse *, /, //, % operators."""
        left, pos = self._parse_unary(tokens, pos, context)
        
        while pos < len(tokens) and tokens[pos] in ('*', '/', '//', '%'):
            op = tokens[pos]
            pos += 1
            right, pos = self._parse_unary(tokens, pos, context)
            
            if op == '*':
                left = left * right
            elif op == '/':
                left = left / right if right != 0 else 0
            elif op == '//':
                left = left // right if right != 0 else 0
            else:  # %
                left = left % right if right != 0 else 0
        
        return left, pos
    
    def _parse_unary(self, tokens: List[str], pos: int,
                     context: Dict[str, Any]) -> tuple:
        """Parse unary operators."""
        if pos < len(tokens) and tokens[pos] == '-':
            pos += 1
            value, pos = self._parse_primary(tokens, pos, context)
            return -value, pos
        
        return self._parse_primary(tokens, pos, context)
    
    def _parse_primary(self, tokens: List[str], pos: int,
                       context: Dict[str, Any]) -> tuple:
        """Parse primary expressions (numbers, variables, functions, parens)."""
        if pos >= len(tokens):
            return 0, pos
        
        token = tokens[pos]
        
        # Number
        if re.match(r'^\d+\.?\d*$', token):
            return float(token) if '.' in token else int(token), pos + 1
        
        # Parentheses
        if token == '(':
            pos += 1
            value, pos = self._parse_expression(tokens, pos, context)
            if pos < len(tokens) and tokens[pos] == ')':
                pos += 1
            return value, pos
        
        # Function call or variable
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', token):
            # Check if it's a function call
            if pos + 1 < len(tokens) and tokens[pos + 1] == '(':
                return self._parse_function_call(tokens, pos, context)
            
            # Variable lookup
            if token in context:
                value = context[token]
                if isinstance(value, bool):
                    return 1 if value else 0, pos + 1
                return value, pos + 1
            
            # Unknown variable - return 0
            return 0, pos + 1
        
        return 0, pos + 1
    
    def _parse_function_call(self, tokens: List[str], pos: int,
                             context: Dict[str, Any]) -> tuple:
        """Parse a function call."""
        func_name = tokens[pos]
        pos += 2  # Skip function name and '('
        
        # Parse arguments
        args = []
        while pos < len(tokens) and tokens[pos] != ')':
            if tokens[pos] == ',':
                pos += 1
                continue
            arg, pos = self._parse_expression(tokens, pos, context)
            args.append(arg)
        
        if pos < len(tokens) and tokens[pos] == ')':
            pos += 1
        
        # Special 'if' function: if(condition, true_val, false_val)
        if func_name == 'if' and len(args) >= 3:
            return args[1] if args[0] else args[2], pos
        
        # Built-in safe functions
        if func_name in self.SAFE_FUNCTIONS:
            try:
                return self.SAFE_FUNCTIONS[func_name](*args), pos
            except (ValueError, TypeError, ZeroDivisionError):
                return 0, pos
        
        # Unknown function
        return 0, pos


class BehaviorEngine:
    """
    Evaluates behavior definitions for powers/skills/modifiers.
    """
    
    def __init__(self, behavior: BehaviorSchema):
        self.behavior = behavior
        self.evaluator = SafeExpressionEvaluator()
    
    def build_context(self, power_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build evaluation context from power instance data.
        
        Args:
            power_data: Dictionary containing power configuration
            
        Returns:
            Context dictionary for expression evaluation
        """
        context = {
            # Basic power attributes
            'levels': power_data.get('levels', 0),
            'base_cost': power_data.get('base_cost', 0),
            'active_cost': power_data.get('active_cost', 0),
            'real_cost': power_data.get('real_cost', 0),
            
            # Calculated values
            'dice': power_data.get('levels', 0),  # Alias for levels
            'points': power_data.get('levels', 0),
            'meters': power_data.get('levels', 0),
            
            # Modifiers
            'total_advantages': power_data.get('total_advantages', 0),
            'total_limitations': power_data.get('total_limitations', 0),
            
            # Character attributes (if available)
            'str': power_data.get('str', 10),
            'dex': power_data.get('dex', 10),
            'con': power_data.get('con', 10),
            'int': power_data.get('int', 10),
            'ego': power_data.get('ego', 10),
            'pre': power_data.get('pre', 10),
            
            # Flags
            'is_6e': power_data.get('is_6e', True),
            'uses_end': power_data.get('uses_end', True),
            
            # Display values
            'name': power_data.get('name', ''),
            'alias': power_data.get('alias', self.behavior.display_template),
            'input': power_data.get('input', ''),
        }
        
        # Add adder-specific values
        for adder in power_data.get('adders', []):
            adder_id = adder.get('xmlid', '').lower()
            context[f'has_{adder_id}'] = True
            context[f'{adder_id}_levels'] = adder.get('levels', 0)
        
        return context
    
    def evaluate_formula(self, formula: str, context: Dict[str, Any]) -> Union[int, float]:
        """Evaluate a formula expression."""
        return self.evaluator.evaluate(formula, context)
    
    def calculate_damage(self, power_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate damage for an attack power.
        
        Returns:
            Dictionary with dice, pips, damage_type, etc.
        """
        if not self.behavior.damage_calculation:
            return {'dice': 0, 'pips': 0, 'damage_type': 'normal'}
        
        dc = self.behavior.damage_calculation
        context = self.build_context(power_data)
        
        # Base dice from formula
        dice = self.evaluate_formula(dc.formula, context)
        pips = 0
        
        # Apply adder bonuses
        for adder in power_data.get('adders', []):
            xmlid = adder.get('xmlid', '')
            if xmlid in dc.adder_bonuses:
                bonus = dc.adder_bonuses[xmlid]
                dice += bonus.dice
                pips += bonus.pips
        
        return {
            'dice': dice,
            'pips': pips,
            'damage_type': dc.damage_type,
            'stun_multiplier': dc.stun_multiplier,
        }
    
    def calculate_defense(self, power_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate defense values.
        
        Returns:
            Dictionary with pd, ed, md, resistant flags, etc.
        """
        if not self.behavior.defense_calculation:
            return {'pd': 0, 'ed': 0, 'md': 0}
        
        dc = self.behavior.defense_calculation
        context = self.build_context(power_data)
        
        result = {
            'pd': 0,
            'ed': 0, 
            'md': 0,
            'pd_resistant': dc.pd_resistant,
            'ed_resistant': dc.ed_resistant,
        }
        
        if dc.pd_formula:
            result['pd'] = self.evaluate_formula(dc.pd_formula, context)
        if dc.ed_formula:
            result['ed'] = self.evaluate_formula(dc.ed_formula, context)
        if dc.md_formula:
            result['md'] = self.evaluate_formula(dc.md_formula, context)
        
        return result
    
    def calculate_endurance(self, power_data: Dict[str, Any]) -> int:
        """Calculate END cost."""
        if not self.behavior.endurance_calculation:
            return 0
        
        ec = self.behavior.endurance_calculation
        if not ec.costs_end:
            return 0
        
        context = self.build_context(power_data)
        raw_end = self.evaluate_formula(ec.formula, context)
        
        # Apply rounding
        if ec.round == RoundingMode.UP:
            end = math.ceil(raw_end)
        elif ec.round == RoundingMode.DOWN:
            end = math.floor(raw_end)
        elif ec.round == RoundingMode.HALF_UP:
            end = math.floor(raw_end + 0.5)
        else:
            end = round(raw_end)
        
        return max(ec.minimum, int(end))
    
    def calculate_custom(self, calculation_name: str, 
                         power_data: Dict[str, Any]) -> Union[int, float]:
        """Evaluate a custom calculation."""
        if calculation_name not in self.behavior.custom_calculations:
            return 0
        
        formula = self.behavior.custom_calculations[calculation_name]
        context = self.build_context(power_data)
        return self.evaluate_formula(formula, context)
    
    def display(self, power_data: Dict[str, Any]) -> str:
        """
        Generate display string for the power.
        
        Args:
            power_data: Power configuration dictionary
            
        Returns:
            Formatted display string
        """
        context = self.build_context(power_data)
        
        # Add calculated values to context
        damage = self.calculate_damage(power_data)
        context['damage_display'] = self._format_damage(damage)
        context['damage_type'] = damage.get('damage_type', 'normal')
        
        defense = self.calculate_defense(power_data)
        context['pd_display'] = f"{defense['pd']}{'r' if defense.get('pd_resistant') else ''} PD"
        context['ed_display'] = f"{defense['ed']}{'r' if defense.get('ed_resistant') else ''} ED"
        
        context['end_cost'] = self.calculate_endurance(power_data)
        
        # Format template
        try:
            return self.behavior.display_template.format(**context)
        except KeyError as e:
            # Missing key - return basic display
            return context.get('alias', self.behavior.xmlid)
    
    def _format_damage(self, damage: Dict[str, Any]) -> str:
        """Format damage dice for display."""
        dice = damage.get('dice', 0)
        pips = damage.get('pips', 0)
        
        # Handle fractional dice
        full_dice = int(dice)
        half_die = dice - full_dice >= 0.5
        
        parts = []
        if full_dice > 0:
            parts.append(f"{full_dice}d6")
        if half_die:
            parts.append("½d6")
        if pips > 0:
            parts.append(f"+{pips}")
        elif pips < 0:
            parts.append(str(pips))
        
        return ''.join(parts) if parts else "0d6"
    
    def validate(self, power_data: Dict[str, Any]) -> List[str]:
        """
        Validate power configuration against rules.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        context = self.build_context(power_data)
        
        for rule in self.behavior.validation_rules:
            if rule.rule_type == 'min_levels':
                if context['levels'] < rule.value:
                    errors.append(rule.message or f"Minimum {rule.value} levels required")
            
            elif rule.rule_type == 'max_levels':
                if context['levels'] > rule.value:
                    errors.append(rule.message or f"Maximum {rule.value} levels allowed")
            
            elif rule.rule_type == 'requires_input':
                if not context.get('input'):
                    errors.append(rule.message or f"Input required: {rule.value}")
            
            elif rule.rule_type == 'requires_adder':
                if not context.get(f'has_{rule.value.lower()}'):
                    errors.append(rule.message or f"Adder required: {rule.value}")
        
        return errors

