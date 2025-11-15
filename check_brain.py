#!/usr/bin/env python3
"""
Quick Brain Connection Status Checker
Checks if all Brain models are accessible
"""

import requests
import sys

PORTS = {
    "3B (fast)": 11434,
    "7B (balanced)": 11435,
    "14B (smart)": 11436
}

print("🔍 Checking Delta Brain Connection...")
print("=" * 50)

all_connected = True

for model, port in PORTS.items():
    try:
        response = requests.get(f"http://localhost:{port}/api/version", timeout=2)
        if response.ok:
            print(f"✅ {model:15} (port {port}) → Connected")
        else:
            print(f"❌ {model:15} (port {port}) → Error")
            all_connected = False
    except requests.exceptions.ConnectionError:
        print(f"❌ {model:15} (port {port}) → Not reachable")
        all_connected = False
    except Exception as e:
        print(f"⚠️  {model:15} (port {port}) → {str(e)[:30]}")
        all_connected = False

print("=" * 50)

if all_connected:
    print("✅ All Brain models connected!")
    print("\nYou can now use:")
    print("  python test_brain.py")
    print("  python examples.py")
    sys.exit(0)
else:
    print("❌ Brain not fully connected")
    print("\nTo connect:")
    print("  ./connect_brain_auto.sh")
    print("\nOr install auto-connect:")
    print("  ./install_auto_connect.sh")
    sys.exit(1)
