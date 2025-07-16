"""
Motor control widget for dynamometer interface.
Handles drive and brake motor control inputs.
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, 
                             QLabel, QPushButton, QLineEdit, QCheckBox, QGridLayout)
from PyQt5.QtCore import pyqtSignal, Qt


class ControlWidget(QWidget):
    """Widget for motor control inputs."""
    
    drive_speed_requested = pyqtSignal(int)  # rpm
    brake_load_requested = pyqtSignal(float)  # current
    drive_enable_requested = pyqtSignal(bool)  # enabled
    brake_enable_requested = pyqtSignal(bool)  # enabled
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Create the control UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create group box
        group_box = QGroupBox("Dynamometer Control")
        main_layout.addWidget(group_box)
        
        # Group box layout
        group_layout = QHBoxLayout(group_box)
        
        # Drive motor controls
        drive_group = QGroupBox("Drive Motor (Spinning)")
        drive_layout = QGridLayout(drive_group)
        
        drive_layout.addWidget(QLabel("Target RPM:"), 0, 0)
        self.target_rpm_input = QLineEdit("0")
        self.target_rpm_input.setMaximumWidth(100)
        drive_layout.addWidget(self.target_rpm_input, 0, 1)
        
        self.set_speed_button = QPushButton("Set Speed")
        self.set_speed_button.clicked.connect(self._on_set_speed_clicked)
        drive_layout.addWidget(self.set_speed_button, 0, 2)
        
        self.drive_enabled_checkbox = QCheckBox("Enable Drive")
        self.drive_enabled_checkbox.stateChanged.connect(self._on_drive_enable_changed)
        drive_layout.addWidget(self.drive_enabled_checkbox, 1, 0, 1, 3)
        
        group_layout.addWidget(drive_group)
        
        # Brake motor controls
        brake_group = QGroupBox("Brake Motor (Load)")
        brake_layout = QGridLayout(brake_group)
        
        brake_layout.addWidget(QLabel("Load Current (A):"), 0, 0)
        self.target_load_input = QLineEdit("0")
        self.target_load_input.setMaximumWidth(100)
        brake_layout.addWidget(self.target_load_input, 0, 1)
        
        self.set_load_button = QPushButton("Set Load")
        self.set_load_button.clicked.connect(self._on_set_load_clicked)
        brake_layout.addWidget(self.set_load_button, 0, 2)
        
        self.brake_enabled_checkbox = QCheckBox("Enable Brake")
        self.brake_enabled_checkbox.stateChanged.connect(self._on_brake_enable_changed)
        brake_layout.addWidget(self.brake_enabled_checkbox, 1, 0, 1, 3)
        
        group_layout.addWidget(brake_group)
        
    def _on_set_speed_clicked(self):
        """Handle set speed button click."""
        try:
            rpm = int(self.target_rpm_input.text())
            self.drive_speed_requested.emit(rpm)
        except ValueError:
            # Handle invalid input - could emit error signal
            pass
            
    def _on_set_load_clicked(self):
        """Handle set load button click."""
        try:
            current = float(self.target_load_input.text())
            self.brake_load_requested.emit(current)
        except ValueError:
            # Handle invalid input - could emit error signal
            pass
            
    def _on_drive_enable_changed(self, state):
        """Handle drive enable checkbox change."""
        enabled = state == Qt.Checked
        self.drive_enable_requested.emit(enabled)
        
    def _on_brake_enable_changed(self, state):
        """Handle brake enable checkbox change."""
        enabled = state == Qt.Checked
        self.brake_enable_requested.emit(enabled)
        
    def update_drive_enabled(self, enabled):
        """Update drive enable checkbox."""
        self.drive_enabled_checkbox.setChecked(enabled)
        
    def update_brake_enabled(self, enabled):
        """Update brake enable checkbox."""
        self.brake_enabled_checkbox.setChecked(enabled)
        
    def get_target_rpm(self):
        """Get target RPM value."""
        try:
            return int(self.target_rpm_input.text())
        except ValueError:
            return 0
            
    def get_target_load(self):
        """Get target load value."""
        try:
            return float(self.target_load_input.text())
        except ValueError:
            return 0.0
            
    def set_target_rpm(self, rpm):
        """Set target RPM value."""
        self.target_rpm_input.setText(str(rpm))
        
    def set_target_load(self, load):
        """Set target load value."""
        self.target_load_input.setText(str(load))
        
    def set_enabled(self, enabled):
        """Enable/disable control inputs."""
        self.target_rpm_input.setEnabled(enabled)
        self.target_load_input.setEnabled(enabled)
        self.set_speed_button.setEnabled(enabled)
        self.set_load_button.setEnabled(enabled)
        self.drive_enabled_checkbox.setEnabled(enabled)
        self.brake_enabled_checkbox.setEnabled(enabled)