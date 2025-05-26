"""
Pytest configuration and fixtures for Image Master tests.
"""
import os
import shutil
import tempfile
from pathlib import Path

import pytest
from PyQt5.QtWidgets import QApplication

# Initialize QApplication once for all tests
app = QApplication.instance()
if app is None:
    app = QApplication([])

@pytest.fixture(scope="session")
def test_data_dir():
    """Fixture to provide a directory with test images."""
    # Create a temporary directory for test data
    test_dir = Path(tempfile.mkdtemp(prefix="image_master_test_"))
    
    # Create some test files (you can add more as needed)
    test_files = [
        "test.jpg",
        "test.png",
        "test.heic",
        "test.webp"
    ]
    
    for file in test_files:
        # Create empty files for testing
        (test_dir / file).touch()
    
    yield test_dir
    
    # Cleanup after tests
    shutil.rmtree(test_dir, ignore_errors=True)

@pytest.fixture
def temp_output_dir():
    """Fixture to provide a temporary output directory for tests."""
    temp_dir = Path(tempfile.mkdtemp(prefix="image_master_output_"))
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def qapp():
    """Fixture to provide QApplication instance."""
    return app
