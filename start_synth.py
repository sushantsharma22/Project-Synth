#!/usr/bin/env python3
"""
🚀 SYNTH - QUICK START 🚀

This script makes it easy to launch Synth menu bar app.
Just run: python start_synth.py
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("=" * 60)
    print(" " * 15 + "🧠 SYNTH MENU BAR APP 🧠")
    print("=" * 60)
    
    # Check if in correct directory
    if not Path("synth_menubar.py").exists():
        print("\n❌ Error: synth_menubar.py not found!")
        print("   Run this from the project-synth directory")
        sys.exit(1)
    
    print("\n✅ Starting Synth...")
    print("   • Menu bar icon will appear near WiFi")
    print("   • Click 🧠 to open assistant")
    print("   • Press Ctrl+C to stop\n")
    
    # Set environment
    env = os.environ.copy()
    
    try:
        # Run menu bar app
        subprocess.run(["python3", "synth_menubar.py"], env=env)
    except KeyboardInterrupt:
        print("\n\n👋 Synth stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
