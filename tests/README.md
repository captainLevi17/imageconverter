# Testing Image Master

This directory contains the test suite for the Image Master application.

## Running Tests

### Prerequisites

1. Install the test dependencies:
   ```bash
   pip install -r ../requirements.txt
   ```

2. For GUI testing on Linux, you may need to install xvfb:
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install xvfb
   ```

### Running All Tests

To run all tests with coverage report:

```bash
pytest -v --cov=imageconverter --cov-report=term-missing
```

### Running Specific Tests

Run a specific test file:
```bash
pytest tests/test_image_utils.py -v
```

Run a specific test class:
```bash
pytest tests/test_image_utils.py::TestImageUtils -v
```

Run a specific test method:
```bash
pytest tests/test_image_utils.py::TestImageUtils::test_resize_image -v
```

### Running Tests with Different Options

Run tests without capturing output (useful for debugging):
```bash
pytest -v -s
```

Run tests in parallel (requires pytest-xdist):
```bash
pytest -n auto
```

### Coverage Reports

Generate an HTML coverage report:
```bash
pytest --cov=imageconverter --cov-report=html
```

Then open `htmlcov/index.html` in a web browser.

## Writing Tests

When adding new tests:

1. Create a new test file named `test_*.py`
2. Follow the existing test patterns
3. Use fixtures from `conftest.py` when possible
4. Keep tests focused and independent
5. Mock external dependencies when necessary

## Test Organization

- `test_image_utils.py`: Tests for image processing utilities
- `test_gui_components.py`: Tests for GUI components
- `conftest.py`: Pytest configuration and fixtures

## Continuous Integration

The test suite is designed to run in CI environments. See `.github/workflows/tests.yml` for the CI configuration.
