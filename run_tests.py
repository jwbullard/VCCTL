#!/usr/bin/env python3
"""
VCCTL Test Runner

Comprehensive test runner for VCCTL application with different test suites,
coverage reporting, and performance benchmarking.
"""

import sys
import subprocess
import argparse
from pathlib import Path
import time
from typing import List, Dict, Any


class VCCTLTestRunner:
    """Test runner for VCCTL application."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.src_dir = self.project_root / "src"
        self.tests_dir = self.src_dir / "tests"
        
    def run_unit_tests(self, verbose: bool = False) -> bool:
        """Run unit tests."""
        print("🧪 Running Unit Tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir / "unit"),
            "-m", "unit",
            "--cov=src/app",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov/unit",
            "--cov-report=xml:coverage-unit.xml"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd)
    
    def run_integration_tests(self, verbose: bool = False) -> bool:
        """Run integration tests."""
        print("🔗 Running Integration Tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir / "integration"),
            "-m", "integration",
            "--cov=src/app",
            "--cov-report=term-missing", 
            "--cov-report=html:htmlcov/integration",
            "--cov-report=xml:coverage-integration.xml"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd)
    
    def run_e2e_tests(self, verbose: bool = False) -> bool:
        """Run end-to-end tests."""
        print("🎯 Running End-to-End Tests...")
        
        cmd = [
            sys.executable, "-m", "pytest", 
            str(self.tests_dir / "e2e"),
            "-m", "e2e",
            "--cov=src/app",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov/e2e", 
            "--cov-report=xml:coverage-e2e.xml"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd)
    
    def run_performance_tests(self, verbose: bool = False) -> bool:
        """Run performance benchmarks."""
        print("⚡ Running Performance Tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir / "performance"), 
            "-m", "performance",
            "--cov=src/app",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov/performance"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd)
    
    def run_gui_tests(self, verbose: bool = False) -> bool:
        """Run GUI tests (requires display)."""
        print("🖥️  Running GUI Tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir),
            "-m", "gui",
            "--cov=src/app/ui",
            "--cov=src/app/windows",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov/gui",
            "--cov-report=xml:coverage-gui.xml"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd)
    
    def run_all_tests(self, verbose: bool = False) -> bool:
        """Run all test suites."""
        print("🚀 Running All Tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir),
            "--cov=src/app", 
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov/all",
            "--cov-report=xml:coverage-all.xml",
            "--cov-fail-under=80"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd)
    
    def run_quick_tests(self, verbose: bool = False) -> bool:
        """Run quick test suite (excludes slow tests)."""
        print("⚡ Running Quick Tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir),
            "-m", "not slow and not e2e and not performance",
            "--cov=src/app",
            "--cov-report=term-missing"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd)
    
    def run_database_tests(self, verbose: bool = False) -> bool:
        """Run database-related tests."""
        print("💾 Running Database Tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir),
            "-m", "database",
            "--cov=src/app/database",
            "--cov=src/app/models", 
            "--cov=src/app/services",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov/database"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd)
    
    def run_filesystem_tests(self, verbose: bool = False) -> bool:
        """Run filesystem-related tests."""
        print("📁 Running Filesystem Tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir),
            "-m", "filesystem",
            "--cov=src/app/utils/file_operations",
            "--cov=src/app/services/file_operations_service",
            "--cov-report=term-missing"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd)
    
    def run_compatibility_tests(self, verbose: bool = False) -> bool:
        """Run cross-platform compatibility tests."""
        print("🌐 Running Cross-Platform Compatibility Tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir / "test_cross_platform_compatibility.py"),
            "-m", "compatibility",
            "--cov=src/app",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov/compatibility"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd)
    
    def run_comprehensive_tests(self, verbose: bool = False) -> bool:
        """Run all comprehensive test suites (VCCTL-024)."""
        print("🎯 Running Comprehensive Test Suite (VCCTL-024)...")
        
        all_passed = True
        
        # Run unit tests with comprehensive coverage
        print("\n📋 Phase 1: Comprehensive Unit Tests...")
        if not self.run_unit_tests(verbose):
            all_passed = False
        
        # Run integration tests
        print("\n📋 Phase 2: UI Component Integration Tests...")
        if not self.run_integration_tests(verbose):
            all_passed = False
        
        # Run end-to-end tests
        print("\n📋 Phase 3: End-to-End Workflow Tests...")
        if not self.run_e2e_tests(verbose):
            all_passed = False
        
        # Run performance benchmarks
        print("\n📋 Phase 4: Performance Benchmarks...")
        if not self.run_performance_tests(verbose):
            all_passed = False
        
        # Run compatibility tests
        print("\n📋 Phase 5: Cross-Platform Compatibility Tests...")
        if not self.run_compatibility_tests(verbose):
            all_passed = False
        
        print(f"\n{'✅' if all_passed else '❌'} Comprehensive Test Suite {'Completed Successfully' if all_passed else 'Failed'}")
        return all_passed
    
    def check_code_quality(self) -> bool:
        """Run code quality checks."""
        print("🔍 Running Code Quality Checks...")
        
        success = True
        
        # Run flake8
        print("  📏 Running flake8...")
        flake8_cmd = [sys.executable, "-m", "flake8", str(self.src_dir)]
        if not self._run_command(flake8_cmd, capture_output=True):
            print("    ❌ flake8 found issues")
            success = False
        else:
            print("    ✅ flake8 passed")
        
        # Run mypy
        print("  🏷️  Running mypy...")
        mypy_cmd = [sys.executable, "-m", "mypy", str(self.src_dir)]
        if not self._run_command(mypy_cmd, capture_output=True):
            print("    ❌ mypy found issues") 
            success = False
        else:
            print("    ✅ mypy passed")
        
        # Run black check
        print("  🎨 Running black check...")
        black_cmd = [sys.executable, "-m", "black", "--check", str(self.src_dir)]
        if not self._run_command(black_cmd, capture_output=True):
            print("    ❌ black formatting issues found")
            success = False
        else:
            print("    ✅ black formatting passed")
        
        return success
    
    def format_code(self) -> bool:
        """Format code with black."""
        print("🎨 Formatting code with black...")
        
        cmd = [sys.executable, "-m", "black", str(self.src_dir)]
        return self._run_command(cmd)
    
    def generate_coverage_report(self) -> None:
        """Generate comprehensive coverage report."""
        print("📊 Generating Coverage Report...")
        
        # Combine coverage data
        subprocess.run([
            sys.executable, "-m", "coverage", "combine"
        ], cwd=self.project_root)
        
        # Generate HTML report
        subprocess.run([
            sys.executable, "-m", "coverage", "html",
            "--directory=htmlcov/combined"
        ], cwd=self.project_root)
        
        # Generate XML report 
        subprocess.run([
            sys.executable, "-m", "coverage", "xml",
            "--output=coverage-combined.xml"
        ], cwd=self.project_root)
        
        # Print summary
        subprocess.run([
            sys.executable, "-m", "coverage", "report"
        ], cwd=self.project_root)
        
        print(f"📊 Coverage reports generated in {self.project_root / 'htmlcov'}")
    
    def setup_test_environment(self) -> bool:
        """Setup test environment."""
        print("🔧 Setting up test environment...")
        
        # Install test dependencies
        cmd = [
            sys.executable, "-m", "pip", "install", "-r", 
            str(self.project_root / "requirements.txt")
        ]
        
        return self._run_command(cmd)
    
    def cleanup_test_artifacts(self) -> None:
        """Clean up test artifacts."""
        print("🧹 Cleaning up test artifacts...")
        
        import shutil
        
        # Remove coverage files
        coverage_files = [
            ".coverage",
            "coverage-*.xml",
            "htmlcov"
        ]
        
        for pattern in coverage_files:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
        
        # Remove pytest cache
        pytest_cache = self.project_root / ".pytest_cache"
        if pytest_cache.exists():
            shutil.rmtree(pytest_cache)
        
        print("✅ Test artifacts cleaned up")
    
    def _run_command(self, cmd: List[str], capture_output: bool = False) -> bool:
        """Run command and return success status."""
        try:
            if capture_output:
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
                return result.returncode == 0
            else:
                result = subprocess.run(cmd, cwd=self.project_root)
                return result.returncode == 0
        except Exception as e:
            print(f"Error running command {' '.join(cmd)}: {e}")
            return False


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="VCCTL Test Runner")
    parser.add_argument(
        "suite",
        choices=[
            "unit", "integration", "e2e", "performance", "gui", "compatibility",
            "all", "quick", "database", "filesystem", "comprehensive", "quality", "format"
        ],
        help="Test suite to run"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--setup", action="store_true", help="Setup test environment")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup test artifacts")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    
    args = parser.parse_args()
    
    runner = VCCTLTestRunner()
    
    # Setup if requested
    if args.setup:
        if not runner.setup_test_environment():
            print("❌ Failed to setup test environment")
            return 1
    
    # Cleanup if requested
    if args.cleanup:
        runner.cleanup_test_artifacts()
        return 0
    
    # Run tests
    start_time = time.time()
    success = False
    
    if args.suite == "unit":
        success = runner.run_unit_tests(args.verbose)
    elif args.suite == "integration":
        success = runner.run_integration_tests(args.verbose)
    elif args.suite == "e2e":
        success = runner.run_e2e_tests(args.verbose)
    elif args.suite == "performance":
        success = runner.run_performance_tests(args.verbose)
    elif args.suite == "gui":
        success = runner.run_gui_tests(args.verbose)
    elif args.suite == "all":
        success = runner.run_all_tests(args.verbose)
    elif args.suite == "quick":
        success = runner.run_quick_tests(args.verbose)
    elif args.suite == "database":
        success = runner.run_database_tests(args.verbose)
    elif args.suite == "filesystem":
        success = runner.run_filesystem_tests(args.verbose)
    elif args.suite == "compatibility":
        success = runner.run_compatibility_tests(args.verbose)
    elif args.suite == "comprehensive":
        success = runner.run_comprehensive_tests(args.verbose)
    elif args.suite == "quality":
        success = runner.check_code_quality()
    elif args.suite == "format":
        success = runner.format_code()
    
    elapsed_time = time.time() - start_time
    
    # Generate coverage report if requested
    if args.coverage and args.suite != "quality" and args.suite != "format":
        runner.generate_coverage_report()
    
    # Print summary
    print("\n" + "="*50)
    if success:
        print(f"✅ {args.suite.title()} tests completed successfully in {elapsed_time:.2f}s")
        return 0
    else:
        print(f"❌ {args.suite.title()} tests failed after {elapsed_time:.2f}s")
        return 1


if __name__ == "__main__":
    sys.exit(main())