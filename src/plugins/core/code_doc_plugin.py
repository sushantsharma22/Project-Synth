"""
Code Documentation Plugin - Phase 5: Advanced Features
Generates docstrings, README content, type hints, and code explanations
"""

import re
import logging
from typing import List
from pathlib import Path

import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.plugins.base_plugin import (
    BasePlugin, PluginMetadata, PluginContext, PluginSuggestion
)

logger = logging.getLogger(__name__)


class CodeDocPlugin(BasePlugin):
    """
    Intelligent code documentation assistance.
    
    Features:
    - Generate Python docstrings
    - Create README sections
    - Add type hints
    - Explain code complexity
    - Suggest documentation improvements
    """
    
    # Code patterns
    FUNCTION_PATTERN = r'def\s+(\w+)\s*\([^)]*\):'
    CLASS_PATTERN = r'class\s+(\w+)(?:\([^)]*\))?:'
    IMPORT_PATTERN = r'(?:from\s+[\w.]+\s+)?import\s+[\w\s,]+'
    
    def _get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="code_doc_plugin",
            version="1.0.0",
            author="Project Synth",
            description="Intelligent code documentation generation and improvement",
            dependencies=[]
        )
    
    def can_handle(self, context: PluginContext) -> bool:
        """Check if context contains code."""
        if not context.clipboard_text:
            return False
        
        text = context.clipboard_text
        
        # Check for code indicators
        has_function = re.search(self.FUNCTION_PATTERN, text)
        has_class = re.search(self.CLASS_PATTERN, text)
        has_import = re.search(self.IMPORT_PATTERN, text)
        
        # Check for code-like syntax
        code_chars = ['{', '}', '()', '=>', 'function', 'class', 'def', 'var', 'const', 'let']
        has_code_syntax = any(char in text for char in code_chars)
        
        return bool(has_function or has_class or has_import or has_code_syntax)
    
    def analyze(self, context: PluginContext) -> List[PluginSuggestion]:
        """Analyze code and provide documentation suggestions."""
        suggestions = []
        text = context.clipboard_text
        
        if not text:
            return suggestions
        
        # Check for functions without docstrings
        functions = self._find_undocumented_functions(text)
        if functions:
            suggestions.append(self._suggest_function_docstring(functions[0], text))
        
        # Check for classes without docstrings
        classes = self._find_undocumented_classes(text)
        if classes:
            suggestions.append(self._suggest_class_docstring(classes[0], text))
        
        # Check for missing type hints
        if self._needs_type_hints(text):
            suggestions.append(self._suggest_type_hints())
        
        # Check for complex code
        complexity = self._estimate_complexity(text)
        if complexity > 5:
            suggestions.append(self._suggest_explanation(complexity))
        
        # Check if it's a README-like content
        if self._is_readme_content(text):
            suggestions.append(self._suggest_readme_improvements())
        
        return suggestions
    
    def _find_undocumented_functions(self, text: str) -> List[str]:
        """Find functions without docstrings."""
        lines = text.split('\n')
        undocumented = []
        
        for i, line in enumerate(lines):
            if match := re.search(self.FUNCTION_PATTERN, line):
                func_name = match.group(1)
                
                # Check if next non-empty line is a docstring
                next_line_idx = i + 1
                while next_line_idx < len(lines) and not lines[next_line_idx].strip():
                    next_line_idx += 1
                
                if next_line_idx < len(lines):
                    next_line = lines[next_line_idx].strip()
                    if not (next_line.startswith('"""') or next_line.startswith("'''")):
                        undocumented.append(func_name)
        
        return undocumented
    
    def _find_undocumented_classes(self, text: str) -> List[str]:
        """Find classes without docstrings."""
        lines = text.split('\n')
        undocumented = []
        
        for i, line in enumerate(lines):
            if match := re.search(self.CLASS_PATTERN, line):
                class_name = match.group(1)
                
                # Check if next non-empty line is a docstring
                next_line_idx = i + 1
                while next_line_idx < len(lines) and not lines[next_line_idx].strip():
                    next_line_idx += 1
                
                if next_line_idx < len(lines):
                    next_line = lines[next_line_idx].strip()
                    if not (next_line.startswith('"""') or next_line.startswith("'''")):
                        undocumented.append(class_name)
        
        return undocumented
    
    def _needs_type_hints(self, text: str) -> bool:
        """Check if code needs type hints."""
        # Find function definitions
        functions = re.findall(self.FUNCTION_PATTERN, text)
        
        if not functions:
            return False
        
        # Check if any function has type hints
        has_type_hints = '->' in text or ': ' in text
        
        return not has_type_hints and len(functions) > 0
    
    def _estimate_complexity(self, text: str) -> int:
        """Estimate code complexity (simplified)."""
        complexity = 0
        
        # Count control flow statements
        complexity += text.count('if ')
        complexity += text.count('elif ')
        complexity += text.count('for ')
        complexity += text.count('while ')
        complexity += text.count('try:')
        complexity += text.count('except ')
        
        # Count nested structures
        complexity += text.count('    if ')  # nested if
        complexity += text.count('        if ')  # deeply nested
        
        return complexity
    
    def _is_readme_content(self, text: str) -> bool:
        """Check if text looks like README content."""
        text_lower = text.lower()
        
        readme_indicators = ['# ', '## ', 'installation', 'usage', 'getting started', 'features', 'requirements']
        return sum(1 for indicator in readme_indicators if indicator in text_lower) >= 2
    
    def _suggest_function_docstring(self, func_name: str, code: str) -> PluginSuggestion:
        """Suggest adding a docstring to a function."""
        # Generate basic docstring template
        docstring = f'''"""
    [Brief description of {func_name}]
    
    Args:
        [parameter_name]: [description]
    
    Returns:
        [return value description]
    """'''
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='copy_to_clipboard',
            title=f'📝 Add Docstring to {func_name}()',
            description='Copy docstring template',
            confidence=0.90,
            action_params={'text': docstring},
            priority=9
        )
    
    def _suggest_class_docstring(self, class_name: str, code: str) -> PluginSuggestion:
        """Suggest adding a docstring to a class."""
        docstring = f'''"""
    {class_name} - [Brief description]
    
    Attributes:
        [attribute_name]: [description]
    
    Methods:
        [method_name]: [description]
    """'''
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='copy_to_clipboard',
            title=f'📚 Add Docstring to {class_name}',
            description='Copy class docstring template',
            confidence=0.88,
            action_params={'text': docstring},
            priority=8
        )
    
    def _suggest_type_hints(self) -> PluginSuggestion:
        """Suggest adding type hints."""
        example = """from typing import List, Dict, Optional

def example_function(items: List[str], config: Dict[str, int]) -> Optional[str]:
    \"\"\"Example with type hints.\"\"\"
    pass"""
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='copy_to_clipboard',
            title='🎯 Add Type Hints',
            description='Copy type hints example',
            confidence=0.85,
            action_params={'text': example},
            priority=7
        )
    
    def _suggest_explanation(self, complexity: int) -> PluginSuggestion:
        """Suggest adding explanation for complex code."""
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='show_notification',
            title='🧠 Complex Code Detected',
            description=f'Complexity score: {complexity}. Consider adding comments',
            confidence=0.80,
            action_params={
                'title': 'Code Complexity',
                'message': f'This code has complexity {complexity}. Add comments to explain the logic.'
            },
            priority=6
        )
    
    def _suggest_readme_improvements(self) -> PluginSuggestion:
        """Suggest README improvements."""
        template = """# Project Name

## Description
[Brief description of what this project does]

## Installation
```bash
pip install [package-name]
```

## Usage
```python
# Example usage
import [package-name]
```

## Features
- Feature 1
- Feature 2
- Feature 3

## Contributing
[Contribution guidelines]

## License
[License information]"""
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='copy_to_clipboard',
            title='📄 README Template',
            description='Copy comprehensive README template',
            confidence=0.82,
            action_params={'text': template},
            priority=7
        )


