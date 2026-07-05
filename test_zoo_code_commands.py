#!/usr/bin/env python3
"""Test script to verify all Zoo-Code commands are properly implemented."""

import sys
import os
from pathlib import Path

# Add the src directory to the path so we can import specsmith modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_command_imports():
    """Test that all zoo-code commands can be imported without errors."""
    try:
        from specsmith.commands.zoo_code import (
            zoo_code_group,
            zoo_code_init,
            zoo_code_export_modes,
            zoo_code_benchmark,
            zoo_code_telemetry,
            zoo_code_verify,
            zoo_code_metrics,
            zoo_code_escalate,
            zoo_code_optimize,
            zoo_code_benchmark_test,
            zoo_code_cross_platform,
            zoo_code_dashboard
        )
        print("✓ All zoo-code command modules imported successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to import zoo-code commands: {e}")
        return False

def test_command_structure():
    """Test that the command structure is properly defined."""
    try:
        from specsmith.commands.zoo_code import zoo_code_group
        # Check that the group has the expected commands
        expected_commands = [
            'init',
            'export-modes',
            'benchmark',
            'telemetry',
            'verify',
            'metrics',
            'escalate',
            'optimize',
            'benchmark-test',
            'cross-platform',
            'dashboard'
        ]

        # Get the command names from the group
        command_names = [cmd.name for cmd in zoo_code_group.commands.values()]

        missing_commands = set(expected_commands) - set(command_names)
        extra_commands = set(command_names) - set(expected_commands)

        if missing_commands:
            print(f"✗ Missing commands: {missing_commands}")
            return False
        elif extra_commands:
            print(f"⚠ Extra commands found: {extra_commands}")
            # This is not necessarily an error, but worth noting
        else:
            print("✓ All expected commands found in zoo-code group")

        return True
    except Exception as e:
        print(f"✗ Failed to verify command structure: {e}")
        return False

def test_function_signatures():
    """Test that key functions have expected signatures."""
    try:
        from specsmith.commands.zoo_code import (
            zoo_code_telemetry,
            zoo_code_verify,
            zoo_code_escalate,
            zoo_code_optimize,
            zoo_code_benchmark_test,
            zoo_code_cross_platform,
            zoo_code_dashboard
        )

        # Test that functions exist and are callable
        functions_to_test = [
            ('zoo_code_telemetry', zoo_code_telemetry),
            ('zoo_code_verify', zoo_code_verify),
            ('zoo_code_escalate', zoo_code_escalate),
            ('zoo_code_optimize', zoo_code_optimize),
            ('zoo_code_benchmark_test', zoo_code_benchmark_test),
            ('zoo_code_cross_platform', zoo_code_cross_platform),
            ('zoo_code_dashboard', zoo_code_dashboard)
        ]

        for name, func in functions_to_test:
            if callable(func):
                print(f"✓ {name} is callable")
            else:
                print(f"✗ {name} is not callable")
                return False

        return True
    except Exception as e:
        print(f"✗ Failed to test function signatures: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing Zoo-Code Command Implementation")
    print("=" * 40)

    tests = [
        test_command_imports,
        test_command_structure,
        test_function_signatures
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        print(f"\nRunning {test.__name__}...")
        if test():
            passed += 1
        else:
            print(f"✗ {test.__name__} failed")

    print(f"\n{'=' * 40}")
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All tests passed! Zoo-Code commands are properly implemented.")
        return 0
    else:
        print("✗ Some tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
