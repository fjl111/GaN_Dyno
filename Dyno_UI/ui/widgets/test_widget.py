"""
Test automation widget for dynamometer interface.
Handles automated test sequence controls.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
                             QPushButton, QLineEdit, QSizePolicy, QComboBox, QFrame)
from PyQt5.QtCore import pyqtSignal


class TestWidget(QWidget):
    """Widget for test automation controls."""
    
    speed_sweep_requested = pyqtSignal(int, int, int, int)  # start_rpm, end_rpm, steps, duration
    sweep_3d_requested = pyqtSignal(tuple, tuple, int, int, int)  # rpm_range, amp_range, rpm_steps, amp_steps, duration
    test_stop_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Create the test automation UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create group box
        group_box = QGroupBox("Automated Testing")
        group_box.setMaximumHeight(120)  # Taller for 3D sweep options
        main_layout.addWidget(group_box)
        
        # Group box layout
        group_layout = QVBoxLayout(group_box)
        group_layout.setContentsMargins(8, 8, 8, 8)
        
        # Test type selection row
        type_layout = QHBoxLayout()
        type_label = QLabel("Test Type:")
        type_layout.addWidget(type_label)
        
        self.test_type_combo = QComboBox()
        self.test_type_combo.addItems(["Speed Sweep (1D)", "3D Sweep (Speed + Amperage)"])
        self.test_type_combo.currentTextChanged.connect(self._on_test_type_changed)
        type_layout.addWidget(self.test_type_combo)
        type_layout.addStretch()
        
        group_layout.addLayout(type_layout)
        
        # Parameters layout (will be dynamic based on test type)
        self.params_layout = QHBoxLayout()
        group_layout.addLayout(self.params_layout)
        
        # Control buttons and status row  
        controls_layout = QHBoxLayout()
        
        self.start_sweep_button = QPushButton("Start")
        self.start_sweep_button.setMaximumWidth(80)
        self.start_sweep_button.clicked.connect(self._on_start_sweep_clicked)
        controls_layout.addWidget(self.start_sweep_button)
        
        self.stop_test_button = QPushButton("Stop")
        self.stop_test_button.setMaximumWidth(80)
        self.stop_test_button.clicked.connect(self.test_stop_requested.emit)
        self.stop_test_button.setEnabled(False)
        controls_layout.addWidget(self.stop_test_button)
        
        controls_layout.addStretch()
        
        # Test status
        self.test_status_label = QLabel("Ready")
        self.test_status_label.setStyleSheet("color: green; font-weight: bold;")
        controls_layout.addWidget(self.test_status_label)
        
        group_layout.addLayout(controls_layout)
        
        # Initialize with speed sweep UI
        self._setup_speed_sweep_ui()
        
    def _clear_params_layout(self):
        """Clear all widgets from parameters layout."""
        while self.params_layout.count():
            child = self.params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def _setup_speed_sweep_ui(self):
        """Setup UI for speed sweep test."""
        self._clear_params_layout()
        
        # RPM range
        self.params_layout.addWidget(QLabel("RPM:"))
        self.sweep_start_input = QLineEdit("0")
        self.sweep_start_input.setFixedWidth(60)
        self.params_layout.addWidget(self.sweep_start_input)
        
        self.params_layout.addWidget(QLabel("to"))
        self.sweep_end_input = QLineEdit("5000")
        self.sweep_end_input.setFixedWidth(60)
        self.params_layout.addWidget(self.sweep_end_input)
        
        # Steps
        self.params_layout.addWidget(QLabel("Steps:"))
        self.sweep_steps_input = QLineEdit("10")
        self.sweep_steps_input.setFixedWidth(50)
        self.params_layout.addWidget(self.sweep_steps_input)
        
        # Duration
        self.params_layout.addWidget(QLabel("Duration (s):"))
        self.step_duration_input = QLineEdit("3")
        self.step_duration_input.setFixedWidth(50)
        self.params_layout.addWidget(self.step_duration_input)
        
        self.params_layout.addStretch()
        
    def _setup_3d_sweep_ui(self):
        """Setup UI for 3D sweep test."""
        self._clear_params_layout()
        
        # RPM range
        self.params_layout.addWidget(QLabel("RPM:"))
        self.rpm_start_input = QLineEdit("0")
        self.rpm_start_input.setFixedWidth(50)
        self.params_layout.addWidget(self.rpm_start_input)
        
        self.params_layout.addWidget(QLabel("-"))
        self.rpm_end_input = QLineEdit("5000")
        self.rpm_end_input.setFixedWidth(50)
        self.params_layout.addWidget(self.rpm_end_input)
        
        self.params_layout.addWidget(QLabel("("))
        self.rpm_steps_input = QLineEdit("10")
        self.rpm_steps_input.setFixedWidth(30)
        self.params_layout.addWidget(self.rpm_steps_input)
        self.params_layout.addWidget(QLabel(")"))
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.params_layout.addWidget(separator)
        
        # Amperage range
        self.params_layout.addWidget(QLabel("Amps:"))
        self.amp_start_input = QLineEdit("0")
        self.amp_start_input.setFixedWidth(50)
        self.params_layout.addWidget(self.amp_start_input)
        
        self.params_layout.addWidget(QLabel("-"))
        self.amp_end_input = QLineEdit("10")
        self.amp_end_input.setFixedWidth(50)
        self.params_layout.addWidget(self.amp_end_input)
        
        self.params_layout.addWidget(QLabel("("))
        self.amp_steps_input = QLineEdit("5")
        self.amp_steps_input.setFixedWidth(30)
        self.params_layout.addWidget(self.amp_steps_input)
        self.params_layout.addWidget(QLabel(")"))
        
        # Duration
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        self.params_layout.addWidget(separator2)
        
        self.params_layout.addWidget(QLabel("Duration (s):"))
        self.step_duration_3d_input = QLineEdit("5")
        self.step_duration_3d_input.setFixedWidth(50)
        self.params_layout.addWidget(self.step_duration_3d_input)
        
        self.params_layout.addStretch()
        
    def _on_test_type_changed(self, test_type):
        """Handle test type change."""
        if "Speed Sweep" in test_type:
            self._setup_speed_sweep_ui()
        elif "3D Sweep" in test_type:
            self._setup_3d_sweep_ui()
            
    def _on_start_sweep_clicked(self):
        """Handle start sweep button click."""
        current_test = self.test_type_combo.currentText()
        
        try:
            if "Speed Sweep" in current_test:
                start_rpm = int(self.sweep_start_input.text())
                end_rpm = int(self.sweep_end_input.text())
                steps = int(self.sweep_steps_input.text())
                duration = int(self.step_duration_input.text())
                self.speed_sweep_requested.emit(start_rpm, end_rpm, steps, duration)
                
            elif "3D Sweep" in current_test:
                rpm_start = int(self.rpm_start_input.text())
                rpm_end = int(self.rpm_end_input.text())
                rpm_steps = int(self.rpm_steps_input.text())
                
                amp_start = float(self.amp_start_input.text())
                amp_end = float(self.amp_end_input.text())
                amp_steps = int(self.amp_steps_input.text())
                
                duration = int(self.step_duration_3d_input.text())
                
                rpm_range = (rpm_start, rpm_end)
                amp_range = (amp_start, amp_end)
                
                self.sweep_3d_requested.emit(rpm_range, amp_range, rpm_steps, amp_steps, duration)
                
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
        self.test_type_combo.setEnabled(not running)
        
        # Disable all input fields during test
        current_test = self.test_type_combo.currentText()
        
        if "Speed Sweep" in current_test:
            if hasattr(self, 'sweep_start_input'):
                self.sweep_start_input.setEnabled(not running)
            if hasattr(self, 'sweep_end_input'):
                self.sweep_end_input.setEnabled(not running)
            if hasattr(self, 'sweep_steps_input'):
                self.sweep_steps_input.setEnabled(not running)
            if hasattr(self, 'step_duration_input'):
                self.step_duration_input.setEnabled(not running)
                
        elif "3D Sweep" in current_test:
            if hasattr(self, 'rpm_start_input'):
                self.rpm_start_input.setEnabled(not running)
            if hasattr(self, 'rpm_end_input'):
                self.rpm_end_input.setEnabled(not running)
            if hasattr(self, 'rpm_steps_input'):
                self.rpm_steps_input.setEnabled(not running)
            if hasattr(self, 'amp_start_input'):
                self.amp_start_input.setEnabled(not running)
            if hasattr(self, 'amp_end_input'):
                self.amp_end_input.setEnabled(not running)
            if hasattr(self, 'amp_steps_input'):
                self.amp_steps_input.setEnabled(not running)
            if hasattr(self, 'step_duration_3d_input'):
                self.step_duration_3d_input.setEnabled(not running)
        
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