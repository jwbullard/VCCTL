#!/usr/bin/env python3
"""
VCCTL Integration Test Runner

Runs comprehensive end-to-end integration tests to verify
all components work together properly.
"""

import sys
import logging
import argparse
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from app.utils.integration_tests import run_integration_tests


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('vcctl_integration_tests.log', mode='w')
        ]
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run VCCTL end-to-end integration tests"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("test_results"),
        help="Directory to save test results (default: test_results)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--no-performance",
        action="store_true",
        help="Skip performance tests"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    logger = logging.getLogger('VCCTL.TestRunner')
    logger.info("Starting VCCTL integration tests")
    
    try:
        # Run integration tests
        results = run_integration_tests(args.output_dir)
        
        # Print summary
        total_tests = results['total_tests']
        passed_tests = results['passed']
        failed_tests = results['failed']
        success_rate = results['success_rate']
        
        print("\n" + "=" * 60)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print("=" * 60)
        
        if failed_tests > 0:
            print("\nFAILED TESTS:")
            for suite in results['suites']:
                for test in suite['tests']:
                    if test['status'] == 'failed':
                        print(f"  ✗ {suite['name']}: {test['name']}")
                        if test['error']:
                            print(f"    Error: {test['error']}")
        
        # Print recommendations based on results
        print("\nRECOMMENDATIONS:")
        
        if success_rate >= 95:
            print("  ✓ Excellent! All components are well integrated.")
        elif success_rate >= 80:
            print("  ⚠ Good integration with minor issues to address.")
        elif success_rate >= 60:
            print("  ⚠ Moderate integration issues need attention.")
        else:
            print("  ✗ Significant integration problems require immediate attention.")
        
        # Performance recommendations
        perf_metrics = results.get('performance_metrics', {})
        if 'service_response_times' in perf_metrics:
            slow_services = {k: v for k, v in perf_metrics['service_response_times'].items() if v > 1.0}
            if slow_services:
                print(f"  ⚠ Slow services detected: {list(slow_services.keys())}")
        
        if 'memory_usage' in perf_metrics and perf_metrics['memory_usage']:
            latest_memory = perf_metrics['memory_usage'][-1]['memory_mb']
            if latest_memory > 200:
                print(f"  ⚠ High memory usage: {latest_memory:.1f} MB")
        
        print(f"\nDetailed results saved to: {args.output_dir}")
        
        # Exit with appropriate code
        sys.exit(0 if failed_tests == 0 else 1)
        
    except Exception as e:
        logger.error(f"Integration test runner failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(2)


if __name__ == "__main__":
    main()