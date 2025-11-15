#!/usr/bin/env python3
"""
Test script for Delta Brain connection
Tests all three models and available methods
"""
from brain_client import DeltaBrain
import time

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def main():
    brain = DeltaBrain()
    
    print("🧠 Delta Brain Connection Test")
    print("Testing connection to Delta HPC Brain System")
    
    # Test 1: Connection Status
    print_section("1. Connection Status Check")
    status = brain.check_connection()
    for mode, result in status.items():
        print(f"  {mode:10} → {result}")
    
    # Test 2: Fast Model (3B)
    print_section("2. Fast Model Test (3B - GPU 3)")
    print("Query: What is 10 + 10?")
    start = time.time()
    response = brain.ask("What is 10 + 10?", mode="fast")
    elapsed = time.time() - start
    print(f"Response: {response}")
    print(f"Time: {elapsed:.1f} seconds")
    
    # Test 3: Error Analysis (7B)
    print_section("3. Error Analysis Test (7B - GPU 2)")
    error_code = """
def divide(a, b):
    return a / b

result = divide(10, 0)
"""
    print("Testing error analysis...")
    start = time.time()
    analysis = brain.analyze_error("ZeroDivisionError: division by zero", error_code)
    elapsed = time.time() - start
    print(analysis[:300] + "..." if len(analysis) > 300 else analysis)
    print(f"Time: {elapsed:.1f} seconds")
    
    # Test 4: Code Explanation
    print_section("4. Code Explanation Test (7B)")
    code = "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"
    print(f"Code: {code}")
    start = time.time()
    explanation = brain.explain_code(code)
    elapsed = time.time() - start
    print(explanation[:300] + "..." if len(explanation) > 300 else explanation)
    print(f"Time: {elapsed:.1f} seconds")
    
    # Summary
    print_section("Test Summary")
    print("✅ All tests complete!")
    print("\nAvailable methods:")
    print("  • brain.ask(prompt, mode)")
    print("  • brain.analyze_error(error_msg, code)")
    print("  • brain.explain_code(code)")
    print("  • brain.optimize_code(code, mode)")
    print("  • brain.review_code(code)")
    print("  • brain.check_connection()")
    print("\nModes: 'fast', 'balanced', 'smart'")
    print("\nBrain is ready for your projects! 🚀")

if __name__ == "__main__":
    main()

