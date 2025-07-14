# VCCTL Testing Suite

Comprehensive testing framework for the VCCTL (Virtual Cement and Concrete Testing Laboratory) application.

## Overview

This testing suite provides complete coverage for the VCCTL GTK3 desktop application, including:

- **Unit Tests**: Individual component testing with >80% coverage
- **Integration Tests**: Component interaction testing, especially UI components
- **End-to-End Tests**: Complete workflow testing from material definition to simulation
- **Performance Tests**: Benchmarking and performance regression testing
- **Database Tests**: Migration testing and data integrity validation

## Test Structure

```
tests/
├── conftest.py                 # Global test configuration and fixtures
├── unit/                       # Unit tests
│   ├── test_cement_service.py
│   ├── test_file_operations_service.py
│   ├── test_data_models.py
│   └── test_database_migrations.py
├── integration/                # Integration tests
│   └── test_ui_components.py
├── e2e/                       # End-to-end tests
│   └── test_complete_workflows.py
├── performance/               # Performance benchmarks
│   └── test_benchmarks.py
└── fixtures/                  # Test data and utilities
```

## Running Tests

Use the provided test runner for different test suites:

```bash
# Run all tests
python run_tests.py all

# Run specific test suites
python run_tests.py unit
python run_tests.py integration
python run_tests.py e2e
python run_tests.py performance

# Run quick tests (excludes slow tests)
python run_tests.py quick

# Run with coverage reporting
python run_tests.py all --coverage

# Setup test environment
python run_tests.py unit --setup

# Code quality checks
python run_tests.py quality

# Clean up test artifacts
python run_tests.py all --cleanup
```

## Test Categories

### Unit Tests

- **Service Layer**: Tests for all service classes (cement, aggregate, file operations, etc.)
- **Data Models**: Validation tests for Pydantic models
- **Database**: Migration and schema testing
- **Utilities**: File operations, error handling, performance monitoring

### Integration Tests

- **UI Components**: GTK widget integration and interaction testing
- **UI Polish System**: Theme management, accessibility, keyboard shortcuts, responsive layout
- **Service Integration**: Inter-service communication and coordination
- **Database Integration**: Service-database interaction patterns

### End-to-End Tests

- **Complete Workflows**: Material creation → Mix design → Simulation → Export
- **Import/Export**: Full material import/export cycles
- **Project Management**: Save/load project workflows
- **Batch Processing**: Multi-material processing workflows
- **Error Recovery**: Error handling and recovery scenarios

### Performance Tests

- **Database Operations**: CRUD performance benchmarks
- **File Operations**: Import/export and file processing performance
- **UI Responsiveness**: GTK interface performance with large datasets
- **Memory Usage**: Memory leak detection and usage optimization
- **Concurrent Operations**: Thread safety and parallel processing

## Test Fixtures

### Global Fixtures (conftest.py)

- `gtk_test_environment`: GTK testing setup with offscreen rendering
- `temp_directory`: Isolated temporary directory for each test
- `test_database`: In-memory SQLite database for testing
- `test_config`: Test configuration manager
- `mock_service_container`: Mock service container with test services
- `sample_cement_data`: Standard cement material data
- `sample_aggregate_data`: Standard aggregate material data
- `sample_mix_design_data`: Standard mix design data
- `performance_timer`: Performance measurement utility

### Custom Assertions

- `assert_valid_cement_composition()`: Validates cement oxide composition totals ~100%
- `assert_valid_mix_design()`: Validates mix design proportions and limits
- `assert_file_exists_and_valid()`: Validates file existence and minimum size

### Performance Benchmarks

- `PerformanceBenchmarks.MAX_DATABASE_QUERY_TIME`: 100ms
- `PerformanceBenchmarks.MAX_UI_RESPONSE_TIME`: 50ms
- `PerformanceBenchmarks.MAX_FILE_OPERATION_TIME`: 1s
- `PerformanceBenchmarks.MAX_CALCULATION_TIME`: 5s

## Test Markers

Use pytest markers to run specific test categories:

```bash
# Run only unit tests
pytest -m unit

# Run only GUI tests (requires display)
pytest -m gui

# Run only performance tests
pytest -m performance

# Exclude slow tests
pytest -m "not slow"

# Run only database tests
pytest -m database

# Run only filesystem tests
pytest -m filesystem
```

Available markers:
- `unit`: Unit tests for individual components
- `integration`: Integration tests for component interactions
- `e2e`: End-to-end tests for complete workflows
- `performance`: Performance and benchmark tests
- `slow`: Tests that take longer than 5 seconds
- `gui`: Tests that require GTK/GUI environment
- `database`: Tests that require database connection
- `filesystem`: Tests that interact with filesystem
- `external`: Tests that require external dependencies

## Coverage Requirements

