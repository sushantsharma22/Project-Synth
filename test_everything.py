#!/usr/bin/env python3
"""
🧪 COMPLETE SYSTEM TEST 🧪
Tests all phases and components to ensure everything works

Run this to verify the entire system:
  python test_everything.py
"""

import sys
import time
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_section(title):
    """Print test section header"""
    print(f"\n{'=' * 80}")
    print(f" {title.center(78)} ")
    print(f"{'=' * 80}\n")

def test_brain():
    """Test Brain AI connection"""
    test_section("TESTING BRAIN AI")
    
    try:
        from brain_client import DeltaBrain
        brain = DeltaBrain()
        status = brain.check_connection()
        
        print("🧠 Brain Status:")
        for mode, result in status.items():
            print(f"   {mode:10} → {result}")
        
        available = sum(1 for s in status.values() if "✅" in s)
        
        if available == 3:
            print(f"\n✅ ALL BRAIN MODELS ONLINE ({available}/3)")
            
            # Quick test
            print("\n📝 Quick test...")
            response = brain.ask("Say 'Brain online!' if you work", mode="fast")
            print(f"   Response: {response[:50]}...")
            return True
        else:
            print(f"\n⚠️  Only {available}/3 models available")
            return False
            
    except Exception as e:
        print(f"❌ Brain test failed: {e}")
        return False

def test_senses():
    """Test Senses (clipboard, screenshot, OCR)"""
    test_section("TESTING SENSES")
    
    try:
        from src.senses.screen_capture import ScreenCapture
        from src.senses.ocr_engine import OCREngine
        import pyperclip
        
        # Test clipboard
        print("📋 Testing clipboard...")
        pyperclip.copy("Test clipboard content")
        content = pyperclip.paste()
        assert content == "Test clipboard content"
        print("   ✅ Clipboard working")
        
        # Test screenshot
        print("\n📸 Testing screenshot...")
        capture = ScreenCapture()
        monitors = capture.list_monitors()
        print(f"   Found {len(monitors)} monitor(s)")
        
        img = capture.capture(monitor=1)
        if img:
            print(f"   ✅ Screenshot: {img.width}x{img.height}")
        else:
            print("   ⚠️  Screenshot failed (may need permissions)")
        
        # Test OCR
        print("\n👁️  Testing OCR...")
        ocr = OCREngine()
        if ocr.available:
            print("   ✅ OCR engine available")
        else:
            print("   ⚠️  OCR not available (install pytesseract)")
        
        return True
        
    except Exception as e:
        print(f"❌ Senses test failed: {e}")
        return False

def test_plugins():
    """Test Plugin system"""
    test_section("TESTING PLUGINS")
    
    try:
        from src.plugins.plugin_manager import PluginManager
        from src.plugins.base_plugin import PluginContext
        
        plugin_dirs = [str(project_root / "src" / "plugins" / "core")]
        pm = PluginManager(plugin_dirs=plugin_dirs)
        pm.load_all_plugins()
        
        print(f"🔌 Loaded {len(pm.plugins)} plugins:")
        for name in sorted(pm.plugins.keys()):
            print(f"   • {name}")
        
        # Test with sample content
        print("\n💡 Testing suggestions...")
        context = PluginContext(clipboard_text="Calculate 15 * 24 = ?")
        suggestions = pm.get_suggestions(context)
        print(f"   Generated {len(suggestions)} suggestions")
        
        if len(pm.plugins) == 8:
            print(f"\n✅ ALL 8 PLUGINS LOADED")
            return True
        else:
            print(f"\n⚠️  Only {len(pm.plugins)}/8 plugins loaded")
            return False
            
    except Exception as e:
        print(f"❌ Plugin test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test full integration"""
    test_section("TESTING FULL INTEGRATION")
    
    try:
        from brain_client import DeltaBrain
        from src.plugins.plugin_manager import PluginManager
        from src.plugins.base_plugin import PluginContext
        import pyperclip
        
        # Setup
        brain = DeltaBrain()
        pm = PluginManager([str(project_root / "src" / "plugins" / "core")])
        pm.load_all_plugins()
        
        # Test scenario
        test_text = "TypeError: Cannot read property 'map' of undefined"
        print(f"📋 Test scenario: {test_text}")
        
        # Brain analysis
        print("\n🧠 Brain analyzing...")
        start = time.time()
        response = brain.ask(f"Analyze this error: {test_text}", mode="fast")
        duration = time.time() - start
        print(f"   ✅ Response in {duration:.1f}s")
        print(f"   Preview: {response[:100]}...")
        
        # Plugin suggestions
        print("\n🔌 Getting plugin suggestions...")
        context = PluginContext(clipboard_text=test_text)
        suggestions = pm.get_suggestions(context)
        print(f"   ✅ {len(suggestions)} suggestions")
        
        if suggestions:
            print(f"   Top: {suggestions[0].title}")
        
        print("\n✅ FULL INTEGRATION WORKING")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_menu_bar():
    """Test menu bar app components"""
    test_section("TESTING MENU BAR APP")
    
    try:
        print("📦 Checking dependencies...")
        
        # Check rumps
        try:
            import rumps
            print("   ✅ rumps installed")
        except ImportError:
            print("   ❌ rumps not installed (pip install rumps)")
            return False
        
        # Check PyQt6
        try:
            from PyQt6.QtWidgets import QApplication
            print("   ✅ PyQt6 installed")
        except ImportError:
            print("   ❌ PyQt6 not installed (pip install PyQt6)")
            return False
        
        # Check if file exists
        menu_bar_file = project_root / "synth_menubar.py"
        if menu_bar_file.exists():
            print(f"   ✅ Menu bar app exists: {menu_bar_file.name}")
        else:
            print(f"   ❌ Menu bar app not found")
            return False
        
        print("\n✅ MENU BAR APP READY")
        print("\n💡 To launch: python synth_menubar.py")
        return True
        
    except Exception as e:
        print(f"❌ Menu bar test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print(" " * 20 + "🚀 SYNTH COMPLETE SYSTEM TEST 🚀")
    print("=" * 80)
    
    results = {
        "Brain AI": test_brain(),
        "Senses": test_senses(),
        "Plugins": test_plugins(),
        "Integration": test_integration(),
        "Menu Bar": test_menu_bar()
    }
    
    # Summary
    test_section("TEST SUMMARY")
    
    total = len(results)
    passed = sum(results.values())
    
    print("📊 Component Status:")
    for component, status in results.items():
        icon = "✅" if status else "❌"
        print(f"   {icon} {component}")
    
    print(f"\n{'=' * 80}")
    percentage = (passed / total) * 100
    
    if passed == total:
        print(f" ✅ ALL TESTS PASSED: {passed}/{total} ({percentage:.0f}%)")
        print("=" * 80)
        print("\n🎉 SYSTEM READY TO USE!")
        print("\n🚀 Launch: python start_synth.py")
        return True
    else:
        print(f" ⚠️  TESTS PASSED: {passed}/{total} ({percentage:.0f}%)")
        print("=" * 80)
        print(f"\n❌ {total - passed} component(s) need attention")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
