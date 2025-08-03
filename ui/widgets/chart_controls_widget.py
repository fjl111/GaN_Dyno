"""
Chart controls widget for dynamometer interface.
Provides interactive controls for chart display and performance settings.
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, 
                             QLabel, QSlider, QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class ChartControlsWidget(QWidget):
    """Widget for controlling chart time range display."""
    
    # Signals for communicating with main window
    time_range_changed = pyqtSignal(int)  # seconds
    export_current_data_requested = pyqtSignal()
    export_visible_data_requested = pyqtSignal()
    export_all_data_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Create the simple time range control UI."""
        # Main layout
        main_layout = QHBoxLayout(self)
        
        # Time range controls
        time_group = QGroupBox("Chart Time Range")
        time_layout = QHBoxLayout(time_group)
        
        time_layout.addWidget(QLabel("Show last:"))
        
        # Time range slider (10 seconds to all data)
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setMinimum(0)  # 0 = 10 seconds
        self.time_slider.setMaximum(6)  # 6 = all data
        self.time_slider.setValue(3)    # Default to 60 seconds
        self.time_slider.setTickPosition(QSlider.TicksBelow)
        self.time_slider.setTickInterval(1)
        time_layout.addWidget(self.time_slider)
        
        # Label to show current time range
        self.time_label = QLabel("2 minutes")
        self.time_label.setMinimumWidth(100)
        self.time_label.setFont(QFont("Arial", 12, QFont.Bold))
        time_layout.addWidget(self.time_label)
        
        main_layout.addWidget(time_group)
        
        # Export controls
        export_group = QGroupBox("Export Data")
        export_layout = QVBoxLayout(export_group)
        
        # Export buttons
        export_buttons_layout = QHBoxLayout()
        
        self.export_current_btn = QPushButton("Export Current Values")
        self.export_current_btn.setToolTip("Export snapshot of current motor values")
        self.export_current_btn.clicked.connect(self.export_current_data_requested.emit)
        export_buttons_layout.addWidget(self.export_current_btn)
        
        self.export_visible_btn = QPushButton("Export Visible Data")
        self.export_visible_btn.setToolTip("Export data for the currently visible time range")
        self.export_visible_btn.clicked.connect(self.export_visible_data_requested.emit)
        export_buttons_layout.addWidget(self.export_visible_btn)
        
        self.export_all_btn = QPushButton("Export All Session Data")
        self.export_all_btn.setToolTip("Export all data from the current session")
        self.export_all_btn.clicked.connect(self.export_all_data_requested.emit)
        export_buttons_layout.addWidget(self.export_all_btn)
        
        export_layout.addLayout(export_buttons_layout)
        main_layout.addWidget(export_group)
        
    def connect_signals(self):
        """Connect widget signals to internal handlers."""
        self.time_slider.valueChanged.connect(self._on_time_slider_changed)
        
    def _on_time_slider_changed(self, value):
        """Handle time range slider change."""
        # Map slider value to seconds
        time_map = {
            0: 10,    # 10 seconds
            1: 30,    # 30 seconds  
            2: 60,    # 1 minute
            3: 120,   # 2 minutes
            4: 300,   # 5 minutes
            5: 600,   # 10 minutes
            6: 0      # All data
        }
        
        seconds = time_map.get(value, 60)
        
        # Update label
        if seconds == 0:
            self.time_label.setText("All data")
        elif seconds < 60:
            self.time_label.setText(f"{seconds} seconds")
        elif seconds < 3600:
            minutes = seconds // 60
            self.time_label.setText(f"{minutes} minute{'s' if minutes > 1 else ''}")
        else:
            hours = seconds // 3600
            self.time_label.setText(f"{hours} hour{'s' if hours > 1 else ''}")
            
        self.time_range_changed.emit(seconds)
            
    def set_time_range(self, seconds):
        """Programmatically set the time range."""
        # Map seconds to slider value
        value_map = {
            10: 0, 30: 1, 60: 2, 120: 3, 300: 4, 600: 5, 0: 6
        }
        value = value_map.get(seconds, 2)  # Default to 60 seconds
        self.time_slider.setValue(value)
        
    def get_current_time_range(self):
        """Get current time range in seconds."""
        value = self.time_slider.value()
        time_map = {
            0: 10, 1: 30, 2: 60, 3: 120, 4: 300, 5: 600, 6: 0
        }
        return time_map.get(value, 60)
    
    def set_export_enabled(self, enabled):
        """Enable/disable export buttons."""
        self.export_current_btn.setEnabled(enabled)
        self.export_visible_btn.setEnabled(enabled)
        self.export_all_btn.setEnabled(enabled)