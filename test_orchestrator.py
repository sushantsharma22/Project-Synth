"""Quick test of the orchestrator"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from synth_orchestrator import SynthOrchestrator
import time

print("\n🧪 Testing Orchestrator for 10 seconds...\n")

# Create orchestrator
orchestrator = SynthOrchestrator()

# Start it
orchestrator.start()

# Let it run for 10 seconds
print("⏱️  Running for 10 seconds...")
print("💡 Try copying something to clipboard!\n")

time.sleep(10)

# Stop it
orchestrator.stop()

print("\n✅ Test complete!")
