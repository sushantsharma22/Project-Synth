#!/usr/bin/env python3
"""
Phase 2 Demo: Senses → Brain → Actions
Complete end-to-end demonstration of proactive AI assistance.

This demo shows:
1. Clipboard monitoring (Phase 1)
2. Screenshot capture (Phase 1)  
3. Context package creation (Phase 1)
4. Brain AI analysis (Phase 2) ✨ NEW
5. Action suggestion (Phase 2) ✨ NEW
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.senses.clipboard_monitor import ClipboardMonitor
from src.senses.screen_capture import ScreenCapture
from src.senses.trigger_system import TriggerSystem, ContextPackage
from src.brain.brain_api_client import BrainAPIClient, BrainResponse


def demo_brain_analysis():
    """Demo: Brain analyzes different types of content."""
    print("\n" + "="*70)
    print("🧠 DEMO 1: Brain Analysis of Different Content Types")
    print("="*70)
    
    brain = BrainAPIClient()
    
    # Check connection
    print("\n🔌 Checking Brain connection...")
    if not brain.check_connection():
        print("❌ Brain is offline!")
        print("💡 Start with: ./brain_monitor_key.sh")
        return False
    print("✅ Brain is online!\n")
    
    # Test scenarios
    scenarios = [
        {
            'name': 'KeyError Exception',
            'content': "KeyError: 'user_id' not found in dictionary",
            'type': 'error',
            'expected_action': 'fix_error'
        },
        {
            'name': 'GitHub URL',
            'content': "https://github.com/sushantsharma22/Project-Synth",
            'type': 'url',
            'expected_action': 'open_url'
        },
        {
            'name': 'Python Code',
            'content': "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)",
            'type': 'code',
            'expected_action': 'explain_code'
        },
        {
            'name': 'File Path',
            'content': "/Users/sushant/project-synth/src/brain/brain_api_client.py",
            'type': 'path',
            'expected_action': 'search_file'
        }
    ]
    
    results = []
    
    for scenario in scenarios:
        print(f"📋 Testing: {scenario['name']}")
        print(f"   Content: {scenario['content'][:60]}...")
        
        # Create context
        context = ContextPackage(
            clipboard_content=scenario['content'],
            clipboard_metadata={
                'timestamp': time.time(),
                'type': scenario['type']
            }
        )
        
        # Analyze with Brain
        print(f"   🧠 Analyzing...")
        start = time.time()
        response = brain.analyze_context(context, mode='fast')
        elapsed = (time.time() - start) * 1000
        
        # Show results
        print(f"   ✅ Action: {response.action_type}")
        print(f"   💡 Suggestion: {response.suggested_action}")
        print(f"   🎯 Confidence: {response.confidence:.2f}")
        print(f"   ⏱️  Time: {elapsed:.0f}ms")
        
        # Check if expected
        correct = response.action_type == scenario['expected_action']
        status = "✅" if correct else "⚠️"
        print(f"   {status} Expected: {scenario['expected_action']}\n")
        
        results.append({
            'scenario': scenario['name'],
            'correct': correct,
            'time_ms': elapsed
        })
    
    # Summary
    total = len(results)
    correct = sum(1 for r in results if r['correct'])
    avg_time = sum(r['time_ms'] for r in results) / total
    
    print(f"📊 Results:")
    print(f"   Accuracy: {correct}/{total} ({correct/total*100:.0f}%)")
    print(f"   Avg time: {avg_time:.0f}ms")
    
    return correct >= total * 0.75  # 75% accuracy threshold


def demo_linkedin_scenario():
    """Demo: The flagship LinkedIn demo - KeyError detection."""
    print("\n" + "="*70)
    print("🎯 DEMO 2: LinkedIn Scenario - KeyError Detection")
    print("="*70)
    
    print("\n📝 Scenario:")
    print("   You're coding and encounter a KeyError.")
    print("   Project Synth detects it and suggests a fix.\n")
    
    brain = BrainAPIClient()
    
    # Simulate the error in clipboard
    error_message = """Traceback (most recent call last):
  File "app.py", line 42, in get_user
    user_name = user_data['name']
