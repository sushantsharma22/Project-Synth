"""
Quick test of Phase 4 Orchestrator
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from synth_orchestrator import SynthOrchestrator
import time

print("\n" + "=" * 70)
print("🧪 TESTING PHASE 4 ORCHESTRATOR")
print("=" * 70)

# Test 1: Initialize
print("\n1️⃣ Testing initialization...")
orchestrator = SynthOrchestrator()
print("   ✅ Orchestrator created")

# Test 2: Start
print("\n2️⃣ Testing start...")
orchestrator.start()
print("   ✅ Orchestrator started")

# Test 3: Run for 5 seconds
print("\n3️⃣ Running for 5 seconds...")
print("   💡 Try copying a URL to test clipboard monitoring!")
time.sleep(5)

# Test 4: Stop
print("\n4️⃣ Testing stop...")
orchestrator.stop()
print("   ✅ Orchestrator stopped")

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED")
print("=" * 70 + "\n")
