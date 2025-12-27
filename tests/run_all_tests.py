#!/usr/bin/env python3
"""
Simple test runner for all tests.

Runs tests without requiring pytest. Works with the current test structure.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import all test modules
from unit.test_html_processing import TestHTMLStripping, TestTextTruncation
from unit.test_field_filtering import TestFieldSkipping, TestURLDetection, TestFieldNameFormatting, TestIconInference
from functional.test_application import (
    TestBindDataSingleObject, TestBindDataList, TestBindDataPrimitives, TestErrorHandling,
    TestGitHubAPI, TestWebSearchAPI
)


def run_test_class(test_class):
    """Run all tests in a test class."""
    class_name = test_class.__name__
    passed = 0
    failed = 0
    errors = []

    # Get all test methods
    test_methods = [m for m in dir(test_class) if m.startswith('test_')]

    for method_name in test_methods:
        try:
            # Create instance and run test
            instance = test_class()
            method = getattr(instance, method_name)
            method()
            passed += 1
            print(f"  ✓ {method_name}")
        except AssertionError as e:
            failed += 1
            print(f"  ✗ {method_name}")
            errors.append((f"{class_name}.{method_name}", str(e)))
        except Exception as e:
            failed += 1
            print(f"  ✗ {method_name} (ERROR)")
            errors.append((f"{class_name}.{method_name}", f"ERROR: {str(e)}"))

    return passed, failed, errors


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("RUNNING ALL TESTS")
    print("=" * 70)

    total_passed = 0
    total_failed = 0
    all_errors = []

    # Test groups
    test_groups = [
        ("Unit Tests - HTML Processing", [TestHTMLStripping, TestTextTruncation]),
        ("Unit Tests - Field Filtering", [TestFieldSkipping, TestURLDetection, TestFieldNameFormatting, TestIconInference]),
        ("Functional Tests - Data Binding", [TestBindDataSingleObject, TestBindDataList, TestBindDataPrimitives, TestErrorHandling]),
        ("Functional Tests - Real-World APIs", [TestGitHubAPI, TestWebSearchAPI]),
    ]

    for group_name, test_classes in test_groups:
        print(f"\n{group_name}")
        print("-" * 70)

        for test_class in test_classes:
            print(f"\n{test_class.__name__}:")
            passed, failed, errors = run_test_class(test_class)
            total_passed += passed
            total_failed += failed
            all_errors.extend(errors)

    # Summary
    print("\n" + "=" * 70)
    print(f"SUMMARY: {total_passed} passed, {total_failed} failed")
    print("=" * 70)

    if all_errors:
        print("\nFailed tests:")
        for test_name, error in all_errors:
            print(f"\n  ✗ {test_name}")
            if error:
                print(f"    {error}")

    return total_failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
