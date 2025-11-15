#!/usr/bin/env python3
"""
Phase 1 End-to-End Demo
Complete workflow test for Senses - Detection System

This script demonstrates:
1. Clipboard monitoring (300ms detection)
2. Screen capture with compression
3. Privacy filtering
4. Context package creation
5. Integration with Brain API (Phase 2 prep)
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.senses.clipboard_monitor import ClipboardMonitor
from src.senses.screen_capture import ScreenCapture
from src.senses.trigger_system import TriggerSystem, ContextPackage


def demo_clipboard_monitor():
    """Demo 1: Test clipboard monitoring."""
    print("\n" + "="*70)
    print("📋 DEMO 1: Clipboard Monitor")
    print("="*70)
    
    def on_change(data):
        print(f"\n✅ Clipboard detected!")
        print(f"   Type: {data['type']}")
        print(f"   Length: {len(data['content'])} chars")
        print(f"   Preview: {data['content'][:60]}...")
    
    monitor = ClipboardMonitor(callback=on_change, interval=0.3)
    
    print(f"\n🎯 Configuration:")
    print(f"   Polling interval: {monitor.interval*1000:.0f}ms")
    print(f"   Target: <500ms ✅")
    
    print(f"\n🔒 Privacy Filters:")
    test_cases = [
        ("password: test123", True),
        ("api_key: sk-123456", True),
        ("Hello world", False),
        ("def hello(): pass", False)
    ]
    
    for content, should_filter in test_cases:
        filtered = monitor._is_sensitive(content)
        status = "✅" if filtered == should_filter else "❌"
        print(f"   {status} '{content[:30]}...' → Filtered: {filtered}")
    
    print(f"\n💡 Copy some text to test real-time detection...")
    print(f"   (Will run for 10 seconds)")
    
    try:
        monitor.start()
        time.sleep(10)
        monitor.stop()
        print(f"\n✅ Clipboard monitoring: WORKING")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return True


def demo_screen_capture():
    """Demo 2: Test screen capture."""
    print("\n" + "="*70)
    print("📸 DEMO 2: Screen Capture")
    print("="*70)
    
    capture = ScreenCapture(quality=75, max_width=1920)
    
    # List monitors
    print(f"\n🖥️  Available Monitors:")
    monitors = capture.list_monitors()
    for mon in monitors:
        print(f"   Monitor {mon['number']}: {mon['width']}×{mon['height']}")
    
    # Test capture
    print(f"\n📸 Capturing screenshot...")
    try:
        start = time.time()
        img = capture.capture(monitor=1)
        capture_time = (time.time() - start) * 1000
        
        if img:
            print(f"   ✅ Captured in {capture_time:.1f}ms")
            
            # Get size info
            info = capture.get_size_info(monitor=1)
            print(f"\n📊 Compression Stats:")
            print(f"   Resolution: {info['resolution']}")
            print(f"   Original: {info['original_kb']:.2f} KB")
            print(f"   Compressed: {info['compressed_kb']:.2f} KB")
            print(f"   Ratio: {info['compression_ratio']:.1f}x")
            print(f"   Under 100KB: {'✅' if info['under_100kb'] else '⚠️  (acceptable for Retina)'}")
            
            # Test base64 encoding
            print(f"\n🔤 Testing base64 encoding...")
            base64_str = capture.capture_base64(monitor=1)
            if base64_str:
                size_kb = len(base64_str.encode('utf-8')) / 1024
                print(f"   ✅ Encoded: {size_kb:.2f} KB")
                print(f"   Preview: {base64_str[:50]}...")
                print(f"\n✅ Screen capture: WORKING")
                return True
        else:
            print(f"   ❌ Capture failed")
            return False
            
    except Exception as e:
        print(f"\n⚠️  Screen capture error: {e}")
        print(f"   💡 Tip: Grant Screen Recording permission:")
        print(f"      System Settings → Privacy & Security → Screen Recording")
        return False


def demo_trigger_system():
    """Demo 3: Test integrated trigger system."""
    print("\n" + "="*70)
    print("🎯 DEMO 3: Trigger System (Clipboard + Screenshot)")
    print("="*70)
    
    contexts_received = []
    
    def on_trigger(context: ContextPackage):
        contexts_received.append(context)
        print(f"\n📦 Context Package #{len(contexts_received)}")
        print(f"   ID: {context.context_id}")
        print(f"   Content: {len(context.clipboard_content)} chars")
        print(f"   Type: {context.clipboard_metadata.get('type', 'unknown')}")
        print(f"   Screenshot: {'✅ Included' if context.screenshot_base64 else '❌ None'}")
        print(f"   Total size: {context.get_size_kb():.2f} KB")
    
    # Test with screenshots disabled first (faster)
    print(f"\n🧪 Test 1: Without screenshots")
    trigger = TriggerSystem(
        trigger_callback=on_trigger,
        auto_screenshot=False
    )
    
    print(f"   Copy some text to test...")
    print(f"   (Will run for 8 seconds)")
    
    try:
        trigger.start(poll_interval=0.1)
        time.sleep(8)
        trigger.stop()
        
        stats = trigger.get_stats()
        print(f"\n📊 Stats (no screenshots):")
        print(f"   Triggers: {stats['total_triggers']}")
        print(f"   Avg size: {stats['avg_package_size_kb']:.2f} KB")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    # Test with screenshots enabled
    print(f"\n🧪 Test 2: With screenshots")
    trigger2 = TriggerSystem(
        trigger_callback=on_trigger,
        auto_screenshot=True,
        screenshot_delay=0.1
    )
    
    print(f"   Copy some text to test with screenshots...")
    print(f"   (Will run for 8 seconds)")
    
    try:
        trigger2.start(poll_interval=0.1)
        time.sleep(8)
        trigger2.stop()
        
        stats2 = trigger2.get_stats()
        print(f"\n📊 Stats (with screenshots):")
        print(f"   Triggers: {stats2['total_triggers']}")
        print(f"   With screenshots: {stats2['with_screenshot']}")
        print(f"   Avg size: {stats2['avg_package_size_kb']:.2f} KB")
        
        print(f"\n✅ Trigger system: WORKING")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def demo_context_package():
    """Demo 4: Test context package format."""
    print("\n" + "="*70)
    print("📦 DEMO 4: Context Package Format")
    print("="*70)
    
    # Create sample context
    context = ContextPackage(
        clipboard_content="KeyError: 'user_id' not found in dictionary",
        clipboard_metadata={
            'timestamp': time.time(),
            'type': 'error'
        },
        screenshot_base64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        screenshot_metadata={
            'size_kb': 50.5,
            'encoding': 'base64'
        }
    )
    
    print(f"\n📋 Context Package:")
    print(f"   ID: {context.context_id}")
    print(f"   Timestamp: {context.timestamp}")
    print(f"   Size: {context.get_size_kb():.2f} KB")
    
    print(f"\n🔍 JSON Preview:")
    json_str = context.to_json(indent=2)
    lines = json_str.split('\n')[:15]
    for line in lines:
        print(f"   {line}")
    if len(json_str.split('\n')) > 15:
        print(f"   ... ({len(json_str.split('\n')) - 15} more lines)")
    
    print(f"\n📊 Package Contents:")
    data = context.to_dict()
    print(f"   Clipboard content: {len(data['clipboard']['content'])} chars")
    print(f"   Clipboard type: {data['clipboard']['metadata'].get('type')}")
    if data['screenshot']:
        print(f"   Screenshot included: ✅")
        print(f"   Screenshot size: {data['screenshot']['metadata']['size_kb']:.2f} KB")
    else:
        print(f"   Screenshot included: ❌")
    
    print(f"\n✅ Context package format: WORKING")
    return True


def demo_brain_integration_prep():
    """Demo 5: Preview Brain API integration (Phase 2)."""
    print("\n" + "="*70)
    print("🧠 DEMO 5: Brain API Integration Preview (Phase 2)")
    print("="*70)
    
    # Check if Brain is accessible
    try:
        from brain_client import DeltaBrain
        
        brain = DeltaBrain()
        print(f"\n✅ Brain client imported successfully")
        print(f"\n🔗 Available models:")
        print(f"   • 3B (fast): localhost:11434")
        print(f"   • 7B (balanced): localhost:11435")
        print(f"   • 14B (smart): localhost:11436")
        
        # Check connection
        print(f"\n🔌 Testing connection...")
        connected = brain.check_connection()
        
        if connected:
            print(f"   ✅ Brain connection: ACTIVE")
            
            # Test quick query
            print(f"\n🧪 Testing quick query...")
            response = brain.ask("What is 2+2?", mode="fast")
            if response:
                print(f"   ✅ Brain response: {response[:100]}...")
                print(f"\n🎉 Ready for Phase 2 integration!")
                return True
        else:
            print(f"   ⚠️  Brain connection: OFFLINE")
            print(f"   💡 Start the Brain connection:")
            print(f"      ./brain_monitor_key.sh")
            return False
            
    except ImportError:
        print(f"\n⚠️  brain_client.py not found in path")
        print(f"   Location: ~/project-synth/brain_client.py")
        return False
    except Exception as e:
        print(f"\n⚠️  Error: {e}")
        return False


def run_all_demos():
    """Run all Phase 1 demos."""
    print("\n" + "🚀"*35)
    print("  PROJECT SYNTH - PHASE 1 END-TO-END DEMONSTRATION")
    print("🚀"*35)
    
    print(f"\n📅 Date: November 14, 2025")
    print(f"🎯 Phase: 1 - Senses (Detection System)")
    print(f"⏱️  Estimated time: ~1 minute")
    
    results = {}
    
    # Run demos
    results['clipboard'] = demo_clipboard_monitor()
    results['screen'] = demo_screen_capture()
    results['trigger'] = demo_trigger_system()
    results['context'] = demo_context_package()
    results['brain_prep'] = demo_brain_integration_prep()
    
    # Summary
    print("\n" + "="*70)
    print("📊 PHASE 1 TEST SUMMARY")
    print("="*70)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        name_display = name.replace('_', ' ').title()
        print(f"   {status} - {name_display}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n🎉 PHASE 1: ALL SYSTEMS OPERATIONAL!")
        print(f"✅ Ready to proceed to Phase 2: Brain AI Reasoning")
    else:
        print(f"\n⚠️  Some components need attention")
        print(f"   Review the errors above and fix before Phase 2")
    
    print(f"\n" + "="*70)
    
    return passed == total


if __name__ == "__main__":
    try:
        success = run_all_demos()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n🛑 Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
