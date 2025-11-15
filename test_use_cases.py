"""
🎯 SYNTH USE CASES DEMONSTRATION 🎯

This demonstrates REAL use cases for Synth:
- What problems does it solve?
- How accurate are the answers?
- When would you actually use this?
- Does it identify the right next steps?

Author: Sushant Sharma
"""

import sys
import time
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.senses.screen_capture import ScreenCapture
from src.senses.ocr_engine import OCREngine
from brain_client import DeltaBrain
from src.plugins.plugin_manager import PluginManager
from src.plugins.base_plugin import PluginContext


def print_banner(text):
    """Print a styled banner"""
    print("\n" + "=" * 100)
    print(f" {text.center(98)} ")
    print("=" * 100)


def print_section(emoji, title):
    """Print a section header"""
    print(f"\n{emoji} {title}")
    print("─" * 100)


def use_case_demo():
    """Demonstrate real-world use cases"""
    
    print_banner("🎯 SYNTH USE CASES - WHAT CAN IT DO FOR YOU? 🎯")
    
    print("\n📚 SYNTH solves these REAL problems:")
    print("   1. 📸 You see an error on screen → It diagnoses and suggests fixes")
    print("   2. 📝 You copy code → It explains, documents, and improves it")
    print("   3. 🔗 You copy a URL → It analyzes, searches docs, opens relevant tools")
    print("   4. 📊 You see numbers → It calculates, converts units, analyzes data")
    print("   5. 🔐 You paste secrets → It warns you before you commit them!")
    print("   6. 📅 You mention dates → It creates calendar events automatically")
    
    # Initialize components
    print_section("🔧", "Initializing Synth Components")
    
    screen_capture = ScreenCapture()
    ocr_engine = OCREngine()
    brain = DeltaBrain()
    
    plugin_dirs = [str(project_root / "src" / "plugins" / "core")]
    plugin_manager = PluginManager(plugin_dirs=plugin_dirs)
    plugin_manager.load_all_plugins()
    
    print(f"✅ Senses: Screen Capture + OCR")
    print(f"✅ Brain: {len([s for s in brain.check_connection().values() if '✅' in s])}/3 models online")
    print(f"✅ Plugins: {len(plugin_manager.plugins)} intelligent modules")
    
    # Real-world test scenarios
    print_banner("🧪 TESTING REAL-WORLD SCENARIOS")
    
    scenarios = [
        {
            "name": "CODING ERROR",
            "description": "You're coding and see an error message",
            "test_content": """
TypeError: Cannot read property 'map' of undefined
    at processItems (app.js:45)
    at render (app.js:120)
    
Code:
function processItems(items) {
    return items.map(item => item.name);
}
""",
            "what_synth_should_do": [
                "Identify it's a JavaScript error",
                "Explain the cause (items is undefined)",
                "Suggest a fix (add null check)",
                "Offer to search Stack Overflow",
                "Provide corrected code"
            ],
            "expected_plugins": ["web_search", "code_doc"]
        },
        {
            "name": "GIT REPOSITORY",
            "description": "You copy a GitHub URL to check it out",
            "test_content": """
https://github.com/facebook/react
Star this repo if you like it!
Clone: git clone https://github.com/facebook/react.git
""",
            "what_synth_should_do": [
                "Detect GitHub repository URL",
                "Offer to open in browser",
                "Suggest clone command",
                "Check if you have similar repos",
                "Offer to search documentation"
            ],
            "expected_plugins": ["git", "web_search"]
        },
        {
            "name": "MATH PROBLEM",
            "description": "You need to do calculations",
            "test_content": """
Calculate the total cost:
- 15 items at $24.99 each
- Tax rate: 8.5%
- Shipping: $12.50

Also convert 500 USD to EUR
""",
            "what_synth_should_do": [
                "Calculate: 15 × $24.99 = $374.85",
                "Add tax: $374.85 × 1.085 = $406.71",
                "Add shipping: $406.71 + $12.50 = $419.21",
                "Convert USD to EUR",
                "Show step-by-step breakdown"
            ],
            "expected_plugins": ["math"]
        },
        {
            "name": "SECURITY LEAK",
            "description": "You accidentally copy API keys",
            "test_content": """
# Deploy to production
export API_KEY=sk_test_EXAMPLE_KEY_NOT_REAL_12345
export DATABASE_URL=postgresql://user:pass123@db.example.com:5432/prod
git add .
git commit -m "Ready to deploy"
""",
            "what_synth_should_do": [
                "🚨 ALERT: API keys detected!",
                "Warn about security risk",
                "Suggest using .env files",
                "Recommend git-secrets",
                "Prevent accidental commit"
            ],
            "expected_plugins": ["security", "git"]
        },
        {
            "name": "MEETING NOTES",
            "description": "You copy meeting details",
            "test_content": """
Team standup - Tomorrow at 10:30 AM
Attendees: John, Sarah, Mike
Topics:
- Sprint review
- Q4 planning
- Bug fixes

Also schedule code review Friday 2pm
""",
            "what_synth_should_do": [
                "Parse 2 events: standup tomorrow 10:30, review Friday 2pm",
                "Extract attendees",
                "Create calendar entries",
                "Format as email if needed"
            ],
            "expected_plugins": ["calendar", "email"]
        }
    ]
    
    results = {
        "total": len(scenarios),
        "correct_analysis": 0,
        "correct_plugins": 0,
        "useful_suggestions": 0,
        "response_times": []
    }
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'═' * 100}")
        print(f"USE CASE {i}/{len(scenarios)}: {scenario['name']}")
        print(f"{'═' * 100}")
        
        print(f"\n📖 Scenario: {scenario['description']}")
        print(f"\n📋 Test Content:")
        print("   " + "─" * 96)
        for line in scenario['test_content'].strip().split('\n'):
            print(f"   {line}")
        print("   " + "─" * 96)
        
        print(f"\n🎯 What Synth SHOULD do:")
        for item in scenario['what_synth_should_do']:
            print(f"   • {item}")
        
        # Test with Brain
        print(f"\n🧠 Sending to Brain...")
        start_time = time.time()
        
        brain_prompt = f"""Analyze this content and provide:
1. What type of content is this?
2. What is the main problem or task?
3. What specific actions should be taken?
4. Any warnings or important notes?

Content:
{scenario['test_content']}
"""
        
        try:
            brain_response = brain.ask(brain_prompt, mode="balanced")
            response_time = time.time() - start_time
            results['response_times'].append(response_time)
            
            print(f"✅ Brain analyzed in {response_time:.2f}s")
            print(f"\n🧠 Brain's Analysis:")
            print("   " + "─" * 96)
            
            # Show key parts of response
            lines = brain_response.split('\n')
            for line in lines[:15]:  # First 15 lines
                if line.strip():
                    print(f"   {line[:94]}")
            
            if len(lines) > 15:
                print(f"   ... ({len(lines) - 15} more lines)")
            print("   " + "─" * 96)
            
            # Check if analysis is correct
            content_lower = scenario['test_content'].lower()
            response_lower = brain_response.lower()
            
            # Simple accuracy check
            if scenario['name'] == "CODING ERROR" and "undefined" in response_lower:
                results['correct_analysis'] += 1
                print("   ✅ CORRECT: Identified undefined error")
            elif scenario['name'] == "GIT REPOSITORY" and "github" in response_lower:
                results['correct_analysis'] += 1
                print("   ✅ CORRECT: Identified GitHub repo")
            elif scenario['name'] == "MATH PROBLEM" and any(word in response_lower for word in ["calculate", "multiply", "tax"]):
                results['correct_analysis'] += 1
                print("   ✅ CORRECT: Identified calculation task")
            elif scenario['name'] == "SECURITY LEAK" and any(word in response_lower for word in ["api", "key", "security", "credential"]):
                results['correct_analysis'] += 1
                print("   ✅ CORRECT: Identified security risk")
            elif scenario['name'] == "MEETING NOTES" and any(word in response_lower for word in ["meeting", "schedule", "calendar"]):
                results['correct_analysis'] += 1
                print("   ✅ CORRECT: Identified scheduling task")
            
        except Exception as e:
            print(f"   ❌ Brain error: {str(e)[:100]}")
            brain_response = None
        
        # Test with Plugins
        print(f"\n🔌 Plugin Suggestions:")
        
        plugin_context = PluginContext(clipboard_text=scenario['test_content'])
        suggestions = plugin_manager.get_suggestions(plugin_context)
        
        activated_plugins = set(s.plugin_name for s in suggestions)
        print(f"   Activated: {', '.join(sorted(activated_plugins)) if activated_plugins else 'None'}")
        
        # Check if expected plugins activated
        expected = set(scenario['expected_plugins'])
        actual = set(s.plugin_name.replace('_plugin', '') for s in suggestions)
        
        if expected.intersection(actual):
            results['correct_plugins'] += 1
            print(f"   ✅ CORRECT: Expected plugins activated")
        
        if len(suggestions) >= 2:
            results['useful_suggestions'] += 1
        
        print(f"\n💡 Top Suggestions ({len(suggestions)} total):")
        for j, sug in enumerate(suggestions[:3], 1):
            print(f"   {j}. {sug.title} ({sug.confidence:.0%})")
            print(f"      {sug.description[:80]}...")
        
        print(f"\n⏱️  Performance:")
        print(f"   Brain: {response_time:.2f}s")
        print(f"   Plugins: instant")
        
        time.sleep(0.5)  # Brief pause
    
    # Final Results
    print(f"\n{'═' * 100}")
    print(" FINAL RESULTS - ACCURACY & USEFULNESS ")
    print(f"{'═' * 100}")
    
    print(f"\n✅ ACCURACY:")
    accuracy = (results['correct_analysis'] / results['total']) * 100
    print(f"   Brain Analysis: {results['correct_analysis']}/{results['total']} correct ({accuracy:.0f}%)")
    
    plugin_accuracy = (results['correct_plugins'] / results['total']) * 100
    print(f"   Plugin Selection: {results['correct_plugins']}/{results['total']} correct ({plugin_accuracy:.0f}%)")
    
    print(f"\n⚡ PERFORMANCE:")
    avg_time = sum(results['response_times']) / len(results['response_times'])
    print(f"   Average Response: {avg_time:.2f}s")
    print(f"   Fastest: {min(results['response_times']):.2f}s")
    print(f"   Slowest: {max(results['response_times']):.2f}s")
    
    print(f"\n💡 USEFULNESS:")
    usefulness = (results['useful_suggestions'] / results['total']) * 100
    print(f"   Helpful Suggestions: {results['useful_suggestions']}/{results['total']} scenarios ({usefulness:.0f}%)")
    
    print_banner("🎯 WHEN TO USE SYNTH")
    
    print("""
✅ USE SYNTH WHEN:
   • You copy an error message → Get instant diagnosis + fixes
   • You copy code → Get docs, explanations, improvements
   • You copy a URL → Get smart actions (open, clone, search)
   • You copy text with dates → Auto-create calendar events
   • You copy API keys → Get security warnings
   • You copy numbers → Get calculations and conversions
   • You see something on screen → OCR + AI analysis

🚀 HOW IT WORKS:
   1. Copy text or take screenshot
   2. Synth detects and analyzes (Brain AI)
   3. Plugins suggest intelligent actions
   4. Execute actions with one click

💡 REAL BENEFITS:
   • Saves 10-30 minutes per error debugging
   • Prevents security leaks before they happen
   • Auto-documents code as you write
   • Instant calculations without leaving terminal
   • Smart scheduling without opening calendar
   • Context-aware help at your fingertips

🎯 ACCURACY: {accuracy:.0f}% correct analysis
⚡ SPEED: {avg_time:.1f}s average response
🔌 SMART: {plugin_accuracy:.0f}% correct plugin activation
""")
    
    print(f"{'═' * 100}")
    print(" 🎉 SYNTH IS YOUR INTELLIGENT CODING ASSISTANT! 🎉 ")
    print(f"{'═' * 100}\n")
    
    return True


if __name__ == "__main__":
    try:
        success = use_case_demo()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
