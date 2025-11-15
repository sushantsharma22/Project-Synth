#!/usr/bin/env python3
"""
Example usage of Delta Brain for code analysis
Shows practical use cases for the Brain system
"""
from brain_client import DeltaBrain

def main():
    brain = DeltaBrain()
    
    print("🧠 Delta Brain - Example Usage")
    print("=" * 60)
    
    # Example 1: Quick Math
    print("\n📌 Example 1: Quick Question (Fast Mode)")
    print("-" * 60)
    answer = brain.ask("What is the Fibonacci sequence?", mode="fast")
    print(answer)
    
    # Example 2: Debug an Error
    print("\n📌 Example 2: Debug Error (Balanced Mode)")
    print("-" * 60)
    buggy_code = """
def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)

scores = []
average = calculate_average(scores)
print(average)
"""
    fix = brain.analyze_error(
        error_msg="ZeroDivisionError: division by zero",
        code=buggy_code
    )
    print(fix)
    
    # Example 3: Explain Complex Code
    print("\n📌 Example 3: Explain Code (Balanced Mode)")
    print("-" * 60)
    complex_code = """
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
"""
    explanation = brain.explain_code(complex_code)
    print(explanation)
    
    # Example 4: Optimize Code
    print("\n📌 Example 4: Optimize Code (Smart Mode)")
    print("-" * 60)
    slow_code = """
def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(i+1, len(items)):
            if items[i] == items[j] and items[i] not in duplicates:
                duplicates.append(items[i])
    return duplicates
"""
    optimized = brain.optimize_code(slow_code, mode="smart")
    print(optimized)
    
    # Example 5: Code Review
    print("\n📌 Example 5: Code Review (Balanced Mode)")
    print("-" * 60)
    review_code = """
def process_user_data(data):
    result = []
    for item in data:
        result.append(item['name'].upper())
    return result
"""
    review = brain.review_code(review_code)
    print(review)
    
    print("\n" + "=" * 60)
    print("✅ Examples complete! Start building with the Brain! 🚀")

if __name__ == "__main__":
    main()
