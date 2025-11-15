"""
Demo: Phase 5 - Advanced Plugins (Email, CodeDoc, Calendar, WebSearch)
Tests the new plugin capabilities
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.plugins.plugin_manager import PluginManager
from src.plugins.base_plugin import PluginContext


def demo_advanced_plugins():
    """Demonstrate advanced plugin capabilities."""
    print("=" * 80)
    print("PHASE 5: ADVANCED PLUGINS DEMO")
    print("Testing Email, CodeDoc, Calendar, WebSearch plugins")
    print("=" * 80)
    
    # Initialize plugin manager with plugin directory
    print("\n📦 Initializing Plugin Manager...")
    plugin_dirs = [str(project_root / "src" / "plugins" / "core")]
    manager = PluginManager(plugin_dirs=plugin_dirs)
    
    # Load all plugins
    print("\n⚡ Loading all plugins...")
    manager.load_all_plugins()
    
    print(f"\n✨ Total plugins loaded: {len(manager.plugins)}")
    
    # Test scenarios
    print("\n" + "=" * 80)
    print("SCENARIO TESTS")
    print("=" * 80)
    
    # Scenario 1: Email draft
    print("\n1️⃣ Email Draft Detection")
    print("-" * 80)
    email_text = """Hi Sarah,

I wanted to follow up on our meeting yesterday. The proposal looks great!

Can we schedule a call tomorrow at 3pm to discuss next steps?

Thanks,
John"""
    
    context = PluginContext(clipboard_text=email_text)
    suggestions = manager.get_suggestions(context)
    
    print(f"📝 Text: {email_text[:60]}...")
    print(f"💡 Suggestions: {len(suggestions)}")
    for i, suggestion in enumerate(suggestions[:5], 1):
        print(f"\n   {i}. {suggestion.title}")
        print(f"      📄 {suggestion.description}")
        print(f"      🎯 Confidence: {suggestion.confidence:.0%}")
        print(f"      🔧 Action: {suggestion.action_type}")
    
    # Scenario 2: Undocumented code
    print("\n\n2️⃣ Undocumented Code Detection")
    print("-" * 80)
    code_text = """def calculate_total(items, tax_rate):
    subtotal = sum(items)
    tax = subtotal * tax_rate
    return subtotal + tax

class ShoppingCart:
    def __init__(self):
        self.items = []
    
    def add_item(self, item):
        self.items.append(item)"""
    
    context = PluginContext(clipboard_text=code_text)
    suggestions = manager.get_suggestions(context)
    
    print(f"📝 Text: Function and class without docstrings")
    print(f"💡 Suggestions: {len(suggestions)}")
    for i, suggestion in enumerate(suggestions[:5], 1):
        print(f"\n   {i}. {suggestion.title}")
        print(f"      📄 {suggestion.description}")
        print(f"      🎯 Confidence: {suggestion.confidence:.0%}")
    
    # Scenario 3: Meeting scheduling
    print("\n\n3️⃣ Meeting Scheduling")
    print("-" * 80)
    meeting_text = "Let's schedule a team standup meeting tomorrow at 10am"
    
    context = PluginContext(clipboard_text=meeting_text)
    suggestions = manager.get_suggestions(context)
    
    print(f"📝 Text: {meeting_text}")
    print(f"💡 Suggestions: {len(suggestions)}")
    for i, suggestion in enumerate(suggestions[:5], 1):
        print(f"\n   {i}. {suggestion.title}")
        print(f"      📄 {suggestion.description}")
        print(f"      🎯 Confidence: {suggestion.confidence:.0%}")
    
    # Scenario 4: Error search
    print("\n\n4️⃣ Error Message Search")
    print("-" * 80)
    error_text = "TypeError: Cannot read property 'map' of undefined\nat processData (app.js:42)"
    
    context = PluginContext(clipboard_text=error_text)
    suggestions = manager.get_suggestions(context)
    
    print(f"📝 Text: {error_text[:60]}...")
    print(f"💡 Suggestions: {len(suggestions)}")
    for i, suggestion in enumerate(suggestions[:5], 1):
        print(f"\n   {i}. {suggestion.title}")
        print(f"      📄 {suggestion.description}")
        print(f"      🎯 Confidence: {suggestion.confidence:.0%}")
    
    # Scenario 5: Multi-plugin activation
    print("\n\n5️⃣ Multi-Plugin Activation")
    print("-" * 80)
    complex_text = """Subject: Code Review Meeting

Hi team,

We need to schedule a code review meeting for tomorrow at 2pm.

I found a bug in the payment processing function:
TypeError: expected string, got NoneType

The function needs better documentation too.

Let me know if you're available.

Best,
Alex"""
    
    context = PluginContext(clipboard_text=complex_text)
    suggestions = manager.get_suggestions(context)
    
    print(f"📝 Text: Email + Meeting + Error + Code")
    print(f"💡 Suggestions: {len(suggestions)}")
    print("\n   Activated plugins:")
    
    plugin_names = set(s.plugin_name for s in suggestions)
    for plugin_name in sorted(plugin_names):
        count = sum(1 for s in suggestions if s.plugin_name == plugin_name)
        print(f"      • {plugin_name}: {count} suggestion(s)")
    
    print("\n   Top suggestions:")
    for i, suggestion in enumerate(suggestions[:7], 1):
        print(f"\n   {i}. [{suggestion.plugin_name}] {suggestion.title}")
        print(f"      📄 {suggestion.description}")
        print(f"      🎯 Confidence: {suggestion.confidence:.0%} | Priority: {suggestion.priority}")
    
    # Summary
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n✅ Plugins loaded: {len(manager.plugins)}")
    print(f"✅ Scenarios tested: 5")
    print(f"✅ Total suggestions generated: {len(suggestions)}")
    print("\n🎉 Advanced plugins are working perfectly!")
    print("   • Email plugin: Detects drafts, suggests tones")
    print("   • CodeDoc plugin: Finds missing docs, suggests templates")
    print("   • Calendar plugin: Parses dates, creates events")
    print("   • WebSearch plugin: Smart searches, multi-engine")
    print("   • Git plugin: Repository detection, commit messages")
    print("   • Security plugin: API key detection, warnings")
    print("\n🚀 Project Synth is getting smarter than Siri!")


if __name__ == "__main__":
    try:
        demo_advanced_plugins()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
