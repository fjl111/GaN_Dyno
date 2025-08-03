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
    
    # Step sizes for increment/decrement buttons
    RPM_STEP = 100  # RPM increment/decrement step
    CURRENT_STEP = 0.1  # Current increment/decrement step (Amps)
    
    # Limits
    MAX_RPM = 10000
    MIN_RPM = 0
    MAX_CURRENT = 50.0  # Amps
    MIN_CURRENT = 0.0
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Create the control UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create group box with reduced height
        group_box = QGroupBox("Dynamometer Control")
        group_box.setMaximumHeight(80)
        main_layout.addWidget(group_box)
        
        # Group box layout
        group_layout = QHBoxLayout(group_box)
        group_layout.setSpacing(15)
        group_layout.setContentsMargins(8, 8, 8, 8)
        
        # Drive motor controls - compact inline layout
        drive_layout = QHBoxLayout()
        drive_layout.addWidget(QLabel("RPM:"))
        
        self.target_rpm_input = QLineEdit("0")
        self.target_rpm_input.setMaximumWidth(100)
        drive_layout.addWidget(self.target_rpm_input)
        
        # RPM up/down buttons
        self.rpm_down_button = QPushButton("-")
        self.rpm_down_button.setMaximumWidth(25)
        self.rpm_down_button.clicked.connect(self._on_rpm_down_clicked)
        drive_layout.addWidget(self.rpm_down_button)
        
        self.rpm_up_button = QPushButton("+")
        self.rpm_up_button.setMaximumWidth(25)
        self.rpm_up_button.clicked.connect(self._on_rpm_up_clicked)
        drive_layout.addWidget(self.rpm_up_button)
        
        self.set_speed_button = QPushButton("Set")
        self.set_speed_button.setMaximumWidth(50)
        self.set_speed_button.clicked.connect(self._on_set_speed_clicked)
        drive_layout.addWidget(self.set_speed_button)
        
        self.drive_enabled_checkbox = QCheckBox("Drive")
        self.drive_enabled_checkbox.stateChanged.connect(self._on_drive_enable_changed)
        drive_layout.addWidget(self.drive_enabled_checkbox)
        
        group_layout.addLayout(drive_layout)
        
        # Separator
        separator = QLabel("|")
        separator.setStyleSheet("color: gray; font-weight: bold;")
        group_layout.addWidget(separator)
        
        # Brake motor controls - compact inline layout
        brake_layout = QHBoxLayout()
        brake_layout.addWidget(QLabel("Load (A):"))
        
        self.target_load_input = QLineEdit("0")
        self.target_load_input.setMaximumWidth(100)
        brake_layout.addWidget(self.target_load_input)
        
        # Current up/down buttons
        self.current_down_button = QPushButton("-")
        self.current_down_button.setMaximumWidth(25)
        self.current_down_button.clicked.connect(self._on_current_down_clicked)
        brake_layout.addWidget(self.current_down_button)
        
        self.current_up_button = QPushButton("+")
        self.current_up_button.setMaximumWidth(25)
        self.current_up_button.clicked.connect(self._on_current_up_clicked)
        brake_layout.addWidget(self.current_up_button)
        
        self.set_load_button = QPushButton("Set")
        self.set_load_button.setMaximumWidth(50)
        self.set_load_button.clicked.connect(self._on_set_load_clicked)
        brake_layout.addWidget(self.set_load_button)
        
        self.brake_enabled_checkbox = QCheckBox("Brake")
        self.brake_enabled_checkbox.stateChanged.connect(self._on_brake_enable_changed)
        brake_layout.addWidget(self.brake_enabled_checkbox)
        
        group_layout.addLayout(brake_layout)
        
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
        
    def _on_rpm_up_clicked(self):
        """Handle RPM up button click."""
        current_rpm = self.get_target_rpm()
        new_rpm = min(current_rpm + self.RPM_STEP, self.MAX_RPM)
        self.set_target_rpm(new_rpm)
        self.drive_speed_requested.emit(new_rpm)
        
    def _on_rpm_down_clicked(self):
        """Handle RPM down button click."""
        current_rpm = self.get_target_rpm()
        new_rpm = max(current_rpm - self.RPM_STEP, self.MIN_RPM)
        self.set_target_rpm(new_rpm)
        self.drive_speed_requested.emit(new_rpm)
        
    def _on_current_up_clicked(self):
        """Handle current up button click."""
        current_load = self.get_target_load()
        new_load = min(current_load + self.CURRENT_STEP, self.MAX_CURRENT)
        self.set_target_load(round(new_load, 1))
        self.brake_load_requested.emit(new_load)
        
    def _on_current_down_clicked(self):
        """Handle current down button click."""
        current_load = self.get_target_load()
        new_load = max(current_load - self.CURRENT_STEP, self.MIN_CURRENT)
        self.set_target_load(round(new_load, 1))
        self.brake_load_requested.emit(new_load)
        
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
        self.rpm_up_button.setEnabled(enabled)
        self.rpm_down_button.setEnabled(enabled)
        self.current_up_button.setEnabled(enabled)
        self.current_down_button.setEnabled(enabled)