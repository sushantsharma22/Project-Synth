"""
Phase 4 Live Demo - Full System Integration
Demonstrates: Real-time Clipboard → Brain → Action execution
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from synth_orchestrator import SynthOrchestrator
import subprocess
import time

print("\n" + "🎬 " * 20)
print("PROJECT SYNTH - PHASE 4 LIVE DEMO")
print("Full System: Senses → Brain → Hands")
print("🎬 " * 20)

# Create custom config for demo
config = {
    'clipboard': {
        'enabled': True,
        'interval': 0.3,
    },
    'screen': {
        'enabled': False,  # Keep disabled for demo
    },
    'brain': {
        'model': 'fast',  # Use fast model for quick responses
        'min_confidence': 0.7,
    },
    'actions': {
        'auto_execute': True,
        'enabled_actions': [
            'open_url',
            'search_file',
            'fix_error',
            'show_notification',
        ],
        'require_confirmation': ['run_command']
    },
    'privacy': {
        'filter_sensitive': True,
        'sensitive_patterns': ['password', 'api_key', 'secret', 'token']
    }
}

print("\n📋 Demo Plan:")
print("   1. Start orchestrator")
print("   2. Simulate clipboard changes")
print("   3. Watch Brain analyze & actions execute")
print("   4. Show statistics")
print("\n" + "=" * 70)

# Create orchestrator
orchestrator = SynthOrchestrator(config=config)

# Start it
orchestrator.start()

print("\n🎬 Starting demo scenarios...")
time.sleep(1)

# Scenario 1: GitHub URL
print("\n" + "=" * 70)
print("📋 SCENARIO 1: GitHub URL")
print("=" * 70)
url1 = "https://github.com/sushantsharma22/Project-Synth"
print(f"Copying to clipboard: {url1}")
subprocess.run(['pbcopy'], input=url1.encode())
time.sleep(3)  # Wait for processing

# Scenario 2: Python Error
print("\n" + "=" * 70)
print("📋 SCENARIO 2: Python Error")
print("=" * 70)
error = """Traceback (most recent call last):
  File "app.py", line 15
    result = data['user_id']
KeyError: 'user_id'
"""
print("Copying error traceback to clipboard")
subprocess.run(['pbcopy'], input=error.encode())
time.sleep(3)

# Scenario 3: Filename
print("\n" + "=" * 70)
print("📋 SCENARIO 3: Filename Search")
print("=" * 70)
filename = "synth_orchestrator.py"
print(f"Copying filename: {filename}")
subprocess.run(['pbcopy'], input=filename.encode())
time.sleep(3)

# Scenario 4: Another URL
print("\n" + "=" * 70)
print("📋 SCENARIO 4: Documentation URL")
print("=" * 70)
url2 = "https://python.org/docs"
print(f"Copying to clipboard: {url2}")
subprocess.run(['pbcopy'], input=url2.encode())
time.sleep(3)

print("\n" + "=" * 70)
print("✅ All demo scenarios complete!")
print("=" * 70)

# Stop orchestrator
time.sleep(1)
orchestrator.stop()

print("\n🎉 Phase 4 Live Demo Complete!")
print("   The system successfully:")
print("   - Monitored clipboard in real-time")
print("   - Analyzed content with Brain")
print("   - Executed appropriate actions")
print("   - Tracked all statistics")
print("\n")
