"""
🎬 LIVE SYNTH DEMO 🎬
Real-time demonstration of the complete system:
Senses → Brain → Hands → Plugins

This will:
1. Take a screenshot of your current screen
2. Extract text using OCR
3. Send to Brain for analysis
4. Get plugin suggestions
5. Show actionable solutions

Author: Sushant Sharma
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import Senses
try:
    from src.senses.screen_capture import ScreenCapture
    from src.senses.ocr_engine import OCREngine
    SENSES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Senses not available: {e}")
    SENSES_AVAILABLE = False

# Import Brain
try:
    from brain_client import DeltaBrain
    BRAIN_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Brain not available: {e}")
    BRAIN_AVAILABLE = False

# Import Plugins
try:
    from src.plugins.plugin_manager import PluginManager
    from src.plugins.base_plugin import PluginContext
    PLUGINS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Plugins not available: {e}")
    PLUGINS_AVAILABLE = False


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 100)
    print(f" {title.center(98)} ")
    print("=" * 100)


def print_section(title):
    """Print a section header"""
    print("\n" + "─" * 100)
    print(f"📍 {title}")
    print("─" * 100)


def live_demo():
    """Run a live demonstration of the complete system"""
    
    print_header("🎬 LIVE SYNTH DEMO - REAL-TIME SYSTEM TEST 🎬")
    
    print("\n🎯 This demo will:")
    print("   1. 📸 Take a screenshot of your current screen")
    print("   2. 👁️  Extract text using OCR (Senses)")
    print("   3. 🧠 Send to Brain for AI analysis")
    print("   4. 🔌 Get intelligent plugin suggestions")
    print("   5. ✋ Show actionable solutions (Hands)")
    
    # Check prerequisites
    print_section("System Check")
    
    if not all([SENSES_AVAILABLE, BRAIN_AVAILABLE, PLUGINS_AVAILABLE]):
        print("\n❌ Missing components:")
        if not SENSES_AVAILABLE:
            print("   • Senses (OCR/Screenshot)")
        if not BRAIN_AVAILABLE:
            print("   • Brain (Ollama)")
        if not PLUGINS_AVAILABLE:
            print("   • Plugins")
        print("\n💡 Install missing dependencies first!")
        return False
    
    print("✅ All systems available!")
    
    # Initialize components
    print_section("Initializing Components")
    
    print("🔧 Loading Senses...")
    screen_capture = ScreenCapture()
    ocr_engine = OCREngine()
    print("   ✅ Screen Capture ready")
    print("   ✅ OCR Engine ready")
    
    print("\n🔧 Loading Brain...")
    brain = DeltaBrain()
    status = brain.check_connection()
    print(f"   Brain Status:")
    for mode, result in status.items():
        print(f"      • {mode:10} → {result}")
    
    available_models = sum(1 for s in status.values() if "✅" in s)
    if available_models == 0:
        print("\n❌ No Brain models available! Start Ollama first.")
        return False
    
    print(f"   ✅ {available_models}/3 Brain models available")
    
    print("\n🔧 Loading Plugins...")
    plugin_dirs = [str(project_root / "src" / "plugins" / "core")]
    plugin_manager = PluginManager(plugin_dirs=plugin_dirs)
    plugin_manager.load_all_plugins()
    print(f"   ✅ Loaded {len(plugin_manager.plugins)} plugins:")
    for name in sorted(plugin_manager.plugins.keys()):
        print(f"      • {name}")
    
    # PHASE 1: SENSES - Capture Screen
    print_section("PHASE 1: SENSES 👁️ - Capturing Your Screen")
    
    print("\n📸 Taking screenshot in 3 seconds...")
    print("   💡 Make sure your screen shows what you want analyzed!")
    
    for i in range(3, 0, -1):
        print(f"   {i}...", end=" ", flush=True)
        time.sleep(1)
    print("📸 SNAP!")
    
    # Take screenshot
    img = screen_capture.capture(monitor=1)
    if not img:
        print("❌ Failed to capture screenshot")
        print("💡 Make sure to grant Screen Recording permission:")
        print("   System Preferences → Privacy → Screen Recording")
        return False
    
    # Save screenshot to file
    screenshots_dir = project_root / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = screenshots_dir / f"synth_live_{timestamp}.png"
    img.save(screenshot_path)
    
    print(f"\n✅ Screenshot saved: {screenshot_path.name}")
    print(f"   Location: {screenshot_path.absolute()}")
    print(f"   Size: {screenshot_path.stat().st_size / 1024:.1f} KB")
    
    # Extract text using OCR
    print("\n👁️  Extracting text from screenshot...")
    start_time = time.time()
    
    ocr_result = ocr_engine.extract_text(str(screenshot_path))
    ocr_time = time.time() - start_time
    
    if not ocr_result or not ocr_result.get('text'):
        print("❌ No text found in screenshot")
        return False
    
    extracted_text = ocr_result['text']
    confidence = ocr_result.get('confidence', 0)
    
    print(f"✅ OCR complete ({ocr_time:.2f}s)")
    print(f"   Confidence: {confidence:.0%}")
    print(f"   Text length: {len(extracted_text)} characters")
    print(f"\n📝 Extracted Text Preview:")
    print("   " + "─" * 96)
    
    # Show first 500 chars
    preview = extracted_text[:500]
    for line in preview.split('\n')[:10]:
        if line.strip():
            print(f"   {line[:94]}")
    
    if len(extracted_text) > 500:
        print(f"   ... ({len(extracted_text) - 500} more characters)")
    print("   " + "─" * 96)
    
    # PHASE 2: BRAIN - Analyze Content
    print_section("PHASE 2: BRAIN 🧠 - AI Analysis")
    
    print("\n🧠 Sending to Brain for analysis...")
    print("   Model: balanced (qwen2.5:7b)")
    print("   Processing...", end=" ", flush=True)
    
    start_time = time.time()
    
    brain_prompt = f"""Analyze this text extracted from a screenshot and provide:
