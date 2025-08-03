"""
Console widget for dynamometer interface.
Provides command input and output logging.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QTextEdit)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal, Qt
import time


class ConsoleWidget(QWidget):
    """Widget for console input/output."""
    
    command_requested = pyqtSignal(str)  # command
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Create the console UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Output area
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        console_font = QFont("Consolas", 12)  # Use monospace font
        self.console_output.setFont(console_font)
        main_layout.addWidget(self.console_output)
        
        # Input area
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Command:"))
        
        self.console_input = QLineEdit()
        self.console_input.returnPressed.connect(self._on_send_command)
        input_layout.addWidget(self.console_input)
        
        send_button = QPushButton("Send")
        send_button.clicked.connect(self._on_send_command)
        input_layout.addWidget(send_button)
        
        main_layout.addLayout(input_layout)
        
    def _on_send_command(self):
        """Handle command send."""
        command = self.console_input.text().strip()
        if command:
            self.command_requested.emit(command)
            self.console_input.clear()
            
    def log_message(self, message):
        """Add a message to the console output."""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.console_output.append(formatted_message)
        
    def log_tx(self, command):
        """Log a transmitted command."""
        self.log_message(f"TX: {command}")
        
    def log_rx(self, data):
        """Log received data."""
        self.log_message(f"RX: {data}")
        
    def log_error(self, error):
        """Log an error message."""
        self.log_message(f"ERROR: {error}")
        
    def log_info(self, info):
        """Log an info message."""
        self.log_message(f"INFO: {info}")
        
    def log_warning(self, warning):
        """Log a warning message."""
        self.log_message(f"WARNING: {warning}")
        
    def clear(self):
        """Clear the console output."""
        self.console_output.clear()
        
    def set_input_enabled(self, enabled):
        """Enable/disable command input."""
        self.console_input.setEnabled(enabled)
        
    def get_current_command(self):
        """Get the current command text."""
        return self.console_input.text()
        
    def set_current_command(self, command):
        """Set the current command text."""
        self.console_input.setText(command)