KeyError: 'name'"""
    
    print("📋 Clipboard content:")
    print(f"   {error_message[:80]}...")
    
    # Create context package
    context = ContextPackage(
        clipboard_content=error_message,
        clipboard_metadata={
            'timestamp': time.time(),
            'type': 'error'
        },
        screenshot_base64=None  # Could include screenshot of VS Code
    )
    
    print(f"\n📦 Context package created:")
    print(f"   ID: {context.context_id}")
    print(f"   Type: {context.clipboard_metadata['type']}")
    print(f"   Size: {context.get_size_kb():.2f} KB")
    
    # Analyze with Brain
    print(f"\n🧠 Sending to Brain for analysis...")
    start_time = time.time()
    response = brain.analyze_context(context, mode='balanced')
    total_time = (time.time() - start_time) * 1000
    
    # Show response
    print(f"\n💡 Brain Suggestion:")
    print(f"   Action: {response.action_type}")
    print(f"   Suggestion: {response.suggested_action}")
    print(f"   Confidence: {response.confidence:.2f}")
    print(f"   Reasoning: {response.reasoning}")
    print(f"   Response time: {total_time:.0f}ms")
    
    # Check target
    if total_time < 3000:
        print(f"\n✅ Response time target MET: <3 seconds")
        print(f"🎉 LinkedIn demo: READY!")
        return True
    else:
        print(f"\n⚠️  Response time target MISSED: {total_time/1000:.1f}s")
        return False


def demo_full_pipeline():
    """Demo: Complete pipeline from clipboard to action."""
    print("\n" + "="*70)
    print("🚀 DEMO 3: Full Pipeline (Clipboard → Brain → Action)")
    print("="*70)
    
    print("\n⚠️  This demo monitors your real clipboard!")
    print("Copy some text (error, URL, code) to test.")
    print("Will run for 15 seconds...\n")
    
    brain = BrainAPIClient()
    contexts_analyzed = []
    
    def on_context_ready(context: ContextPackage):
        """Called when context package is ready."""
        print(f"\n📦 Context captured!")
        print(f"   Type: {context.clipboard_metadata.get('type')}")
        print(f"   Content: {context.clipboard_content[:60]}...")
        
        # Analyze with Brain
        print(f"   🧠 Analyzing with Brain...")
        response = brain.analyze_context(context, mode='fast')
        
        print(f"   💡 Action: {response.action_type}")
        print(f"   ✨ Suggestion: {response.suggested_action}")
        print(f"   ⏱️  Time: {response.response_time_ms:.0f}ms")
        
        contexts_analyzed.append({
            'context': context,
            'response': response
        })
    
    # Start trigger system
    trigger = TriggerSystem(
        trigger_callback=on_context_ready,
        auto_screenshot=False  # Disable for faster testing
    )
    
    try:
        trigger.start(poll_interval=0.3)
        
        # Run for 15 seconds
        for i in range(15):
            time.sleep(1)
            remaining = 15 - i
            print(f"⏳ {remaining}s remaining... (copy something!)", end='\r')
        
        print("\n")
        trigger.stop()
        
        # Summary
        print(f"\n📊 Pipeline Summary:")
        print(f"   Contexts analyzed: {len(contexts_analyzed)}")
        
        if contexts_analyzed:
            avg_time = sum(c['response'].response_time_ms for c in contexts_analyzed) / len(contexts_analyzed)
            print(f"   Avg response time: {avg_time:.0f}ms")
            print(f"\n✅ Full pipeline: WORKING")
            return True
        else:
            print(f"   No clipboard changes detected")
            print(f"   💡 Tip: Copy some text to test the pipeline")
            return True  # Not a failure, just no input
            
    except KeyboardInterrupt:
        trigger.stop()
        return False


def run_phase2_demos():
    """Run all Phase 2 demonstrations."""
    print("\n" + "🧠"*35)
    print("  PROJECT SYNTH - PHASE 2 DEMONSTRATIONS")
    print("  Brain AI Reasoning & Action Suggestions")
    print("🧠"*35)
    
    print(f"\n📅 Date: November 14, 2025")
    print(f"🎯 Phase: 2 - Brain AI Reasoning")
    print(f"⏱️  Estimated time: ~1 minute")
    
    results = {}
    
    # Run demos
    results['brain_analysis'] = demo_brain_analysis()
    results['linkedin_demo'] = demo_linkedin_scenario()
    results['full_pipeline'] = demo_full_pipeline()
    
    # Summary
    print("\n" + "="*70)
    print("📊 PHASE 2 DEMO SUMMARY")
    print("="*70)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        name_display = name.replace('_', ' ').title()
        print(f"   {status} - {name_display}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\n🎯 Results: {passed}/{total} demos passed")
    
    if passed == total:
        print(f"\n🎉 PHASE 2: BRAIN AI INTEGRATION WORKING!")
        print(f"✅ Ready for Phase 3: Hands (Automation)")
    else:
        print(f"\n⚠️  Some demos need attention")
    
    print(f"\n" + "="*70)
    
    return passed == total


if __name__ == "__main__":
    try:
        success = run_phase2_demos()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n🛑 Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
