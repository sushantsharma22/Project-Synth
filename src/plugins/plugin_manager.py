"""
Plugin Manager - Phase 5: Advanced Features
Discovers, loads, and manages plugins
"""

import os
import sys
import importlib
import logging
from pathlib import Path
from typing import List, Dict, Optional
from src.plugins.base_plugin import BasePlugin, PluginContext, PluginSuggestion

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Manages plugin lifecycle: discovery, loading, execution.
    """
    
    def __init__(self, plugin_dirs: List[str] = None):
        """
        Initialize plugin manager.
        
        Args:
            plugin_dirs: List of directories to search for plugins
        """
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_dirs = plugin_dirs or []
        
        # Add default plugin directories
        project_root = Path(__file__).parent.parent.parent
        self.plugin_dirs.append(str(project_root / "src" / "plugins" / "core"))
        
        logger.info("🔌 Plugin Manager initialized")
    
    def discover_plugins(self) -> List[str]:
        """
        Discover all available plugins in plugin directories.
        
        Returns:
            List of discovered plugin module names
        """
        discovered = []
        
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                logger.warning(f"Plugin directory not found: {plugin_dir}")
                continue
            
            # Add to Python path if not already there
            if plugin_dir not in sys.path:
                sys.path.insert(0, plugin_dir)
            
            # Find all .py files
            for file in os.listdir(plugin_dir):
                if file.endswith('_plugin.py') and not file.startswith('_'):
                    module_name = file[:-3]  # Remove .py
                    discovered.append(module_name)
                    logger.info(f"   Discovered: {module_name}")
        
        return discovered
    
    def load_plugin(self, module_name: str) -> Optional[BasePlugin]:
        """
        Load a single plugin by module name.
        
        Args:
            module_name: Name of the module to load
            
        Returns:
            Loaded plugin instance or None if failed
        """
        try:
            # Import the module
            module = importlib.import_module(module_name)
            
            # Find plugin class (should end with 'Plugin')
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BasePlugin) and 
                    attr != BasePlugin and
                    attr_name.endswith('Plugin')):
                    plugin_class = attr
                    break
            
            if not plugin_class:
                logger.error(f"No plugin class found in {module_name}")
                return None
            
            # Instantiate plugin
            plugin = plugin_class()
            
            # Call on_load hook
            plugin.on_load()
            
            logger.info(f"✅ Loaded plugin: {plugin.metadata.name} v{plugin.metadata.version}")
            return plugin
            
        except Exception as e:
            logger.error(f"❌ Failed to load plugin {module_name}: {e}")
            return None
    
    def load_all_plugins(self):
        """Discover and load all available plugins."""
        logger.info("🔌 Loading plugins...")
        
        # Discover plugins
        plugin_modules = self.discover_plugins()
        logger.info(f"   Found {len(plugin_modules)} plugin(s)")
        
        # Load each plugin
        loaded_count = 0
        for module_name in plugin_modules:
            plugin = self.load_plugin(module_name)
            if plugin:
                self.plugins[plugin.metadata.name] = plugin
                loaded_count += 1
        
        logger.info(f"✅ Loaded {loaded_count}/{len(plugin_modules)} plugins")
    
    def unload_plugin(self, plugin_name: str):
        """
        Unload a plugin.
        
        Args:
            plugin_name: Name of the plugin to unload
        """
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            plugin.on_unload()
            del self.plugins[plugin_name]
            logger.info(f"Unloaded plugin: {plugin_name}")
    
    def unload_all_plugins(self):
        """Unload all plugins."""
        for plugin_name in list(self.plugins.keys()):
            self.unload_plugin(plugin_name)
    
    def get_suggestions(self, context: PluginContext) -> List[PluginSuggestion]:
        """
        Get suggestions from all enabled plugins for the given context.
        
        Args:
            context: The context to analyze
            
        Returns:
            List of all suggestions from all plugins
        """
        all_suggestions = []
        
        for plugin_name, plugin in self.plugins.items():
            if not plugin.enabled:
                continue
            
            try:
                # Check if plugin can handle this context
                if plugin.can_handle(context):
                    logger.debug(f"Plugin {plugin_name} can handle context")
                    
                    # Get suggestions
                    suggestions = plugin.analyze(context)
                    if suggestions:
                        all_suggestions.extend(suggestions)
                        logger.info(f"   {plugin_name}: {len(suggestions)} suggestion(s)")
            
            except Exception as e:
                logger.error(f"Error in plugin {plugin_name}: {e}")
                # Continue with other plugins
        
        # Sort by priority (higher first) then confidence
        all_suggestions.sort(key=lambda s: (s.priority, s.confidence), reverse=True)
        
        return all_suggestions
    
    def notify_accepted(self, suggestion: PluginSuggestion):
        """
        Notify plugin that suggestion was accepted.
        
        Args:
            suggestion: The accepted suggestion
        """
        plugin_name = suggestion.plugin_name
        if plugin_name in self.plugins:
            self.plugins[plugin_name].on_suggestion_accepted(suggestion)
    
    def notify_rejected(self, suggestion: PluginSuggestion):
        """
        Notify plugin that suggestion was rejected.
        
        Args:
            suggestion: The rejected suggestion
        """
        plugin_name = suggestion.plugin_name
        if plugin_name in self.plugins:
            self.plugins[plugin_name].on_suggestion_rejected(suggestion)
    
    def get_plugin_info(self) -> List[Dict]:
        """
        Get information about all loaded plugins.
        
        Returns:
            List of plugin metadata dictionaries
        """
        return [
            {
                'name': plugin.metadata.name,
                'version': plugin.metadata.version,
                'author': plugin.metadata.author,
                'description': plugin.metadata.description,
                'enabled': plugin.enabled
            }
            for plugin in self.plugins.values()
        ]


# Example usage
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "=" * 70)
    print("🧪 TESTING PLUGIN MANAGER")
    print("=" * 70)
    
    # Create plugin manager
    manager = PluginManager()
    
    # Load all plugins
    print("\n1️⃣ Loading plugins...")
    manager.load_all_plugins()
    
    # Show loaded plugins
    print("\n2️⃣ Loaded plugins:")
    for info in manager.get_plugin_info():
        print(f"   • {info['name']} v{info['version']}")
        print(f"     {info['description']}")
        print(f"     Enabled: {info['enabled']}")
    
    # Test with sample context
    print("\n3️⃣ Testing with sample context...")
    context = PluginContext(
        clipboard_text="https://github.com/sushantsharma22/Project-Synth",
        content_type="url"
    )
    
    suggestions = manager.get_suggestions(context)
    print(f"\n   Got {len(suggestions)} suggestion(s):")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n   Suggestion {i}:")
        print(f"   - From: {suggestion.plugin_name}")
        print(f"   - Title: {suggestion.title}")
        print(f"   - Confidence: {suggestion.confidence:.2f}")
        print(f"   - Action: {suggestion.action_type}")
    
    # Cleanup
    print("\n4️⃣ Unloading plugins...")
    manager.unload_all_plugins()
    
    print("\n" + "=" * 70)
    print("✅ Plugin Manager test complete!")
    print("=" * 70 + "\n")
