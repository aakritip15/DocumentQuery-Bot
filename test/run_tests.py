#!/usr/bin/env python3
"""
Focused test runner for Document Query Bot.
Runs simple, focused tests for each component.
"""

import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def run_focused_tests():
    """Run all focused tests."""
    print("🧪 Running Focused Tests")
    print("=" * 50)
    
    # Create test suite with focused tests
    loader = unittest.TestLoader()
    
    # Load focused test modules
    focused_tests = [
        'test_intent',
        'test_chat', 
        'test_date_extractor',
        'test_validator',
        'test_routes'
    ]
    
    suite = unittest.TestSuite()
    
    for test_module in focused_tests:
        try:
            # Import and load tests from the module
            module = __import__(test_module)
            tests = loader.loadTestsFromModule(module)
            suite.addTests(tests)
            print(f"✅ Loaded tests from {test_module}")
        except ImportError as e:
            print(f"⚠️ Could not load {test_module}: {e}")
    
    if not suite.countTestCases():
        print("❌ No tests loaded!")
        return 1
    
    print(f"📋 Loaded {suite.countTestCases()} test cases")
    print("-" * 50)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {len(result.failures)} tests failed, {len(result.errors)} tests had errors")
        return 1


def list_focused_tests():
    """List all available focused test modules."""
    print("📋 Available Focused Test Modules:")
    print("=" * 40)
    
    test_dir = os.path.dirname(__file__)
    focused_test_files = [
        'test_intent.py',
        'test_chat.py',
        'test_date_extractor.py',
        'test_validator.py',
        'test_routes.py'
    ]
    
    for test_file in focused_test_files:
        if os.path.exists(os.path.join(test_dir, test_file)):
            module_name = test_file[:-3]  # Remove .py extension
            print(f"  • {module_name}")
    
    print(f"\nTotal: {len(focused_test_files)} focused test modules")


def run_single_test(test_module):
    """Run a single focused test module."""
    print(f"🧪 Running tests from {test_module}...")
    print("=" * 50)
    
    try:
        # Import and run tests from the module
        module = __import__(test_module)
        
        # Run tests from the module
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        
        if not suite.countTestCases():
            print(f"❌ No tests found in {test_module}")
            return 1
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Print summary
        print("\n" + "=" * 50)
        if result.wasSuccessful():
            print("✅ All tests passed!")
            return 0
        else:
            print(f"❌ {len(result.failures)} tests failed, {len(result.errors)} tests had errors")
            return 1
            
    except Exception as e:
        print(f"❌ Error running tests from {test_module}: {e}")
        return 1


def main():
    """Main function to run focused tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run focused tests for Document Query Bot')
    parser.add_argument('--module', '-m', help='Run tests from a specific module (e.g., test_intent)')
    parser.add_argument('--list', '-l', action='store_true', help='List all available focused test modules')
    parser.add_argument('--all', '-a', action='store_true', help='Run all focused tests (default)')
    
    args = parser.parse_args()
    
    if args.list:
        list_focused_tests()
        return 0
    
    if args.module:
        return run_single_test(args.module)
    
    # Default: run all focused tests
    return run_focused_tests()


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
