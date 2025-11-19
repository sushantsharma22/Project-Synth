#!/usr/bin/env python3
"""
Quick Connection Checker for Project Synth
Diagnoses common issues that cause hangs and timeouts
"""

import sys
import time
import subprocess
import requests
from pathlib import Path

def print_header(msg):
    print("\n" + "=" * 70)
    print(f" {msg.center(68)} ")
    print("=" * 70)

def print_section(msg):
    print(f"\n{'─' * 70}")
    print(f"📍 {msg}")
    print(f"{'─' * 70}")

def check_ssh_tunnel():
    """Check if SSH tunnel is running"""
    print_section("Checking SSH Tunnel")
    
    try:
        result = subprocess.run(
            ['lsof', '-nP', '-iTCP:11434,11435,11436', '-sTCP:LISTEN'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.stdout:
            print("✅ SSH tunnel is running:")
            for line in result.stdout.strip().split('\n')[:10]:
                print(f"   {line}")
            return True
        else:
            print("❌ SSH tunnel is NOT running")
            print("\n💡 Start the tunnel with:")
            print("   ./scripts/connect_brain_key.sh")
            print("   OR")
            print("   ssh -L 11434:localhost:11434 -L 11435:localhost:11435 -L 11436:localhost:11436 sharmas1@delta.cs.uwindsor.ca")
            return False
    except Exception as e:
        print(f"❌ Error checking tunnel: {e}")
        return False

def check_brain_ports():
    """Check if Brain ports respond"""
    print_section("Checking Brain Ports")
    
    ports = {
        11434: "Fast Model (3B)",
        11435: "Balanced Model (7B)",
        11436: "Smart Model (14B)"
    }
    
    working_ports = []
    
    for port, desc in ports.items():
        try:
            print(f"\n🔍 Testing {desc} on port {port}...", end=" ", flush=True)
            
            start = time.time()
            response = requests.get(
                f"http://localhost:{port}/api/version",
                timeout=3
            )
            elapsed = (time.time() - start) * 1000
            
            if response.status_code == 200:
                print(f"✅ OK ({elapsed:.0f}ms)")
                working_ports.append(port)
            else:
                print(f"❌ Error {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"⏱️  TIMEOUT (>3s) - May be overloaded")
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection refused - Not running")
        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}")
    
    return working_ports

def quick_brain_test(port=11434):
    """Do a quick test with the Brain"""
    print_section("Quick Brain Test")
    
    try:
        print(f"\n🧠 Sending test prompt to port {port}...")
        print("   ⏳ This should take 3-10 seconds...")
        
        start = time.time()
        response = requests.post(
            f"http://localhost:{port}/api/generate",
            json={
                "model": "qwen2.5:3b",
                "prompt": "Say 'OK' if you can hear me",
                "stream": False
            },
            timeout=30
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('response', '')
            print(f"✅ Brain responded in {elapsed:.1f}s")
            print(f"   Response: {answer[:100]}")
            return True
        else:
            print(f"❌ Error {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏱️  TIMEOUT after 30s")
        print("\n💡 Possible causes:")
        print("   • Model is still loading (wait 1-2 minutes)")
        print("   • Brain server is overloaded")
        print("   • Network issues to Delta server")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def check_dependencies():
    """Check if required Python packages are installed"""
    print_section("Checking Python Dependencies")
    
    required = {
        'requests': 'HTTP client',
        'PIL': 'Image processing (Pillow)',
        'pytesseract': 'OCR engine'
    }
    
    all_ok = True
    for package, desc in required.items():
        try:
            __import__(package)
            print(f"✅ {package:15} - {desc}")
        except ImportError:
            print(f"❌ {package:15} - {desc} (MISSING)")
            all_ok = False
    
    if not all_ok:
        print("\n💡 Install missing packages:")
        print("   pip install -r requirements.txt")
    
    return all_ok

def main():
    print_header("🔍 PROJECT SYNTH CONNECTION DIAGNOSTICS")
    
    print("\n🎯 This tool will diagnose common issues that cause hangs\n")
    
    # Check 1: Dependencies
    deps_ok = check_dependencies()
    
    # Check 2: SSH Tunnel
    tunnel_ok = check_ssh_tunnel()
    
    # Check 3: Brain Ports
    working_ports = check_brain_ports()
    
    # Check 4: Quick test if any port works
    if working_ports:
        test_ok = quick_brain_test(working_ports[0])
    else:
        test_ok = False
        print_section("Quick Brain Test")
        print("⚠️  Skipped - No working ports found")
    
    # Summary
    print_header("📊 DIAGNOSIS SUMMARY")
    
    print("\n✅ Working Components:")
    if deps_ok:
        print("   • Python dependencies installed")
    if tunnel_ok:
        print("   • SSH tunnel is running")
    if working_ports:
        print(f"   • {len(working_ports)} Brain model(s) accessible")
    if test_ok:
        print("   • Brain responds to queries")
    
    print("\n❌ Issues Found:")
    issues = []
    if not deps_ok:
        issues.append("Missing Python dependencies")
        print("   • Missing Python dependencies")
    if not tunnel_ok:
        issues.append("SSH tunnel not running")
        print("   • SSH tunnel not running")
    if not working_ports:
        issues.append("No Brain models accessible")
        print("   • No Brain models accessible")
    if working_ports and not test_ok:
        issues.append("Brain not responding to queries")
        print("   • Brain not responding to queries")
    
    if not issues:
        print("   None - System looks healthy! 🎉")
    
    # Recommendations
    if issues:
        print("\n💡 RECOMMENDED ACTIONS:")
        print()
        
        if not tunnel_ok:
            print("1️⃣  Start SSH tunnel:")
            print("   ./scripts/connect_brain_key.sh")
            print()
        
        if tunnel_ok and not working_ports:
            print("2️⃣  Check Brain on Delta server:")
            print("   ssh sharmas1@delta.cs.uwindsor.ca")
            print("   systemctl --user status ollama-*")
            print()
        
        if not deps_ok:
            print("3️⃣  Install missing dependencies:")
            print("   pip install -r requirements.txt")
            print()
        
        if working_ports and not test_ok:
            print("4️⃣  Wait for models to load (1-2 minutes)")
            print("   Then run this script again")
            print()
    else:
        print("\n🚀 NEXT STEPS:")
        print("   Your system is ready! Try:")
        print("   python3 live_demo.py")
    
    print("\n" + "=" * 70)
    
    # Exit code
    sys.exit(0 if not issues else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
