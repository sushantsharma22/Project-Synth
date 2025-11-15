"""
Math/Calculator Plugin - Phase 5: Advanced Features
Solve equations, unit conversion, financial calculations, statistics
"""

import re
import logging
from typing import List, Optional, Tuple
from pathlib import Path

import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.plugins.base_plugin import (
    BasePlugin, PluginMetadata, PluginContext, PluginSuggestion
)

logger = logging.getLogger(__name__)


class MathPlugin(BasePlugin):
    """
    Intelligent math and calculation assistance.
    
    Features:
    - Basic arithmetic evaluation
    - Unit conversions
    - Financial calculations
    - Statistical operations
    - Equation solving
    - Number formatting
    """
    
    # Unit conversion tables
    CONVERSIONS = {
        'length': {
            'km': 1000, 'm': 1, 'cm': 0.01, 'mm': 0.001,
            'mi': 1609.34, 'yd': 0.9144, 'ft': 0.3048, 'in': 0.0254
        },
        'weight': {
            'kg': 1, 'g': 0.001, 'mg': 0.000001,
            'lb': 0.453592, 'oz': 0.0283495, 'ton': 1000
        },
        'temperature': {
            'celsius': 'C', 'fahrenheit': 'F', 'kelvin': 'K'
        },
        'time': {
            'day': 86400, 'hour': 3600, 'min': 60, 'sec': 1,
            'week': 604800, 'month': 2592000, 'year': 31536000
        }
    }
    
    # Math operation patterns
    MATH_PATTERNS = [
        r'(\d+\.?\d*)\s*([\+\-\*\/\^])\s*(\d+\.?\d*)',  # Basic operations
        r'(\d+\.?\d*)\s*%',  # Percentage
        r'sqrt\((\d+\.?\d*)\)',  # Square root
        r'(\d+\.?\d*)\^(\d+\.?\d*)',  # Power
    ]
    
    # Unit conversion patterns
    CONVERSION_PATTERN = r'(\d+\.?\d*)\s*(km|m|cm|mm|mi|ft|in|kg|g|lb|oz|celsius|fahrenheit|kelvin)\s+(?:to|in|as)\s+(km|m|cm|mm|mi|ft|in|kg|g|lb|oz|celsius|fahrenheit|kelvin)'
    
    # Financial patterns
    MONEY_PATTERN = r'[\$€£¥]?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
    
    def _get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="math_plugin",
            version="1.0.0",
            author="Project Synth",
            description="Intelligent math and calculation assistance",
            dependencies=[]
        )
    
    def can_handle(self, context: PluginContext) -> bool:
        """Check if context contains math or calculation content."""
        if not context.clipboard_text:
            return False
        
        text = context.clipboard_text.lower()
        
        # Check for math operations
        has_math = any(re.search(pattern, text) for pattern in self.MATH_PATTERNS)
        
        # Check for unit conversion
        has_conversion = re.search(self.CONVERSION_PATTERN, text, re.IGNORECASE)
        
        # Check for financial content
        has_money = re.search(self.MONEY_PATTERN, text)
        
        # Check for math keywords
        math_keywords = ['calculate', 'compute', 'solve', 'convert', 'sum', 'average', 'total']
        has_keywords = any(keyword in text for keyword in math_keywords)
        
        # Check for numbers
        numbers = re.findall(r'\d+\.?\d*', text)
        has_multiple_numbers = len(numbers) >= 2
        
        return has_math or has_conversion or (has_money and has_keywords) or (has_multiple_numbers and has_keywords)
    
    def analyze(self, context: PluginContext) -> List[PluginSuggestion]:
        """Analyze and provide math suggestions."""
        suggestions = []
        text = context.clipboard_text
        
        if not text:
            return suggestions
        
        # Check for unit conversion
        conversion = self._detect_conversion(text)
        if conversion:
            suggestions.append(self._suggest_conversion(conversion))
        
        # Check for basic math
        math_expr = self._detect_math_expression(text)
        if math_expr:
            suggestions.append(self._suggest_calculation(math_expr))
        
        # Check for statistics
        numbers = self._extract_numbers(text)
        if len(numbers) >= 3:
            suggestions.append(self._suggest_statistics(numbers))
        
        # Check for financial calculations
        if self._has_financial_context(text):
            suggestions.append(self._suggest_financial_calculator())
        
        # Check for percentage calculations
        percentage = self._detect_percentage(text)
        if percentage:
            suggestions.append(self._suggest_percentage_calc(percentage))
        
        return suggestions
    
    def _detect_conversion(self, text: str) -> Optional[Tuple[float, str, str]]:
        """Detect unit conversion request."""
        match = re.search(self.CONVERSION_PATTERN, text, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            from_unit = match.group(2).lower()
            to_unit = match.group(3).lower()
            return (value, from_unit, to_unit)
        return None
    
    def _detect_math_expression(self, text: str) -> Optional[str]:
        """Detect math expression."""
        # Simple expression: number operator number
        match = re.search(r'(\d+\.?\d*)\s*([\+\-\*\/])\s*(\d+\.?\d*)', text)
        if match:
            return f"{match.group(1)} {match.group(2)} {match.group(3)}"
        return None
    
    def _extract_numbers(self, text: str) -> List[float]:
        """Extract all numbers from text."""
        numbers = []
        # Find all numbers (including decimals)
        matches = re.findall(r'\d+\.?\d*', text)
        for match in matches:
            try:
                numbers.append(float(match))
            except ValueError:
                continue
        return numbers
    
    def _has_financial_context(self, text: str) -> bool:
        """Check if text has financial context."""
        financial_keywords = ['interest', 'loan', 'mortgage', 'investment', 'profit', 'loss', 'tax', 'discount']
        return any(keyword in text.lower() for keyword in financial_keywords)
    
    def _detect_percentage(self, text: str) -> Optional[Tuple[float, float]]:
        """Detect percentage calculation."""
        # Pattern: X% of Y
        match = re.search(r'(\d+\.?\d*)\s*%\s*of\s*(\d+\.?\d*)', text)
        if match:
            percentage = float(match.group(1))
            value = float(match.group(2))
            return (percentage, value)
        return None
    
    def _convert_units(self, value: float, from_unit: str, to_unit: str) -> Optional[float]:
        """Convert between units."""
        # Find the category
        for category, units in self.CONVERSIONS.items():
            if from_unit in units and to_unit in units:
                if category == 'temperature':
                    return self._convert_temperature(value, from_unit, to_unit)
                else:
                    # Convert to base unit, then to target unit
                    base_value = value * units[from_unit]
                    return base_value / units[to_unit]
        return None
    
    def _convert_temperature(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert temperature units."""
        # Convert to Celsius first
        if from_unit == 'fahrenheit':
            celsius = (value - 32) * 5/9
        elif from_unit == 'kelvin':
            celsius = value - 273.15
        else:
            celsius = value
        
        # Convert from Celsius to target
        if to_unit == 'fahrenheit':
            return celsius * 9/5 + 32
        elif to_unit == 'kelvin':
            return celsius + 273.15
        else:
            return celsius
    
    def _suggest_conversion(self, conversion: Tuple[float, str, str]) -> PluginSuggestion:
        """Suggest unit conversion."""
        value, from_unit, to_unit = conversion
        result = self._convert_units(value, from_unit, to_unit)
        
        if result is not None:
            result_text = f"{value} {from_unit} = {result:.2f} {to_unit}"
        else:
            result_text = f"Conversion: {value} {from_unit} → {to_unit}"
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='copy_to_clipboard',
            title='🔢 Unit Conversion',
            description=result_text,
            confidence=0.92,
            action_params={'text': result_text},
            priority=10
        )
    
    def _suggest_calculation(self, expression: str) -> PluginSuggestion:
        """Suggest calculation result."""
        try:
            # Safe eval for basic math
            result = eval(expression.replace('^', '**'))
            result_text = f"{expression} = {result}"
        except:
            result_text = f"Calculate: {expression}"
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='copy_to_clipboard',
            title='🧮 Calculate',
            description=result_text,
            confidence=0.95,
            action_params={'text': str(result) if 'result' in locals() else expression},
            priority=9
        )
    
    def _suggest_statistics(self, numbers: List[float]) -> PluginSuggestion:
        """Suggest statistical analysis."""
        count = len(numbers)
        total = sum(numbers)
        average = total / count
        minimum = min(numbers)
        maximum = max(numbers)
        
        stats = f"""Statistics for {count} numbers:
Sum: {total:.2f}
Average: {average:.2f}
Min: {minimum:.2f}
Max: {maximum:.2f}
Range: {maximum - minimum:.2f}"""
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='copy_to_clipboard',
            title='📊 Statistics',
            description=f'Analyze {count} numbers',
            confidence=0.88,
            action_params={'text': stats},
            priority=8
        )
    
    def _suggest_financial_calculator(self) -> PluginSuggestion:
        """Suggest financial calculator."""
        calculator_url = 'https://www.calculator.net/finance-calculator.html'
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='open_url',
            title='💰 Financial Calculator',
            description='Open financial calculator',
            confidence=0.80,
            action_params={'url': calculator_url},
            priority=7
        )
    
    def _suggest_percentage_calc(self, percentage: Tuple[float, float]) -> PluginSuggestion:
        """Suggest percentage calculation."""
        percent, value = percentage
        result = (percent / 100) * value
        result_text = f"{percent}% of {value} = {result:.2f}"
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='copy_to_clipboard',
            title='📈 Percentage',
            description=result_text,
            confidence=0.93,
            action_params={'text': result_text},
            priority=9
        )


if __name__ == "__main__":
    print("\n🧪 Testing Math Plugin...\n")
    
    plugin = MathPlugin()
    print(f"📦 {plugin.metadata.name} v{plugin.metadata.version}")
    
    # Test 1: Unit conversion
    print("\n1️⃣ Test: Unit Conversion")
    context = PluginContext(clipboard_text="Convert 100 km to miles")
    suggestions = plugin.analyze(context)
    print(f"   Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"   - {s.title}: {s.description}")
    
    # Test 2: Basic math
    print("\n2️⃣ Test: Basic Math")
    context = PluginContext(clipboard_text="Calculate 156 * 24")
    suggestions = plugin.analyze(context)
    print(f"   Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"   - {s.title}: {s.description}")
    
    # Test 3: Statistics
    print("\n3️⃣ Test: Statistics")
    context = PluginContext(clipboard_text="Find average of 45, 67, 89, 34, 56, 78")
    suggestions = plugin.analyze(context)
    print(f"   Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"   - {s.title}: {s.description}")
    
    # Test 4: Percentage
    print("\n4️⃣ Test: Percentage")
    context = PluginContext(clipboard_text="What is 15% of 250?")
    suggestions = plugin.analyze(context)
    print(f"   Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"   - {s.title}: {s.description}")
    
    print("\n✅ Math Plugin test complete!\n")
