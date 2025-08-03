"""
Main window UI.
Coordinates all components and handles the main application logic.
"""

import sys
import json
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QMessageBox, QApplication)
from PyQt5.QtCore import pyqtSlot, Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor

# Import other code functions
from models.data_model import DynamometerData
from communication.serial_handler import SerialHandler, CommandInterface, DataParser
from testing.test_controller import TestController
from visualization.plotter import DynamometerPlotter
from export.csv_exporter import CSVExporter
from ui.widgets.connection_widget import ConnectionWidget
from ui.widgets.control_widget import ControlWidget
from ui.widgets.test_widget import TestWidget
from ui.widgets.data_display_widget import DataDisplayWidget
from ui.widgets.console_widget import ConsoleWidget
from ui.widgets.results_widget import ResultsWidget
from ui.widgets.chart_controls_widget import ChartControlsWidget


class DynamometerMainWindow(QMainWindow):
    """Main window for the dynamometer application."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VESC Dynamo Controller")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Initialize components
        self.data_model = DynamometerData()
        self.serial_handler = SerialHandler()
        self.command_interface = CommandInterface(self.serial_handler)
        self.test_controller = TestController(self.command_interface, self.data_model)
        self.csv_exporter = CSVExporter(self)
        
        # Create UI
        self.setup_ui()
        
        # Setup connections
        self.setup_connections()
        
        # Setup timers
        self.setup_timers()
        
        # Initialize ports
        self.connection_widget.update_ports(self.serial_handler.get_available_ports())
        
    def setup_ui(self):
        """Create the main UI."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(5)  # Reduce spacing between elements
        
        # Create top row controls layout (connection and speed control)
        top_row_layout = QHBoxLayout()
        top_row_layout.setSpacing(15)
        
        # Create widgets
        self.connection_widget = ConnectionWidget()
        self.control_widget = ControlWidget()
        self.test_widget = TestWidget()
        
        # Add connection and control widgets to top row
        top_row_layout.addWidget(self.connection_widget)
        top_row_layout.addWidget(self.control_widget)
        top_row_layout.addStretch()  # Push everything to the left
        
        # Add the layouts to main layout
        main_layout.addLayout(top_row_layout)
        main_layout.addWidget(self.test_widget)
        
        # Create tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Charts tab with controls
        self.charts_widget = QWidget()
        self.tabs.addTab(self.charts_widget, "Real-time Charts")
        
        # Create chart layout with controls
        charts_layout = QVBoxLayout(self.charts_widget)
        
        # Add chart controls
        self.chart_controls = ChartControlsWidget()
        charts_layout.addWidget(self.chart_controls)
        
        # Create plotter container
        self.plotter_widget = QWidget()
        charts_layout.addWidget(self.plotter_widget)
        
        # Create plotter
        self.plotter = DynamometerPlotter(self.plotter_widget)
        self.plotter.set_data_model(self.data_model)
        
        # Sync initial time range from chart controls
        initial_time_range = self.chart_controls.get_current_time_range()
        self.plotter.set_time_range(initial_time_range)
        
        # Data display tab
        self.data_display_widget = DataDisplayWidget()
        self.tabs.addTab(self.data_display_widget, "Current Values")
        
        # Test results tab
        self.results_widget = ResultsWidget()
        self.tabs.addTab(self.results_widget, "Test Results")
        
        # Console tab
        self.console_widget = ConsoleWidget()
        self.tabs.addTab(self.console_widget, "Console")
        
        # Initially disable controls
        self.set_controls_enabled(False)
        
    def setup_connections(self):
        """Setup signal-slot connections."""
        # Connection widget signals
        self.connection_widget.connection_requested.connect(self.connect_to_device)
        self.connection_widget.disconnection_requested.connect(self.disconnect_from_device)
        self.connection_widget.refresh_ports_requested.connect(self.refresh_ports)
        self.connection_widget.emergency_stop_requested.connect(self.emergency_stop)
        
        # Control widget signals
        self.control_widget.drive_speed_requested.connect(self.set_drive_speed)
        self.control_widget.brake_load_requested.connect(self.set_brake_load)
        self.control_widget.drive_enable_requested.connect(self.set_drive_enabled)
        self.control_widget.brake_enable_requested.connect(self.set_brake_enabled)
        
        # Test widget signals
        self.test_widget.speed_sweep_requested.connect(self.start_speed_sweep)
        self.test_widget.test_stop_requested.connect(self.stop_test)
        
        # Results widget signals
        self.results_widget.clear_results_requested.connect(self.clear_test_results)
        self.results_widget.export_results_requested.connect(self.export_test_results)
        
        # Console widget signals
        self.console_widget.command_requested.connect(self.send_console_command)
        
        # Chart controls signals
        self.chart_controls.time_range_changed.connect(self.plotter.set_time_range)
        
        # Serial handler callbacks
        self.serial_handler.set_callbacks(self.process_data, self.handle_serial_error)
        
        # Test controller callbacks
        self.test_controller.set_callbacks(self.update_test_status, self.on_test_complete)
        
    def setup_timers(self):
        """Setup update timers."""
        # GUI update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_gui)
        self.update_timer.start(100)  # Update every 100ms
        
        # Database cleanup timer (once per hour)
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cleanup_old_data)
        self.cleanup_timer.start(3600000)  # 1 hour in milliseconds
        
    def connect_to_device(self, port):
        """Connect to ESP32 device."""
        try:
            if self.serial_handler.connect(port):
                self.connection_widget.set_connected(True)
                self.set_controls_enabled(True)
                self.console_widget.log_info(f"Connected to {port}")
            else:
                QMessageBox.critical(self, "Connection Error", "Failed to connect to device")
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect: {str(e)}")
            
    def disconnect_from_device(self):
        """Disconnect from ESP32 device."""
        self.serial_handler.disconnect()
        self.connection_widget.set_connected(False)
        self.set_controls_enabled(False)
        self.console_widget.log_info("Disconnected from device")
        
    def refresh_ports(self):
        """Refresh available serial ports."""
        ports = self.serial_handler.get_available_ports()
        self.connection_widget.update_ports(ports)
        
    def emergency_stop(self):
        """Trigger emergency stop."""
        self.stop_test()
        self.command_interface.emergency_stop()
        self.console_widget.log_warning("EMERGENCY STOP ACTIVATED")
        
    def set_drive_speed(self, rpm):
        """Set drive motor speed."""
        if self.command_interface.set_drive_speed(rpm):
            self.console_widget.log_tx(f"speed {rpm}")
        else:
            QMessageBox.warning(self, "Warning", "Failed to send speed command")
            
    def set_brake_load(self, current):
        """Set brake motor load."""
        if self.command_interface.set_brake_load(current):
            self.console_widget.log_tx(f"load {current}")
        else:
            QMessageBox.warning(self, "Warning", "Failed to send load command")
            
    def set_drive_enabled(self, enabled):
        """Enable/disable drive motor."""
        if enabled:
            success = self.command_interface.enable_drive()
            command = "enable_drive"
        else:
            success = self.command_interface.disable_all()
            command = "disable_all"
            
        if success:
            self.console_widget.log_tx(command)
        else:
            QMessageBox.warning(self, "Warning", "Failed to send enable command")
            
    def set_brake_enabled(self, enabled):
        """Enable/disable brake motor."""
        if enabled:
            success = self.command_interface.enable_brake()
            command = "enable_brake"
        else:
            success = self.command_interface.disable_all()
            command = "disable_all"
            
        if success:
            self.console_widget.log_tx(command)
        else:
            QMessageBox.warning(self, "Warning", "Failed to send enable command")
            
    def start_speed_sweep(self, start_rpm, end_rpm, steps, duration):
        """Start automated speed sweep test."""
        success, message = self.test_controller.start_speed_sweep(start_rpm, end_rpm, steps, duration)
        
        if success:
            self.test_widget.set_test_running(True)
            self.console_widget.log_info(message)
        else:
            QMessageBox.critical(self, "Test Error", message)
            
    def stop_test(self):
        """Stop current test."""
        if self.test_controller.stop_test():
            self.test_widget.set_test_running(False)
            self.test_widget.update_test_status("Test stopped")
            self.console_widget.log_info("Test stopped")
            
    def clear_test_results(self):
        """Clear test results."""
        self.data_model.clear_test_data()
        self.results_widget.clear_results()
        self.console_widget.log_info("Test results cleared")
        
    def export_test_results(self):
        """Export test results to CSV."""
        success, message = self.csv_exporter.export_test_data(self.data_model.test_data)
        if success:
            self.console_widget.log_info(message)
        else:
            self.console_widget.log_error(message)
            
    def send_console_command(self, command):
        """Send raw command from console."""
        if self.command_interface.send_raw_command(command):
            self.console_widget.log_tx(command)
        else:
            QMessageBox.warning(self, "Warning", "Failed to send command")
            
    @pyqtSlot(str)
    def process_data(self, line):
        """Process incoming data from ESP32."""
        data, is_json = DataParser.parse_line(line)
        
        if is_json:
            if DataParser.validate_data(data):
                self.data_model.update_from_json(data)
                
                # Add to test results if test is running
                if self.test_controller.is_test_running():
                    result = self.data_model.add_test_result()
                    self.results_widget.add_result(result)
            else:
                self.console_widget.log_error(f"Invalid data structure: {str(data)[:50]}...")
        else:
            self.console_widget.log_rx(line)
            
    @pyqtSlot(str)
    def handle_serial_error(self, error_msg):
        """Handle serial communication errors."""
        self.console_widget.log_error(error_msg)
        
        if "Read error" in error_msg:
            self.disconnect_from_device()
            
    @pyqtSlot(str)
    def update_test_status(self, status):
        """Update test status display."""
        self.test_widget.update_test_status(status)
        
    @pyqtSlot()
    def on_test_complete(self):
        """Handle test completion."""
        self.test_widget.set_test_running(False)
        self.test_widget.update_test_status("Test completed")
        self.console_widget.log_info("Test completed")
        
    def update_gui(self):
        """Update GUI elements."""
        # Update data display
        self.data_display_widget.update_data(self.data_model)
        
        # Update control widget checkboxes only if state differs
        drive_enabled_data = self.data_model.current_values['dyno']['drive_enabled']
        brake_enabled_data = self.data_model.current_values['dyno']['brake_enabled']
        
        # Only update if the checkbox state differs from the data to prevent overriding user input
        if self.control_widget.drive_enabled_checkbox.isChecked() != drive_enabled_data:
            self.control_widget.update_drive_enabled(drive_enabled_data)
        if self.control_widget.brake_enabled_checkbox.isChecked() != brake_enabled_data:
            self.control_widget.update_brake_enabled(brake_enabled_data)
    
    def cleanup_old_data(self):
        """Clean up old database data to prevent excessive storage growth."""
        try:
            self.data_model.cleanup_old_data(days_to_keep=7)  # Keep 7 days of data
        except Exception as e:
            self.console_widget.log_error(f"Database cleanup failed: {str(e)}")
            
    def export_chart_view(self):
        """Export current chart view to image file."""
        from PyQt5.QtWidgets import QFileDialog
        import matplotlib.pyplot as plt
        
        # Get save file path
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Chart View", "chart_view.png",
            "PNG files (*.png);;PDF files (*.pdf);;SVG files (*.svg)"
        )
        
        if file_path:
            try:
                # Save the current figure
                self.plotter.fig.savefig(file_path, dpi=300, bbox_inches='tight')
                self.console_widget.log_info(f"Chart view exported to: {file_path}")
                
                # Show success message
                QMessageBox.information(
                    self, "Export Successful", 
                    f"Chart view successfully exported to:\n{file_path}"
                )
            except Exception as e:
                self.console_widget.log_error(f"Export failed: {str(e)}")
                QMessageBox.warning(
                    self, "Export Failed", 
                    f"Failed to export chart view:\n{str(e)}"
                )
        
    def set_controls_enabled(self, enabled):
        """Enable/disable control widgets."""
        self.control_widget.set_enabled(enabled)
        self.test_widget.set_enabled(enabled)
        self.console_widget.set_input_enabled(enabled)
        
    def closeEvent(self, event):
        """Handle application closing."""
        if self.test_controller.is_test_running():
            self.test_controller.stop_test()
        if self.serial_handler.is_connected():
            self.serial_handler.disconnect()
        event.accept()


def setup_application_style():
    """Setup application-wide styling."""
    app = QApplication.instance()
    
    # Set application style
    app.setStyle('Fusion')
    
    # Set larger default font
    default_font = QFont()
    default_font.setPointSize(16)
    app.setFont(default_font)
    
    # Force light mode
    light_palette = QPalette()
    light_palette.setColor(QPalette.Window, QColor(240, 240, 240))
    light_palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.Base, QColor(255, 255, 255))
    light_palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
    light_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
    light_palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.Text, QColor(0, 0, 0))
    light_palette.setColor(QPalette.Button, QColor(240, 240, 240))
    light_palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    light_palette.setColor(QPalette.Link, QColor(0, 0, 255))
    light_palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
    light_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    
    app.setPalette(light_palette)