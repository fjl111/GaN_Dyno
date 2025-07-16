"""
Test automation widget for dynamometer interface.
Handles automated test sequence controls.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel, 
                             QPushButton, QLineEdit, QGridLayout)
from PyQt5.QtCore import pyqtSignal


class TestWidget(QWidget):
    """Widget for test automation controls."""
    
    speed_sweep_requested = pyqtSignal(int, int, int)  # start_rpm, end_rpm, steps
    test_stop_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Create the test automation UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create group box
        group_box = QGroupBox("Automated Testing")
        main_layout.addWidget(group_box)
        
        # Group box layout
        group_layout = QGridLayout(group_box)
        
        # Speed sweep controls
        group_layout.addWidget(QLabel("Speed Sweep:"), 0, 0)
        group_layout.addWidget(QLabel("Start RPM:"), 0, 1)
        self.sweep_start_input = QLineEdit("0")
        self.sweep_start_input.setMaximumWidth(80)
        group_layout.addWidget(self.sweep_start_input, 0, 2)
        
        group_layout.addWidget(QLabel("End RPM:"), 0, 3)
        self.sweep_end_input = QLineEdit("5000")
        self.sweep_end_input.setMaximumWidth(80)
        group_layout.addWidget(self.sweep_end_input, 0, 4)
        
        group_layout.addWidget(QLabel("Steps:"), 0, 5)
        self.sweep_steps_input = QLineEdit("10")
        self.sweep_steps_input.setMaximumWidth(60)
        group_layout.addWidget(self.sweep_steps_input, 0, 6)
        
        self.start_sweep_button = QPushButton("Start Speed Sweep")
        self.start_sweep_button.clicked.connect(self._on_start_sweep_clicked)
        group_layout.addWidget(self.start_sweep_button, 0, 7)
        
        self.stop_test_button = QPushButton("Stop Test")
        self.stop_test_button.clicked.connect(self.test_stop_requested.emit)
        self.stop_test_button.setEnabled(False)
        group_layout.addWidget(self.stop_test_button, 0, 8)
        
        # Test status
        self.test_status_label = QLabel("No test running")
        group_layout.addWidget(self.test_status_label, 1, 0, 1, 9)
        
    def _on_start_sweep_clicked(self):
        """Handle start sweep button click."""
        try:
            start_rpm = int(self.sweep_start_input.text())
            end_rpm = int(self.sweep_end_input.text())
            steps = int(self.sweep_steps_input.text())
            self.speed_sweep_requested.emit(start_rpm, end_rpm, steps)
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
        
    def get_sweep_parameters(self):
        """Get current sweep parameters."""
        try:
            return {
                'start_rpm': int(self.sweep_start_input.text()),
                'end_rpm': int(self.sweep_end_input.text()),
                'steps': int(self.sweep_steps_input.text())
            }
        except ValueError:
            return None
            
    def set_sweep_parameters(self, start_rpm, end_rpm, steps):
        """Set sweep parameters."""
        self.sweep_start_input.setText(str(start_rpm))
        self.sweep_end_input.setText(str(end_rpm))
        self.sweep_steps_input.setText(str(steps))
        
    def set_enabled(self, enabled):
        """Enable/disable test controls."""
        self.sweep_start_input.setEnabled(enabled)
        self.sweep_end_input.setEnabled(enabled)
        self.sweep_steps_input.setEnabled(enabled)
        self.start_sweep_button.setEnabled(enabled)
        # Note: stop button state depends on test running status