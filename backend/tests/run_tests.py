#!/usr/bin/env python3
"""
Hedera-Flow Test Runner
Comprehensive test execution script with multiple test categories and reporting
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def run_command(cmd, description=""):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - start_time
    
    print(f"⏱️  Duration: {duration:.2f} seconds")
    print(f"📤 Exit Code: {result.returncode}")
    
    if result.stdout:
        print(f"📋 Output:\n{result.stdout}")
    
    if result.stderr:
        print(f"❌ Errors:\n{result.stderr}")
    
    return result

def setup_test_environment():
    """Setup test environment variables"""
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['HEDERA_MOCK_MODE'] = 'true'
    os.environ['DATABASE_URL'] = 'sqlite:///test_hedera_flow.db'
    os.environ['PYTHONPATH'] = str(backend_dir)
    
    print("🔧 Test environment configured:")
    print(f"   ENVIRONMENT: {os.environ.get('ENVIRONMENT')}")
    print(f"   HEDERA_MOCK_MODE: {os.environ.get('HEDERA_MOCK_MODE')}")
    print(f"   DATABASE_URL: {os.environ.get('DATABASE_URL')}")

def run_unit_tests(verbose=False):
    """Run unit tests"""
    cmd = ['python', '-m', 'pytest', 'tests/unit/']
    if verbose:
        cmd.append('-v')
    cmd.extend(['-m', 'unit'])
    
    return run_command(cmd, "Running Unit Tests")

def run_integration_tests(verbose=False):
    """Run integration tests"""
    cmd = ['python', '-m', 'pytest', 'tests/integration/']
    if verbose:
        cmd.append('-v')
    cmd.extend(['-m', 'integration'])
    
    return run_command(cmd, "Running Integration Tests")

def run_e2e_tests(verbose=False):
    """Run end-to-end tests"""
    cmd = ['python', '-m', 'pytest', 'tests/e2e/']
    if verbose:
        cmd.append('-v')
    cmd.extend(['-m', 'e2e'])
    
    return run_command(cmd, "Running End-to-End Tests")

def run_all_tests(verbose=False, coverage=False):
    """Run all tests"""
    cmd = ['python', '-m', 'pytest', 'tests/']
    if verbose:
        cmd.append('-v')
    if coverage:
        cmd.extend(['--cov=app', '--cov-report=html', '--cov-report=term-missing'])
    
    return run_command(cmd, "Running All Tests")

def run_specific_test(test_path, verbose=False):
    """Run a specific test file"""
    cmd = ['python', '-m', 'pytest', test_path]
    if verbose:
        cmd.append('-v')
    
    return run_command(cmd, f"Running Specific Test: {test_path}")

def run_tests_by_marker(marker, verbose=False):
    """Run tests by marker"""
    cmd = ['python', '-m', 'pytest', 'tests/', '-m', marker]
    if verbose:
        cmd.append('-v')
    
    return run_command(cmd, f"Running Tests with Marker: {marker}")

def check_dependencies():
    """Check if required test dependencies are installed"""
    required_packages = ['pytest', 'pytest-asyncio']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All required test dependencies are installed")
    return True

def generate_test_report():
    """Generate comprehensive test report"""
    print("\n" + "="*80)
    print("📊 HEDERA-FLOW TEST REPORT")
    print("="*80)
    
    # Test structure summary
    test_dirs = ['unit', 'integration', 'e2e', 'manual']
    for test_dir in test_dirs:
        test_path = Path(f"tests/{test_dir}")
        if test_path.exists():
            test_files = list(test_path.glob("test_*.py"))
            print(f"📁 {test_dir.upper()}: {len(test_files)} test files")
    
    # Run tests with coverage
    print("\n🔄 Running comprehensive test suite with coverage...")
    result = run_all_tests(verbose=True, coverage=True)
    
    if result.returncode == 0:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED!")
    
    return result.returncode == 0

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Hedera-Flow Test Runner")
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--e2e', action='store_true', help='Run end-to-end tests only')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--marker', '-m', help='Run tests with specific marker')
    parser.add_argument('--file', '-f', help='Run specific test file')
    parser.add_argument('--report', action='store_true', help='Generate comprehensive test report')
    
    args = parser.parse_args()
    
    # Setup
    print("🚀 Hedera-Flow Test Runner")
    print("="*40)
    
    if not check_dependencies():
        sys.exit(1)
    
    setup_test_environment()
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    success = True
    
    try:
        if args.report:
            success = generate_test_report()
        elif args.unit:
            result = run_unit_tests(args.verbose)
            success = result.returncode == 0
        elif args.integration:
            result = run_integration_tests(args.verbose)
            success = result.returncode == 0
        elif args.e2e:
            result = run_e2e_tests(args.verbose)
            success = result.returncode == 0
        elif args.marker:
            result = run_tests_by_marker(args.marker, args.verbose)
            success = result.returncode == 0
        elif args.file:
            result = run_specific_test(args.file, args.verbose)
            success = result.returncode == 0
        elif args.all:
            result = run_all_tests(args.verbose, args.coverage)
            success = result.returncode == 0
        else:
            # Default: run all tests
            result = run_all_tests(args.verbose, args.coverage)
            success = result.returncode == 0
    
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        success = False
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        success = False
    
    # Summary
    print("\n" + "="*60)
    if success:
        print("🎉 TEST EXECUTION COMPLETED SUCCESSFULLY!")
    else:
        print("💥 TEST EXECUTION FAILED!")
    print("="*60)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()