- **Minimum Coverage**: 80% overall
- **Service Classes**: >90% coverage required
- **UI Components**: >70% coverage (GTK testing limitations)
- **Data Models**: >95% coverage required
- **Critical Paths**: 100% coverage required

## Continuous Integration

The testing suite is designed for CI/CD integration:

### GitHub Actions Example

```yaml
name: VCCTL Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y libgirepository1.0-dev pkg-config
    
    - name: Setup test environment
      run: python run_tests.py unit --setup
    
    - name: Run quick tests
      run: python run_tests.py quick --coverage
    
    - name: Run code quality checks
      run: python run_tests.py quality
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

## Mock Objects and Test Doubles

The testing suite makes extensive use of mocking for:

- **External Dependencies**: Database connections, file systems, network calls
- **GTK Components**: UI widgets and event handling
- **Service Layer**: Inter-service communication
- **Heavy Operations**: Long-running simulations and calculations

### Key Mock Patterns

```python
# Service mocking
with patch.object(service, 'external_dependency') as mock_dep:
    mock_dep.return_value = expected_value
    result = service.method_under_test()

# GTK widget mocking
mock_widget = Mock(spec=Gtk.Widget)
mock_widget.get_style_context.return_value = Mock()

# Database session mocking
with patch.object(db_service, 'get_session') as mock_session:
    mock_session.return_value.__enter__.return_value = Mock()
```

## Test Data Management

### Sample Data Generation

The test suite includes generators for creating realistic test data:

```python
# Generate multiple cement variations
for cement_data in generate_test_cement_data(variations=10):
    test_cement_creation(cement_data)

# Generate parametric study data
for sio2 in range(18, 23):
    for cao in range(60, 70):
        test_parametric_variation(sio2=sio2, cao=cao)
```

### Data Validation

All test data follows the same validation rules as production data:

- Cement compositions must total ~100%
- Physical properties must be within realistic ranges
- Mix designs must follow concrete technology constraints
- File formats must match specification requirements

## Debugging Tests

### Common Issues

1. **GTK Display Issues**: Use `DISPLAY=:99` for headless testing
2. **Database Locks**: Ensure proper session cleanup in fixtures
3. **File Permissions**: Use temp directories with proper permissions
4. **Memory Leaks**: Monitor memory usage in performance tests

### Debug Helpers

```python
# Enable debug logging
import logging
logging.getLogger('VCCTL').setLevel(logging.DEBUG)

# Performance profiling
from tests.conftest import PerformanceTimer
timer = PerformanceTimer()
timer.start()
# ... test code ...
elapsed = timer.stop()
print(f"Operation took {elapsed:.3f}s")

# Memory monitoring
import psutil
process = psutil.Process()
print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.1f}MB")
```

## Contributing to Tests

When adding new features:

1. **Add Unit Tests**: Test individual methods and classes
2. **Add Integration Tests**: Test component interactions
3. **Update Fixtures**: Add new sample data as needed
4. **Document Test Cases**: Include docstrings explaining test purpose
5. **Check Coverage**: Ensure new code meets coverage requirements

### Test Writing Guidelines

- Use descriptive test method names: `test_cement_creation_with_invalid_composition`
- Include both positive and negative test cases
- Mock external dependencies but test real business logic
- Use parametrized tests for multiple similar scenarios
- Clean up resources in test teardown
- Follow the Arrange-Act-Assert pattern

### Example Test Structure

```python
@pytest.mark.unit
def test_cement_service_create_with_valid_data(self, test_database, sample_cement_data):
    """Test successful cement creation with valid composition data."""
    # Arrange
    service = CementService(test_database)
    cement_create = CementCreate(**sample_cement_data)
    
    # Act
    with patch.object(service, '_validate_cement'):
        result = service.create(cement_create)
    
    # Assert
    assert result is not None
    assert result.name == sample_cement_data['name']
```

## Test Metrics and Reporting

The testing suite generates comprehensive reports:

- **Coverage Reports**: HTML and XML formats
- **Performance Benchmarks**: JSON benchmark data
- **Test Results**: JUnit XML for CI integration
- **Code Quality**: Flake8, mypy, and black reports

Reports are generated in:
- `htmlcov/`: Coverage reports
- `benchmark_results/`: Performance benchmark data
- `test_reports/`: JUnit XML results
- `quality_reports/`: Code quality reports

## Maintenance

### Regular Maintenance Tasks

1. **Update Test Data**: Keep sample data current with schema changes
2. **Review Performance Benchmarks**: Update performance expectations
3. **Clean Test Environment**: Remove outdated fixtures and mocks
4. **Update Dependencies**: Keep testing libraries current
5. **Review Coverage**: Identify and test uncovered code paths

### Performance Monitoring

The test suite includes performance regression detection:

- Database operation timing
- File operation benchmarks
- UI responsiveness metrics
- Memory usage tracking
- Concurrent operation performance

Failing performance tests indicate potential regressions that need investigation.