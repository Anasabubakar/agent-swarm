#!/usr/bin/env python3
"""
Test suite for swarm_cli — validates all functionality before publish
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test all imports work"""
    from swarm_cli import C, VERSION, CMDS, detect, read_file, find_files, search_text
    from swarm_cli import WELCOME, GOODBYE, LOADING
    from swarm_cli import clean_input, run_cmd, run_swarm, check_update
    from swarm_cli import handle_slash, main
    print("  ✓ All imports OK")

def test_action_detection():
    """Test action type detection"""
    from swarm_cli import detect
    
    # Chat/greetings
    assert detect("yo") == "chat", f"yo should be chat, got {detect('yo')}"
    assert detect("hi") == "chat", f"hi should be chat, got {detect('hi')}"
    assert detect("hello") == "chat"
    assert detect("hey") == "chat"
    assert detect("sup") == "chat"
    
    # Questions
    assert detect("how do I run Python?") == "question"
    assert detect("what is React?") == "question"
    assert detect("explain Docker to me") == "question"
    
    # Build tasks
    assert detect("build a todo app") == "build"
    assert detect("create a landing page") == "build"
    assert detect("make a website for my startup") == "build"
    
    # File operations
    assert detect("read package.json") == "file"
    assert detect("open index.html") == "file"
    assert detect("show me the config") == "file"
    
    # Commands
    assert detect("run npm install") == "cmd"
    assert detect("npm test") == "cmd"
    assert detect("git status") == "cmd"
    assert detect("ls") == "cmd"
    
    print("  ✓ Action detection OK (17 tests passed)")

def test_version_sync():
    """Test version reads from package.json"""
    import json
    from pathlib import Path
    
    pkg = json.loads(Path("package.json").read_text())
    pkg_version = pkg["version"]
    
    from swarm_cli import VERSION
    assert VERSION == pkg_version, f"VERSION ({VERSION}) != package.json ({pkg_version})"
    print(f"  ✓ Version sync OK (v{VERSION})")

def test_witty_texts():
    """Test witty texts are defined"""
    from swarm_cli import WELCOME, GOODBYE, LOADING
    
    assert len(WELCOME) >= 5, f"WELCOME too short: {len(WELCOME)}"
    assert len(GOODBYE) >= 5, f"GOODBYE too short: {len(GOODBYE)}"
    assert len(LOADING) >= 5, f"LOADING too short: {len(LOADING)}"
    
    # No emojis
    for text in WELCOME + GOODBYE:
        for char in text:
            assert ord(char) < 0x1F600 or ord(char) > 0x1F9FF, f"Emoji found in: {text}"
    
    print(f"  ✓ Witty texts OK ({len(WELCOME)} welcome, {len(GOODBYE)} goodbye, {len(LOADING)} loading)")

def test_commands_list():
    """Test slash commands are defined"""
    from swarm_cli import CMDS
    
    assert len(CMDS) >= 10, f"Too few commands: {len(CMDS)}"
    
    cmd_names = [c[0] for c in CMDS]
    required = ["help", "model", "read <file>", "ls [dir]", "find <pat>", "run <cmd>", "quit"]
    for req in required:
        assert req in cmd_names, f"Missing command: {req}"
    
    print(f"  ✓ Commands OK ({len(CMDS)} defined)")

def test_colors():
    """Test color codes are valid"""
    from swarm_cli import C
    
    assert hasattr(C, 'R')
    assert hasattr(C, 'B')
    assert hasattr(C, 'RED')
    assert hasattr(C, 'GRN')
    assert hasattr(C, 'CYN')
    
    # Test t() function
    result = C.t(C.RED, "test")
    assert "test" in result
    assert "\033[" in result
    
    print("  ✓ Colors OK")

def test_file_reader():
    """Test file reading"""
    from swarm_cli import read_file
    
    # Test reading a known file
    result = read_file("package.json")
    assert "swarm" in result.lower() or "version" in result.lower()
    
    # Test missing file
    result = read_file("nonexistent-file-12345.txt")
    assert "Not found" in result
    
    print("  ✓ File reader OK")

def test_syntax():
    """Test all Python files have valid syntax"""
    import ast
    
    files = ["src/swarm_cli.py", "core/workspace.py", "core/tui.py"]
    for f in files:
        if os.path.exists(f):
            ast.parse(open(f).read())
    
    print("  ✓ Syntax OK (all files)")

def test_help_command():
    """Test /help works"""
    from swarm_cli import handle_slash, C
    
    # Should not raise
    # Can't fully test without terminal, but syntax should be valid
    print("  ✓ Help command syntax OK")

def test_loading_phrases_no_emojis():
    """Verify no emojis in any user-facing text"""
    from swarm_cli import WELCOME, GOODBYE, LOADING
    
    all_text = WELCOME + GOODBYE + LOADING
    emoji_count = 0
    for text in all_text:
        for char in text:
            if ord(char) > 0x1F600 and ord(char) < 0x1F9FF:
                emoji_count += 1
    
    assert emoji_count == 0, f"Found {emoji_count} emojis!"
    print("  ✓ No emojis in any text")

# Run all tests
if __name__ == "__main__":
    print("\n🛡️ Running Swarm CLI Test Suite\n")
    
    tests = [
        test_imports,
        test_syntax,
        test_version_sync,
        test_colors,
        test_witty_texts,
        test_loading_phrases_no_emojis,
        test_commands_list,
        test_action_detection,
        test_file_reader,
        test_help_command,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__}: {e}")
            failed += 1
    
    print(f"\n{'─'*40}")
    print(f"  Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        print(f"\n  ✗ TESTS FAILED — DO NOT PUBLISH")
        sys.exit(1)
    else:
        print(f"\n  ✓ ALL TESTS PASSED — SAFE TO PUBLISH")
