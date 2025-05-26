"""
Theme module for Image Master application.
Based on the New Age Bootstrap theme.
"""
from PyQt5.QtGui import QColor

def get_theme_stylesheet():
    """
    Return the CSS stylesheet for the New Age theme.
    """
    return """
    /* Main application styling */
    QMainWindow, QDialog, QWidget {
        background-color: #ffffff;
        color: #2d3748;
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }

    /* Text styles */
    QLabel {
        color: #2d3748;
        font-size: 14px;
    }

    QLabel#titleLabel {
        font-size: 24px;
        font-weight: bold;
        color: #2937f0;  /* Primary blue from theme */
    }

    QLabel#subtitleLabel {
        font-size: 16px;
        color: #6c757d;
    }

    /* Buttons */
    QPushButton {
        background-color: #2937f0;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        font-weight: 500;
        min-width: 80px;
    }

    QPushButton:hover {
        background-color: #212cc0;
    }

    QPushButton:pressed {
        background-color: #1a2499;
    }

    QPushButton:disabled {
        background-color: #e2e8f0;
        color: #a0aec0;
    }

    /* Tabs */
    QTabWidget::pane {
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        margin-top: 10px;
    }

    QTabBar::tab {
        background: #f8f9fa;
        color: #4a5568;
        padding: 8px 16px;
        margin-right: 4px;
        border: 1px solid #e2e8f0;
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }

    QTabBar::tab:selected {
        background: white;
        color: #2937f0;
        border-bottom: 2px solid #2937f0;
        margin-bottom: -1px;
    }

    QTabBar::tab:!selected {
        margin-top: 4px;
    }

    /* Input fields */
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
        padding: 8px 12px;
        border: 1px solid #d1d9e6;
        border-radius: 6px;
        min-height: 36px;
    }

    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
        border: 1px solid #2937f0;
        outline: none;
    }

    /* Group boxes */
    QGroupBox {
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        margin-top: 20px;
        padding-top: 30px;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 15px;
        padding: 0 5px;
        color: #4a5568;
    }

    /* Scroll bars */
    QScrollBar:vertical {
        border: none;
        background: #f8f9fa;
        width: 10px;
        margin: 0px;
    }

    QScrollBar::handle:vertical {
        background: #cbd5e0;
        min-height: 20px;
        border-radius: 5px;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }

    /* Progress bar */
    QProgressBar {
        border: 1px solid #e2e8f0;
        border-radius: 3px;
        text-align: center;
    }

    QProgressBar::chunk {
        background-color: #2937f0;
        width: 10px;
    }

    /* Checkboxes and radio buttons */
    QCheckBox::indicator, QRadioButton::indicator {
        width: 16px;
        height: 16px;
    }

    QCheckBox::indicator:unchecked, QRadioButton::indicator:unchecked {
        border: 1px solid #cbd5e0;
        border-radius: 3px;
        background: white;
    }

    QCheckBox::indicator:checked {
        image: url(icons/check.svg);
        background: #2937f0;
        border: 1px solid #2937f0;
        border-radius: 3px;
    }

    QRadioButton::indicator:checked {
        border: 1px solid #2937f0;
        border-radius: 8px;
        background: white;
    }

    QRadioButton::indicator:checked {
        background: #2937f0;
    }

    /* Tooltips */
    QToolTip {
        background-color: #2d3748;
        color: white;
        border: 1px solid #4a5568;
        padding: 5px;
        border-radius: 3px;
    }

    /* Status bar */
    QStatusBar {
        background-color: #f8f9fa;
        color: #4a5568;
        border-top: 1px solid #e2e8f0;
    }

    /* Base64 Tool specific styles */
    QWidget#base64ToolWidget {
        background: transparent;
    }
    
    QLabel[preview=true] {
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        background: #f8fafc;
        min-height: 100px;
        min-width: 200px;
        qproperty-alignment: AlignCenter;
        color: #a0aec0;
        font-style: italic;
    }
    
    QTextEdit#base64Output, QTextEdit#base64Input {
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 12px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px;
    }
    
    QFrame#pathFrame {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px 12px;
    }
    
    QLabel#imgPathLabel {
        color: #4a5568;
    }
    
    QLabel#formatLabel {
        color: #4a5568;
    }
    
    QComboBox#formatCombo {
        min-width: 150px;
    }
    
    QFrame#separator {
        color: #e2e8f0;
    }
    
    /* Menu bar */
    QMenuBar {
        background-color: white;
        color: #4a5568;
        padding: 4px;
        border-bottom: 1px solid #e2e8f0;
    }

    QMenuBar::item {
        padding: 4px 8px;
        background: transparent;
    }

    QMenuBar::item:selected {
        background: #edf2f7;
        border-radius: 4px;
    }

    QMenu {
        background-color: white;
        border: 1px solid #e2e8f0;
        padding: 4px;
    }

    QMenu::item {
        padding: 6px 24px 6px 16px;
    }

    QMenu::item:selected {
        background-color: #edf2f7;
        color: #2937f0;
    }

    QMenu::separator {
        height: 1px;
        background: #e2e8f0;
        margin: 4px 0;
    }
    """

def apply_theme(app):
    """
    Apply the New Age theme to the application.
    
    Args:
        app: The QApplication instance
    """
    # Set application style to Fusion for better theming support
    app.setStyle('Fusion')
    
    # Apply the stylesheet
    app.setStyleSheet(get_theme_stylesheet())
    
    # Set application font
    font = app.font()
    font.setPointSize(9)
    app.setFont(font)
    
    # Set application palette with theme colors
    palette = app.palette()
    
    # Base colors
    palette.setColor(palette.Window, QColor(255, 255, 255))
    palette.setColor(palette.WindowText, QColor(45, 55, 72))  # gray.800
    palette.setColor(palette.Base, QColor(255, 255, 255))
    palette.setColor(palette.AlternateBase, QColor(248, 250, 252))  # gray.50
    palette.setColor(palette.ToolTipBase, QColor(45, 55, 72))  # gray.800
    palette.setColor(palette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(palette.Text, QColor(45, 55, 72))  # gray.800
    palette.setColor(palette.Button, QColor(255, 255, 255))
    palette.setColor(palette.ButtonText, QColor(41, 55, 240))  # primary
    palette.setColor(palette.BrightText, QColor(255, 255, 255))
    palette.setColor(palette.Link, QColor(41, 55, 240))  # primary
    palette.setColor(palette.Highlight, QColor(41, 55, 240))  # primary
    palette.setColor(palette.HighlightedText, QColor(255, 255, 255))
    
    # Disabled colors
    palette.setColor(palette.Disabled, palette.WindowText, QColor(160, 174, 192))  # gray.400
    palette.setColor(palette.Disabled, palette.Text, QColor(160, 174, 192))  # gray.400
    palette.setColor(palette.Disabled, palette.ButtonText, QColor(160, 174, 192))  # gray.400
    
    app.setPalette(palette)
