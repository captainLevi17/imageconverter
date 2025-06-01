"""
Dimension controls widget for resizing operations.
"""
from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QSpinBox, 
    QLabel, QCheckBox, QComboBox, QWidget
)
from PyQt5.QtCore import pyqtSignal, Qt

class DimensionControls(QGroupBox):
    """Widget for controlling image dimensions with presets."""
    
    # Signal emitted when any dimension control changes
    dimensions_changed = pyqtSignal()
    
    def __init__(self, presets: dict, parent=None):
        """Initialize the dimension controls.
        
        Args:
            presets: Dictionary of preset names to (width, height) tuples
            parent: Parent widget
        """
        super().__init__("Dimensions", parent)
        self.presets = presets
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout()
        
        # Preset selection
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(self.presets.keys())
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        layout.addWidget(self.preset_combo)
        
        # Width and height controls
        dim_layout = QHBoxLayout()
        
        # Width control
        width_widget = QWidget()
        width_layout = QHBoxLayout()
        width_layout.setContentsMargins(0, 0, 0, 0)
        width_label = QLabel("Width:")
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 9999)
        self.width_spin.setValue(800)
        self.width_spin.setSuffix(" px")
        self.width_spin.setFixedWidth(100)
        self.width_spin.valueChanged.connect(self._on_dimension_changed)
        width_layout.addWidget(width_label)
        width_layout.addWidget(self.width_spin)
        width_widget.setLayout(width_layout)
        
        # Height control
        height_widget = QWidget()
        height_layout = QHBoxLayout()
        height_layout.setContentsMargins(0, 0, 0, 0)
        height_label = QLabel("Height:")
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 9999)
        self.height_spin.setValue(600)
        self.height_spin.setSuffix(" px")
        self.height_spin.setFixedWidth(100)
        self.height_spin.valueChanged.connect(self._on_dimension_changed)
        height_layout.addWidget(height_label)
        height_layout.addWidget(self.height_spin)
        height_widget.setLayout(height_layout)
        
        dim_layout.addWidget(width_widget)
        dim_layout.addWidget(height_widget)
        dim_layout.addStretch()
        
        layout.addLayout(dim_layout)
        
        # Checkboxes
        self.aspect_ratio_check = QCheckBox("Maintain aspect ratio")
        self.aspect_ratio_check.setChecked(True)
        self.aspect_ratio_check.stateChanged.connect(self._on_dimension_changed)
        
        self.allow_enlarge = QCheckBox("Allow image enlargement")
        self.allow_enlarge.setChecked(False)
        self.allow_enlarge.stateChanged.connect(self._on_dimension_changed)
        
        layout.addWidget(self.aspect_ratio_check)
        layout.addWidget(self.allow_enlarge)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def get_dimensions(self) -> tuple[int, int]:
        """Get the current width and height values."""
        return self.width_spin.value(), self.height_spin.value()
    
    def set_dimensions(self, width: int, height: int):
        """Set the width and height values."""
        self.width_spin.blockSignals(True)
        self.height_spin.blockSignals(True)
        self.width_spin.setValue(width)
        self.height_spin.setValue(height)
        self.width_spin.blockSignals(False)
        self.height_spin.blockSignals(False)
    
    def _on_preset_changed(self, preset_name: str):
        """Handle preset selection changes."""
        if preset_name in self.presets:
            width, height = self.presets[preset_name]
            self.set_dimensions(width, height)
            self.dimensions_changed.emit()
    
    def _on_dimension_changed(self, _=None):
        """Handle dimension changes."""
        self.dimensions_changed.emit()
    
    @property
    def maintain_aspect_ratio(self) -> bool:
        """Check if aspect ratio should be maintained."""
        return self.aspect_ratio_check.isChecked()
    
    @property
    def allow_image_enlarge(self) -> bool:
        """Check if image enlargement is allowed."""
        return self.allow_enlarge.isChecked()
