"""
Base Plugin Interface - Phase 5: Advanced Features
All plugins must inherit from this base class
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class PluginMetadata:
    """Metadata about a plugin."""
    name: str
    version: str
    author: str
    description: str
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class PluginContext:
    """Context data passed to plugins for analysis."""
    clipboard_text: Optional[str] = None
    screen_data: Optional[Dict] = None
    file_path: Optional[str] = None
    content_type: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class PluginSuggestion:
    """A suggestion returned by a plugin."""
    plugin_name: str
    action_type: str
    title: str
    description: str
    confidence: float  # 0.0 to 1.0
    action_params: Dict[str, Any]
    priority: int = 0  # Higher = more important
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'plugin_name': self.plugin_name,
            'action_type': self.action_type,
            'title': self.title,
            'description': self.description,
            'confidence': self.confidence,
            'action_params': self.action_params,
            'priority': self.priority
        }


class BasePlugin(ABC):
    """
    Base class for all Project Synth plugins.
    
    Plugins analyze context and provide intelligent suggestions.
    """
    
    def __init__(self):
        self.enabled = True
        self.config = {}
        self._metadata = self._get_metadata()
    
    @abstractmethod
    def _get_metadata(self) -> PluginMetadata:
        """Return plugin metadata. Must be implemented by subclass."""
        pass
    
    @abstractmethod
    def can_handle(self, context: PluginContext) -> bool:
        """
        Check if this plugin can handle the given context.
        
        Args:
            context: The context to analyze
            
        Returns:
            True if plugin can provide suggestions for this context
        """
        pass
    
    @abstractmethod
    def analyze(self, context: PluginContext) -> List[PluginSuggestion]:
        """
        Analyze context and return suggestions.
        
        Args:
            context: The context to analyze
            
        Returns:
            List of suggestions (can be empty)
        """
        pass
    
    def configure(self, config: Dict[str, Any]):
        """
        Configure the plugin with settings.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
    
    def enable(self):
        """Enable this plugin."""
        self.enabled = True
    
    def disable(self):
        """Disable this plugin."""
        self.enabled = False
    
    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return self._metadata
    
    def on_load(self):
        """Called when plugin is loaded. Override to add initialization logic."""
        pass
    
    def on_unload(self):
        """Called when plugin is unloaded. Override to add cleanup logic."""
        pass
    
    def on_suggestion_accepted(self, suggestion: PluginSuggestion):
        """
        Called when user accepts a suggestion from this plugin.
        Override to learn from user behavior.
        
        Args:
            suggestion: The accepted suggestion
        """
        pass
    
    def on_suggestion_rejected(self, suggestion: PluginSuggestion):
        """
        Called when user rejects a suggestion from this plugin.
        Override to learn from user behavior.
        
        Args:
            suggestion: The rejected suggestion
        """
        pass


# Example plugin implementation
class ExamplePlugin(BasePlugin):
    """Example plugin to demonstrate the plugin API."""
    
    def _get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="example_plugin",
            version="1.0.0",
            author="Project Synth",
            description="Example plugin demonstrating the plugin API",
            dependencies=[]
        )
    
    def can_handle(self, context: PluginContext) -> bool:
        """This example plugin handles all text content."""
        return context.clipboard_text is not None
    
    def analyze(self, context: PluginContext) -> List[PluginSuggestion]:
        """
        Example analysis: suggest showing a notification.
        """
        if not context.clipboard_text:
            return []
        
        # Create a simple suggestion
        suggestion = PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='show_notification',
            title='Example Suggestion',
            description=f'You copied {len(context.clipboard_text)} characters',
            confidence=0.5,
            action_params={
                'title': 'Example Plugin',
                'message': f'Clipboard has {len(context.clipboard_text)} chars'
            },
            priority=1
        )
        
        return [suggestion]


if __name__ == "__main__":
    # Test the example plugin
    print("🧪 Testing BasePlugin and ExamplePlugin...")
    
    # Create plugin instance
    plugin = ExamplePlugin()
    
    print(f"\n📦 Plugin Metadata:")
    print(f"   Name: {plugin.metadata.name}")
    print(f"   Version: {plugin.metadata.version}")
    print(f"   Author: {plugin.metadata.author}")
    print(f"   Description: {plugin.metadata.description}")
    
    # Create test context
    context = PluginContext(
        clipboard_text="Hello, Project Synth!",
        content_type="text"
    )
    
    # Check if plugin can handle
    can_handle = plugin.can_handle(context)
    print(f"\n✅ Can handle context: {can_handle}")
    
    # Get suggestions
    suggestions = plugin.analyze(context)
    print(f"\n💡 Suggestions: {len(suggestions)}")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n   Suggestion {i}:")
        print(f"   - Title: {suggestion.title}")
        print(f"   - Description: {suggestion.description}")
        print(f"   - Confidence: {suggestion.confidence}")
        print(f"   - Action: {suggestion.action_type}")
    
    print("\n✅ Plugin system test complete!")
