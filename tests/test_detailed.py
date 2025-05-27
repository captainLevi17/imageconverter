"""Detailed test file with more output."""
import sys
import pytest
from PyQt5.QtWidgets import QApplication

def test_qt_app():
    """Test that a Qt application can be created."""
    app = QApplication.instance() or QApplication(sys.argv)
    assert app is not None
    print("Qt application created successfully")

def test_addition():
    """Test basic addition."""
    print("Running addition test")
    assert 1 + 1 == 2

class TestDetailed:
    """Detailed test class with setup and teardown."""
    
    def setup_method(self):
        """Setup method for each test."""
        print("Setting up test")
        self.app = QApplication.instance() or QApplication(sys.argv)
        
    def test_qt_available(self):
        """Test that Qt is available."""
        print("Testing Qt availability")
        assert QApplication.instance() is not None
        
    def teardown_method(self):
        """Teardown method for each test."""
        print("Tearing down test")
        if hasattr(self, 'app') and self.app:
            self.app.quit()

if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
