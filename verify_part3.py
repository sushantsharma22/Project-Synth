#!/usr/bin/env python3
"""
Part 3 Quick Verification Script
Verifies that all Part 3 tools are properly integrated
"""

def main():
    print("\n" + "=" * 80)
    print("PART 3 VERIFICATION SCRIPT")
    print("=" * 80)
    print()
    
    # Test 1: Import core_tools
    print("Test 1: Importing core_tools...")
    try:
        from src.brain.core_tools import ALL_TOOLS
        print("✅ Successfully imported ALL_TOOLS")
    except Exception as e:
        print(f"❌ Failed to import: {e}")
        return False
    
    # Test 2: Import app_tools
    print("\nTest 2: Importing app_tools...")
    try:
        from src.brain.app_tools import APP_TOOLS
        print("✅ Successfully imported APP_TOOLS")
        print(f"   Found {len(APP_TOOLS)} app control tools")
    except Exception as e:
        print(f"❌ Failed to import: {e}")
        return False
    
    # Test 3: Import ai_tools
    print("\nTest 3: Importing ai_tools...")
    try:
        from src.brain.ai_tools import AI_TOOLS
        print("✅ Successfully imported AI_TOOLS")
        print(f"   Found {len(AI_TOOLS)} AI text processing tools")
    except Exception as e:
        print(f"❌ Failed to import: {e}")
        return False
    
    # Test 4: Verify tool count
    print("\nTest 4: Verifying tool count...")
    expected_total = 41
    actual_total = len(ALL_TOOLS)
    if actual_total == expected_total:
        print(f"✅ Tool count correct: {actual_total}/{expected_total}")
    else:
        print(f"❌ Tool count mismatch: {actual_total} (expected {expected_total})")
        return False
    
    # Test 5: Verify Part 3 tools
    print("\nTest 5: Verifying Part 3 tools in ALL_TOOLS...")
    expected_app_tools = [
        'chrome_open_url', 'safari_open_url', 'whatsapp_call', 'whatsapp_message',
        'spotify_play', 'spotify_control', 'quit_app', 'focus_app',
        'notes_create', 'get_active_app'
    ]
    expected_ai_tools = [
        'summarize_text', 'translate_text', 'explain_concept',
        'code_explain', 'code_debug', 'improve_writing'
    ]
    
    all_tool_names = [t.name if hasattr(t, 'name') else str(t) for t in ALL_TOOLS]
    
    missing_tools = []
    for tool_name in expected_app_tools + expected_ai_tools:
        if tool_name not in all_tool_names:
            missing_tools.append(tool_name)
    
    if not missing_tools:
        print("✅ All Part 3 tools found in ALL_TOOLS")
    else:
        print(f"❌ Missing tools: {', '.join(missing_tools)}")
        return False
    
    # Test 6: Display tool breakdown
    print("\nTest 6: Tool breakdown...")
    from src.brain.file_tools import FILE_TOOLS
    from src.brain.system_tools import SYSTEM_TOOLS
    
    print("  Tool Count by Category:")
    print(f"    Core tools: 10")
    print(f"    File tools: {len(FILE_TOOLS)}")
    print(f"    System tools: {len(SYSTEM_TOOLS)}")
    print(f"    App tools: {len(APP_TOOLS)} ✨")
    print(f"    AI tools: {len(AI_TOOLS)} ✨")
    print(f"    ────────────────")
    print(f"    TOTAL: {len(ALL_TOOLS)}")
    
    # Test 7: List Part 3 tools
    print("\nTest 7: Listing Part 3 tools...")
    print("\n  App Control Tools:")
    for i, tool in enumerate(APP_TOOLS, 1):
        tool_name = tool.name if hasattr(tool, 'name') else str(tool)
        print(f"    {i:2d}. {tool_name}")
    
    print("\n  AI Text Processing Tools:")
    for i, tool in enumerate(AI_TOOLS, 1):
        tool_name = tool.name if hasattr(tool, 'name') else str(tool)
        print(f"    {i:2d}. {tool_name}")
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print()
    print("Part 3 is fully integrated and ready to use!")
    print()
    print("Next steps:")
    print("  1. Run full test suite: python test_part3.py")
    print("  2. Start the agent: python synth_native.py")
    print("  3. Try: 'Open Chrome to github.com and explain what Git is'")
    print()
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
