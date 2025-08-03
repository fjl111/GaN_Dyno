"""
Data display widget for dynamometer interface.
Shows current values and status indicators.
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, 
                             QLabel, QGridLayout)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


class DataDisplayWidget(QWidget):
    """Widget for displaying current motor and dyno data."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drive_labels = {}
        self.brake_labels = {}
        self.dyno_labels = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Create the data display UI."""
        # Main layout
        main_layout = QHBoxLayout(self)
        
        # Drive motor status
        drive_group = QGroupBox("Drive Motor Status")
        drive_layout = QGridLayout(drive_group)
        
        row = 0
        for key in ['rpm', 'current', 'voltage', 'temp_fet', 'temp_motor', 'duty_cycle', 'data_age']:
            label_text = key.replace('_', ' ').title() + ":"
            drive_layout.addWidget(QLabel(label_text), row, 0)
            
            value_label = QLabel("N/A")
            value_label.setFont(QFont("Arial", 16, QFont.Bold))
            drive_layout.addWidget(value_label, row, 1)
            self.drive_labels[key] = value_label
            row += 1
            
        main_layout.addWidget(drive_group)
        
        # Brake motor status
        brake_group = QGroupBox("Brake Motor Status")
        brake_layout = QGridLayout(brake_group)
        
        row = 0
        for key in ['rpm', 'current', 'voltage', 'temp_fet', 'temp_motor', 'duty_cycle', 'data_age']:
            label_text = key.replace('_', ' ').title() + ":"
            brake_layout.addWidget(QLabel(label_text), row, 0)
            
            value_label = QLabel("N/A")
            value_label.setFont(QFont("Arial", 16, QFont.Bold))
            brake_layout.addWidget(value_label, row, 1)
            self.brake_labels[key] = value_label
            row += 1
            
        main_layout.addWidget(brake_group)
        
        # Dyno metrics and status
        dyno_group = QGroupBox("Dyno Metrics & Status")
        dyno_layout = QGridLayout(dyno_group)
        
        row = 0
        for key in ['target_rpm', 'target_load', 'mechanical_power']:
            label_text = key.replace('_', ' ').title() + ":"
            dyno_layout.addWidget(QLabel(label_text), row, 0)
            
            value_label = QLabel("N/A")
            value_label.setFont(QFont("Arial", 16, QFont.Bold))
            dyno_layout.addWidget(value_label, row, 1)
            self.dyno_labels[key] = value_label
            row += 1
            
        # System status indicators
        dyno_layout.addWidget(QLabel("Drive Enabled:"), row, 0)
        self.drive_status_label = QLabel("NO")
        self.drive_status_label.setStyleSheet("color: red; font-weight: bold;")
        dyno_layout.addWidget(self.drive_status_label, row, 1)
        row += 1
        
        dyno_layout.addWidget(QLabel("Brake Enabled:"), row, 0)
        self.brake_status_label = QLabel("NO")
        self.brake_status_label.setStyleSheet("color: red; font-weight: bold;")
        dyno_layout.addWidget(self.brake_status_label, row, 1)
        row += 1
        
        dyno_layout.addWidget(QLabel("Emergency Stop:"), row, 0)
        self.estop_status_label = QLabel("INACTIVE")
        self.estop_status_label.setStyleSheet("color: green; font-weight: bold;")
        dyno_layout.addWidget(self.estop_status_label, row, 1)
        
        main_layout.addWidget(dyno_group)
        
    def update_data(self, data_model):
        """Update all displayed values from data model."""
        current_values = data_model.current_values
        
        # Update drive motor labels
        for key, label in self.drive_labels.items():
            value = current_values['drive'][key]
            text = self._format_value(key, value)
            label.setText(text)
            
            # Apply color coding
            self._apply_color_coding(label, key, value)
            
        # Update brake motor labels
        for key, label in self.brake_labels.items():
            value = current_values['brake'][key]
            text = self._format_value(key, value)
            label.setText(text)
            
            # Apply color coding
            self._apply_color_coding(label, key, value)
            
        # Update dyno metric labels
        for key, label in self.dyno_labels.items():
            value = current_values['dyno'][key]
            text = self._format_value(key, value)
            label.setText(text)
            
        # Update status indicators
        self._update_status_indicators(current_values['dyno'])
        
    def _format_value(self, key, value):
        """Format value based on key type."""
        if key in ['current', 'voltage', 'temp_fet', 'temp_motor', 'duty_cycle']:
            return f"{value:.2f}"
        elif key in ['target_load', 'mechanical_power']:
            return f"{value:.3f}"
        elif key == 'data_age':
            return f"{value} ms"
        else:
            return str(value)
            
    def _apply_color_coding(self, label, key, value):
        """Apply color coding based on value limits."""
        if key == 'temp_fet' and value > 80:
            label.setStyleSheet("color: red; font-weight: bold;")
        elif key == 'temp_motor' and value > 100:
            label.setStyleSheet("color: red; font-weight: bold;")
        elif key == 'data_age' and value > 1000:
            label.setStyleSheet("color: red; font-weight: bold;")
        else:
            label.setStyleSheet("color: black; font-weight: bold;")
            
    def _update_status_indicators(self, dyno_values):
        """Update status indicator labels."""
        # Drive enabled status
        if dyno_values['drive_enabled']:
            self.drive_status_label.setText("YES")
            self.drive_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.drive_status_label.setText("NO")
            self.drive_status_label.setStyleSheet("color: red; font-weight: bold;")
            
        # Brake enabled status
        if dyno_values['brake_enabled']:
            self.brake_status_label.setText("YES")
            self.brake_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.brake_status_label.setText("NO")
            self.brake_status_label.setStyleSheet("color: red; font-weight: bold;")
            
        # Emergency stop status
        if dyno_values['emergency_stop']:
            self.estop_status_label.setText("ACTIVE")
            self.estop_status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.estop_status_label.setText("INACTIVE")
            self.estop_status_label.setStyleSheet("color: green; font-weight: bold;")