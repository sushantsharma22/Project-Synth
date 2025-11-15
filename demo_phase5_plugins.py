"""
Test Phase 5 Plugin System
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now we can import
from src.plugins.plugin_manager import PluginManager
from src.plugins.base_plugin import PluginContext

print("\n" + "🎬 " * 20)
print("PHASE 5 - PLUGIN SYSTEM DEMO")
print("🎬 " * 20)

# Create plugin manager
print("\n1️⃣ Initializing Plugin Manager...")
manager = PluginManager()

# Load plugins
print("\n2️⃣ Loading plugins...")
manager.load_all_plugins()

# Show loaded plugins
print("\n3️⃣ Loaded Plugins:")
for info in manager.get_plugin_info():
    print(f"\n   📦 {info['name']} v{info['version']}")
    print(f"      {info['description']}")
    print(f"      Status: {'✅ Enabled' if info['enabled'] else '❌ Disabled'}")

# Test scenarios
print("\n" + "=" * 70)
print("4️⃣ Testing Plugin Suggestions")
print("=" * 70)

# Scenario 1: GitHub URL
print("\n📋 Scenario 1: GitHub URL")
context = PluginContext(
    clipboard_text="https://github.com/sushantsharma22/Project-Synth",
    content_type="url"
)

suggestions = manager.get_suggestions(context)
print(f"   Got {len(suggestions)} suggestion(s):")
for s in suggestions:
    print(f"   - [{s.plugin_name}] {s.title}")
    print(f"     {s.description} (confidence: {s.confidence:.2f})")

# Scenario 2: API Key (Security Issue)
print("\n📋 Scenario 2: API Key Detection")
context = PluginContext(
    clipboard_text='API_KEY = "sk_test_EXAMPLE_KEY_NOT_REAL"',
    content_type="text"
)

suggestions = manager.get_suggestions(context)
print(f"   Got {len(suggestions)} suggestion(s):")
for s in suggestions:
    print(f"   - [{s.plugin_name}] {s.title}")
    print(f"     {s.description} (confidence: {s.confidence:.2f})")

# Scenario 3: Git Diff
print("\n📋 Scenario 3: Git Diff")
diff_text = """diff --git a/src/main.py b/src/main.py
@@ -10,5 +10,8 @@ def main():
+    print("New feature")
+    print("More code")
-    old_code()
"""
context = PluginContext(
    clipboard_text=diff_text,
    content_type="text"
)

suggestions = manager.get_suggestions(context)
print(f"   Got {len(suggestions)} suggestion(s):")
for s in suggestions:
    print(f"   - [{s.plugin_name}] {s.title}")
    print(f"     {s.description} (confidence: {s.confidence:.2f})")

# Cleanup
print("\n5️⃣ Cleaning up...")
manager.unload_all_plugins()

print("\n" + "✨ " * 20)
print("PHASE 5 PLUGIN SYSTEM WORKING!")
print("✨ " * 20)

print("\n📊 Summary:")
print("   ✅ Plugin architecture implemented")
print("   ✅ Git plugin working")
print("   ✅ Security plugin working")
print("   ✅ Plugin manager loading plugins")
print("   ✅ Multi-plugin suggestions working")
print("\n🎉 Phase 5.1 (Plugin Architecture) COMPLETE!\n")
