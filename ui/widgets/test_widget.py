"""
Test automation widget for dynamometer interface.
Handles automated test sequence controls.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
                             QPushButton, QLineEdit, QSizePolicy)
from PyQt5.QtCore import pyqtSignal


class TestWidget(QWidget):
    """Widget for test automation controls."""
    
    speed_sweep_requested = pyqtSignal(int, int, int, int)  # start_rpm, end_rpm, steps, duration
    test_stop_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Create the test automation UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create group box with reduced height
        group_box = QGroupBox("Automated Testing")
        group_box.setMaximumHeight(85)  # Slightly taller to accommodate duration field
        main_layout.addWidget(group_box)
        
        # Group box layout - horizontal for compactness
        group_layout = QHBoxLayout(group_box)
        group_layout.setSpacing(0)  # No spacing - we'll control it manually
        group_layout.setContentsMargins(8, 8, 8, 8)
        
        # Sweep label
        sweep_label = QLabel("Sweep:")
        sweep_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        group_layout.addWidget(sweep_label)
        group_layout.addSpacing(10)
        
        # Start label and input - tightly coupled
        start_label = QLabel("Start:")
        start_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        group_layout.addWidget(start_label)
        
        self.sweep_start_input = QLineEdit("0")
        self.sweep_start_input.setFixedWidth(60)
        self.sweep_start_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        group_layout.addWidget(self.sweep_start_input)
        group_layout.addSpacing(25)
        
        # End label and input - tightly coupled
        end_label = QLabel("End:")
        end_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        group_layout.addWidget(end_label)
        
        self.sweep_end_input = QLineEdit("5000")
        self.sweep_end_input.setFixedWidth(60)
        self.sweep_end_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        group_layout.addWidget(self.sweep_end_input)
        group_layout.addSpacing(25)
        
        # Steps label and input - tightly coupled
        steps_label = QLabel("Steps:")
        steps_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        group_layout.addWidget(steps_label)
        
        self.sweep_steps_input = QLineEdit("10")
        self.sweep_steps_input.setFixedWidth(50)
        self.sweep_steps_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        group_layout.addWidget(self.sweep_steps_input)
        group_layout.addSpacing(25)
        
        # Duration label and input - tightly coupled
        duration_label = QLabel("Duration:")
        duration_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        group_layout.addWidget(duration_label)
        
        self.step_duration_input = QLineEdit("3")
        self.step_duration_input.setFixedWidth(50)
        self.step_duration_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        group_layout.addWidget(self.step_duration_input)
        group_layout.addSpacing(25)
        
        self.start_sweep_button = QPushButton("Start")
        self.start_sweep_button.setMaximumWidth(60)
        self.start_sweep_button.clicked.connect(self._on_start_sweep_clicked)
        group_layout.addWidget(self.start_sweep_button)
        
        # Add spacing between start and stop buttons
        group_layout.addSpacing(10)
        
        self.stop_test_button = QPushButton("Stop")
        self.stop_test_button.setMaximumWidth(60)
        self.stop_test_button.clicked.connect(self.test_stop_requested.emit)
        self.stop_test_button.setEnabled(False)
        group_layout.addWidget(self.stop_test_button)
        
        # Add stretch to push status label to the right
        group_layout.addStretch()
        
        # Test status
        self.test_status_label = QLabel("Ready")
        self.test_status_label.setStyleSheet("color: green; font-weight: bold;")
        group_layout.addWidget(self.test_status_label)
        
    def _on_start_sweep_clicked(self):
        """Handle start sweep button click."""
        try:
            start_rpm = int(self.sweep_start_input.text())
            end_rpm = int(self.sweep_end_input.text())
            steps = int(self.sweep_steps_input.text())
            duration = int(self.step_duration_input.text())
            self.speed_sweep_requested.emit(start_rpm, end_rpm, steps, duration)
        except ValueError:
            # Handle invalid input - could emit error signal
            pass
            
    def update_test_status(self, status):
        """Update test status label."""
        self.test_status_label.setText(status)
        
    def set_test_running(self, running):
        """Update UI for test running state."""
        self.start_sweep_button.setEnabled(not running)
        self.stop_test_button.setEnabled(running)
        
        # Disable inputs during test
        self.sweep_start_input.setEnabled(not running)
        self.sweep_end_input.setEnabled(not running)
        self.sweep_steps_input.setEnabled(not running)
        self.step_duration_input.setEnabled(not running)
        
    def get_sweep_parameters(self):
        """Get current sweep parameters."""
        try:
            return {
                'start_rpm': int(self.sweep_start_input.text()),
                'end_rpm': int(self.sweep_end_input.text()),
                'steps': int(self.sweep_steps_input.text()),
                'duration': int(self.step_duration_input.text())
            }
        except ValueError:
            return None
            
    def set_sweep_parameters(self, start_rpm, end_rpm, steps, duration=3):
        """Set sweep parameters."""
        self.sweep_start_input.setText(str(start_rpm))
        self.sweep_end_input.setText(str(end_rpm))
        self.sweep_steps_input.setText(str(steps))
        self.step_duration_input.setText(str(duration))
        
    def set_enabled(self, enabled):
        """Enable/disable test controls."""
        self.sweep_start_input.setEnabled(enabled)
        self.sweep_end_input.setEnabled(enabled)
        self.sweep_steps_input.setEnabled(enabled)
        self.step_duration_input.setEnabled(enabled)
        self.start_sweep_button.setEnabled(enabled)
        # Note: stop button state depends on test running status