if __name__ == "__main__":
    print("\n🧪 Testing Code Documentation Plugin...\n")
    
    plugin = CodeDocPlugin()
    print(f"📦 {plugin.metadata.name} v{plugin.metadata.version}")
    
    # Test 1: Undocumented function
    print("\n1️⃣ Test: Undocumented Function")
    code = """def calculate_total(items):
    return sum(items)"""
    context = PluginContext(clipboard_text=code)
    suggestions = plugin.analyze(context)
    print(f"   Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"   - {s.title}: {s.description}")
    
    # Test 2: Complex code
    print("\n2️⃣ Test: Complex Code")
    complex_code = """def process_data(data):
    if data:
        for item in data:
            if item > 0:
                try:
                    result = item * 2
                except Exception as e:
                    pass
    return result"""
    context = PluginContext(clipboard_text=complex_code)
    suggestions = plugin.analyze(context)
    print(f"   Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"   - {s.title}: {s.description}")
    
    # Test 3: README content
    print("\n3️⃣ Test: README Content")
    readme = """# My Project
    
## Installation
Run pip install myproject

## Features
- Feature 1"""
    context = PluginContext(clipboard_text=readme)
    suggestions = plugin.analyze(context)
    print(f"   Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"   - {s.title}: {s.description}")
    
    print("\n✅ Code Documentation Plugin test complete!\n")
