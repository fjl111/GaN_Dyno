"""
Connection control widget for dynamometer interface.
Handles serial port selection and connection status.
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QGroupBox, QLabel, 
                             QPushButton, QComboBox)
from PyQt5.QtCore import pyqtSignal


class ConnectionWidget(QWidget):
    """Widget for managing serial connection."""
    
    connection_requested = pyqtSignal(str)  # port
    disconnection_requested = pyqtSignal()
    refresh_ports_requested = pyqtSignal()
    emergency_stop_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.connected = False
        self.setup_ui()
        
    def setup_ui(self):
        """Create the connection UI."""
        # Create group box
        group_box = QGroupBox("Connection")
        layout = QHBoxLayout(self)
        layout.addWidget(group_box)
        
        # Group box layout
        group_layout = QHBoxLayout(group_box)
        
        # Port selection
        group_layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        group_layout.addWidget(self.port_combo)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_ports_requested.emit)
        group_layout.addWidget(self.refresh_button)
        
        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self._on_connect_clicked)
        group_layout.addWidget(self.connect_button)
        
        # Status label
        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        group_layout.addWidget(self.status_label)
        
        group_layout.addStretch()
        
        # Emergency stop button
        self.estop_button = QPushButton("EMERGENCY STOP")
        self.estop_button.setStyleSheet("""
            QPushButton {
                background-color: red;
                color: white;
                font-weight: bold;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:pressed {
                background-color: darkred;
            }
        """)
        self.estop_button.clicked.connect(self.emergency_stop_requested.emit)
        group_layout.addWidget(self.estop_button)
        
    def _on_connect_clicked(self):
        """Handle connect button click."""
        if self.connected:
            self.disconnection_requested.emit()
        else:
            port = self.port_combo.currentText()
            if port:
                self.connection_requested.emit(port)
                
    def set_connected(self, connected):
        """Update connection status."""
        self.connected = connected
        if connected:
            self.connect_button.setText("Disconnect")
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.connect_button.setText("Connect")
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            
    def update_ports(self, ports):
        """Update available ports."""
        current_port = self.port_combo.currentText()
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        
        # Restore previous selection if still available
        if current_port in ports:
            self.port_combo.setCurrentText(current_port)
            
    def get_selected_port(self):
        """Get currently selected port."""
        return self.port_combo.currentText()
        
    def set_enabled(self, enabled):
        """Enable/disable connection controls."""
        self.port_combo.setEnabled(enabled)
        self.refresh_button.setEnabled(enabled)
        self.connect_button.setEnabled(enabled)