1. What is this content about?
2. What problems or questions do you see?
3. What actions should the user take?
4. Any errors or issues to fix?

Text from screenshot:
{extracted_text[:1000]}
"""
    
    try:
        brain_response = brain.ask(brain_prompt, mode="balanced")
        brain_time = time.time() - start_time
        
        print(f"\n✅ Brain analysis complete ({brain_time:.2f}s)")
        print("\n🧠 Brain Says:")
        print("   " + "─" * 96)
        
        # Show Brain response
        for line in brain_response.split('\n')[:20]:
            if line.strip():
                print(f"   {line[:94]}")
        
        print("   " + "─" * 96)
        
    except Exception as e:
        print(f"\n❌ Brain error: {str(e)[:100]}")
        brain_response = None
    
    # PHASE 3: PLUGINS - Get Suggestions
    print_section("PHASE 3: PLUGINS 🔌 - Smart Suggestions")
    
    print("\n🔌 Getting plugin suggestions...")
    
    plugin_context = PluginContext(clipboard_text=extracted_text)
    suggestions = plugin_manager.get_suggestions(plugin_context)
    
    print(f"✅ Generated {len(suggestions)} suggestions")
    
    if suggestions:
        activated_plugins = set(s.plugin_name for s in suggestions)
        print(f"\n📦 Activated Plugins ({len(activated_plugins)}):")
        for plugin_name in sorted(activated_plugins):
            print(f"   • {plugin_name}")
        
        print(f"\n💡 Top Suggestions:")
        print("   " + "─" * 96)
        
        for i, suggestion in enumerate(suggestions[:5], 1):
            print(f"\n   {i}. {suggestion.title} ({suggestion.confidence:.0%})")
            print(f"      Plugin: {suggestion.plugin_name}")
            print(f"      {suggestion.description}")
            
            # Show action if available
            if hasattr(suggestion, 'action') and suggestion.action:
                print(f"      Action: {suggestion.action.get('name', 'N/A')}")
        
        print("\n   " + "─" * 96)
    else:
        print("   No suggestions (content might be too generic)")
    
    # PHASE 4: SUMMARY
    print_section("SUMMARY - Complete System Flow")
    
    print("\n✅ PHASE 1 - SENSES:")
    print(f"   📸 Screenshot: {Path(screenshot_path).name}")
    print(f"   👁️  OCR: {len(extracted_text)} chars extracted ({confidence:.0%} confidence)")
    
    print("\n✅ PHASE 2 - BRAIN:")
    print(f"   🧠 Model: qwen2.5:7b (balanced)")
    print(f"   ⚡ Response time: {brain_time:.2f}s")
    print(f"   📊 Analysis: {len(brain_response) if brain_response else 0} chars")
    
    print("\n✅ PHASE 3 - PLUGINS:")
    print(f"   🔌 Plugins loaded: {len(plugin_manager.plugins)}")
    print(f"   💡 Suggestions: {len(suggestions)}")
    print(f"   🎯 Activated: {len(activated_plugins) if suggestions else 0}")
    
    print("\n✅ PHASE 4 - HANDS (Ready):")
    total_actions = sum(1 for s in suggestions if hasattr(s, 'action') and s.action)
    print(f"   ✋ Can execute {total_actions} actions")
    
    print_header("🎉 LIVE DEMO COMPLETE! 🎉")
    
    print("\n📊 Full System Verified:")
    print("   ✅ Senses captured and processed your screen")
    print("   ✅ Brain analyzed the content with AI")
    print("   ✅ Plugins generated smart suggestions")
    print("   ✅ Hands ready to execute actions")
    print("\n🚀 ALL PHASES WORKING TOGETHER IN REAL-TIME!")
    
    return True


if __name__ == "__main__":
    try:
        success = live_demo()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
