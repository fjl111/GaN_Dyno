"""
Response time testing widget for dynamometer interface.
Provides UI for running various response time tests and viewing results.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QLabel, QPushButton, QLineEdit, QTextEdit, 
                             QComboBox, QSpinBox, QDoubleSpinBox, QProgressBar,
                             QTabWidget, QScrollArea, QGridLayout, QCheckBox)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QFont, QTextCursor
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from testing.response_time_test import (ResponseTimeTestThread, PingTest, 
                                       CommandResponseTest, StepResponseTest,
                                       ResponseTimeAnalyzer)


class ResponseTimeWidget(QWidget):
    """Widget for response time testing functionality."""
    
    # Signals
    test_started = pyqtSignal()
    test_completed = pyqtSignal(dict)
    
    def __init__(self, command_interface, data_model, parent=None):
        super().__init__(parent)
        self.command_interface = command_interface
        self.data_model = data_model
        self.current_test_thread = None
        self.test_results = []
        
        self.setup_ui()
        self.setup_ping_test()
        
    def setup_ui(self):
        """Create the response time testing UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title_label = QLabel("Response Time Testing")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Test tabs
        self.test_tabs = QTabWidget()
        main_layout.addWidget(self.test_tabs)
        
        # Create test tabs
        self.create_ping_test_tab()
        self.create_command_response_tab()
        self.create_step_response_tab()
        self.create_results_tab()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
    def create_ping_test_tab(self):
        """Create the ping test tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Test parameters group
        params_group = QGroupBox("Ping Test Parameters")
        params_layout = QGridLayout(params_group)
        
        params_layout.addWidget(QLabel("Iterations:"), 0, 0)
        self.ping_iterations_spin = QSpinBox()
        self.ping_iterations_spin.setRange(1, 1000)
        self.ping_iterations_spin.setValue(50)
        params_layout.addWidget(self.ping_iterations_spin, 0, 1)
        
        params_layout.addWidget(QLabel("Delay (ms):"), 1, 0)
        self.ping_delay_spin = QSpinBox()
        self.ping_delay_spin.setRange(1, 1000)
        self.ping_delay_spin.setValue(10)
        params_layout.addWidget(self.ping_delay_spin, 1, 1)
        
        layout.addWidget(params_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.ping_start_button = QPushButton("Start Ping Test")
        self.ping_start_button.clicked.connect(self.start_ping_test)
        button_layout.addWidget(self.ping_start_button)
        
        self.ping_stop_button = QPushButton("Stop Test")
        self.ping_stop_button.clicked.connect(self.stop_test)
        self.ping_stop_button.setEnabled(False)
        button_layout.addWidget(self.ping_stop_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Results display
        self.ping_results_text = QTextEdit()
        self.ping_results_text.setMaximumHeight(200)
        self.ping_results_text.setReadOnly(True)
        layout.addWidget(QLabel("Results:"))
        layout.addWidget(self.ping_results_text)
        
        layout.addStretch()
        self.test_tabs.addTab(tab, "Ping Test")
        
    def create_command_response_tab(self):
        """Create the command response test tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Test parameters group
        params_group = QGroupBox("Command Response Test Parameters")
        params_layout = QGridLayout(params_group)
        
        params_layout.addWidget(QLabel("Test Type:"), 0, 0)
        self.cmd_test_type_combo = QComboBox()
        self.cmd_test_type_combo.addItems(["RPM Response", "Load Response"])
        params_layout.addWidget(self.cmd_test_type_combo, 0, 1)
        
        params_layout.addWidget(QLabel("Target RPM:"), 1, 0)
        self.cmd_target_rpm_spin = QSpinBox()
        self.cmd_target_rpm_spin.setRange(0, 10000)
        self.cmd_target_rpm_spin.setValue(1000)
        params_layout.addWidget(self.cmd_target_rpm_spin, 1, 1)
        
        params_layout.addWidget(QLabel("Target Load (A):"), 2, 0)
        self.cmd_target_load_spin = QDoubleSpinBox()
        self.cmd_target_load_spin.setRange(0.0, 50.0)
        self.cmd_target_load_spin.setValue(2.0)
        self.cmd_target_load_spin.setDecimals(1)
        params_layout.addWidget(self.cmd_target_load_spin, 2, 1)
        
        params_layout.addWidget(QLabel("Timeout (s):"), 3, 0)
        self.cmd_timeout_spin = QDoubleSpinBox()
        self.cmd_timeout_spin.setRange(1.0, 60.0)
        self.cmd_timeout_spin.setValue(5.0)
        self.cmd_timeout_spin.setDecimals(1)
        params_layout.addWidget(self.cmd_timeout_spin, 3, 1)
        
        layout.addWidget(params_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.cmd_start_button = QPushButton("Start Command Test")
        self.cmd_start_button.clicked.connect(self.start_command_test)
        button_layout.addWidget(self.cmd_start_button)
        
        self.cmd_stop_button = QPushButton("Stop Test")
        self.cmd_stop_button.clicked.connect(self.stop_test)
        self.cmd_stop_button.setEnabled(False)
        button_layout.addWidget(self.cmd_stop_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Results display
        self.cmd_results_text = QTextEdit()
        self.cmd_results_text.setMaximumHeight(200)
        self.cmd_results_text.setReadOnly(True)
        layout.addWidget(QLabel("Results:"))
        layout.addWidget(self.cmd_results_text)
        
        layout.addStretch()
        self.test_tabs.addTab(tab, "Command Response")
        
    def create_step_response_tab(self):
        """Create the step response test tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Test parameters group
        params_group = QGroupBox("Step Response Test Parameters")
        params_layout = QGridLayout(params_group)
        
        params_layout.addWidget(QLabel("Target RPM:"), 0, 0)
        self.step_target_rpm_spin = QSpinBox()
        self.step_target_rpm_spin.setRange(0, 10000)
        self.step_target_rpm_spin.setValue(800)
        params_layout.addWidget(self.step_target_rpm_spin, 0, 1)
        
        params_layout.addWidget(QLabel("Duration (s):"), 1, 0)
        self.step_duration_spin = QDoubleSpinBox()
        self.step_duration_spin.setRange(1.0, 60.0)
        self.step_duration_spin.setValue(10.0)
        self.step_duration_spin.setDecimals(1)
        params_layout.addWidget(self.step_duration_spin, 1, 1)
        
        params_layout.addWidget(QLabel("Sample Rate (Hz):"), 2, 0)
        self.step_sample_rate_spin = QSpinBox()
        self.step_sample_rate_spin.setRange(1, 200)
        self.step_sample_rate_spin.setValue(50)
        params_layout.addWidget(self.step_sample_rate_spin, 2, 1)
        
        layout.addWidget(params_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.step_start_button = QPushButton("Start Step Test")
        self.step_start_button.clicked.connect(self.start_step_test)
        button_layout.addWidget(self.step_start_button)
        
        self.step_stop_button = QPushButton("Stop Test")
        self.step_stop_button.clicked.connect(self.stop_test)
        self.step_stop_button.setEnabled(False)
        button_layout.addWidget(self.step_stop_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Results display
        self.step_results_text = QTextEdit()
        self.step_results_text.setMaximumHeight(200)
        self.step_results_text.setReadOnly(True)
        layout.addWidget(QLabel("Results:"))
        layout.addWidget(self.step_results_text)
        
        layout.addStretch()
        self.test_tabs.addTab(tab, "Step Response")
        
    def create_results_tab(self):
        """Create the results summary tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.clear_results_button = QPushButton("Clear All Results")
        self.clear_results_button.clicked.connect(self.clear_results)
        button_layout.addWidget(self.clear_results_button)
        
        self.export_results_button = QPushButton("Export to CSV")
        self.export_results_button.clicked.connect(self.export_results)
        button_layout.addWidget(self.export_results_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Results summary
        self.results_summary_text = QTextEdit()
        self.results_summary_text.setReadOnly(True)
        layout.addWidget(QLabel("Test Results Summary:"))
        layout.addWidget(self.results_summary_text)
        
        self.test_tabs.addTab(tab, "Results Summary")
        
    def setup_ping_test(self):
        """Setup ping test functionality."""
        self.ping_test = PingTest(self.command_interface)
        
    def start_ping_test(self):
        """Start ping test."""
        if self.current_test_thread and self.current_test_thread.isRunning():
            return
            
        # Get parameters
        iterations = self.ping_iterations_spin.value()
        delay_ms = self.ping_delay_spin.value()
        
        # Setup test parameters
        test_params = {
            'iterations': iterations,
            'delay_between_pings': delay_ms / 1000.0
        }
        
        # Start test thread
        self.current_test_thread = ResponseTimeTestThread(
            'ping', test_params, self.command_interface, self.data_model
        )
        self.current_test_thread.progress_update.connect(self.update_status)
        self.current_test_thread.test_complete.connect(self.on_ping_test_complete)
        
        self.current_test_thread.start()
        self.set_test_running(True)
        
    def start_command_test(self):
        """Start command response test."""
        if self.current_test_thread and self.current_test_thread.isRunning():
            return
            
        # Get parameters
        test_type = self.cmd_test_type_combo.currentText()
        target_rpm = self.cmd_target_rpm_spin.value()
        target_load = self.cmd_target_load_spin.value()
        timeout = self.cmd_timeout_spin.value()
        
        # Setup test parameters based on type
        if test_type == "RPM Response":
            test_name = 'rpm_response'
            test_params = {
                'target_rpm': target_rpm,
                'timeout_seconds': timeout
            }
        else:  # Load Response
            test_name = 'load_response'
            test_params = {
                'target_load': target_load,
                'timeout_seconds': timeout
            }
        
        # Start test thread
        self.current_test_thread = ResponseTimeTestThread(
            test_name, test_params, self.command_interface, self.data_model
        )
        self.current_test_thread.progress_update.connect(self.update_status)
        self.current_test_thread.test_complete.connect(self.on_command_test_complete)
        
        self.current_test_thread.start()
        self.set_test_running(True)
        
    def start_step_test(self):
        """Start step response test."""
        if self.current_test_thread and self.current_test_thread.isRunning():
            return
            
        # Get parameters
        target_rpm = self.step_target_rpm_spin.value()
        duration = self.step_duration_spin.value()
        sample_rate = self.step_sample_rate_spin.value()
        
        # Setup test parameters
        test_params = {
            'target_rpm': target_rpm,
            'duration_seconds': duration,
            'sample_rate_hz': sample_rate
        }
        
        # Start test thread
        self.current_test_thread = ResponseTimeTestThread(
            'rpm_step', test_params, self.command_interface, self.data_model
        )
        self.current_test_thread.progress_update.connect(self.update_status)
        self.current_test_thread.test_complete.connect(self.on_step_test_complete)
        
        self.current_test_thread.start()
        self.set_test_running(True)
        
    def stop_test(self):
        """Stop current test."""
        if self.current_test_thread:
            self.current_test_thread.stop()
            self.current_test_thread.wait(5000)  # Wait up to 5 seconds
            self.set_test_running(False)
            
    def set_test_running(self, running):
        """Update UI for test running state."""
        # Disable/enable start buttons
        self.ping_start_button.setEnabled(not running)
        self.cmd_start_button.setEnabled(not running)
        self.step_start_button.setEnabled(not running)
        
        # Enable/disable stop buttons
        self.ping_stop_button.setEnabled(running)
        self.cmd_stop_button.setEnabled(running)
        self.step_stop_button.setEnabled(running)
        
        # Show/hide progress bar
        self.progress_bar.setVisible(running)
        if running:
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
    def update_status(self, message):
        """Update status label."""
        self.status_label.setText(message)
        
    def on_ping_test_complete(self, result):
        """Handle ping test completion."""
        self.set_test_running(False)
        self.test_results.append(result)
        
        # Display results
        if "error" in result:
            text = f"Error: {result['error']}"
        else:
            text = f"""Ping Test Results:
Iterations: {result['iterations']}
Mean latency: {result['mean_us']:.1f} μs
Min latency: {result['min_us']:.1f} μs
Max latency: {result['max_us']:.1f} μs
Std deviation: {result['stdev_us']:.1f} μs"""
        
        self.ping_results_text.setText(text)
        self.update_results_summary()
        self.status_label.setText("Ping test completed")
        
    def on_command_test_complete(self, result):
        """Handle command test completion."""
        self.set_test_running(False)
        self.test_results.append(result)
        
        # Display results
        if "error" in result:
            text = f"Error: {result['error']}"
        else:
            if result.get('test_type') == 'rpm_response':
                text = f"""RPM Response Test Results:
Target RPM: {result['target_rpm']}
Initial RPM: {result['initial_rpm']}
Final RPM: {result['final_rpm']}
Response time: {result['response_time_ms']:.2f} ms"""
            else:  # load_response
                text = f"""Load Response Test Results:
Target Load: {result['target_load']} A
Initial Current: {result['initial_current']} A
Final Current: {result['final_current']} A
Response time: {result['response_time_ms']:.2f} ms"""
        
        self.cmd_results_text.setText(text)
        self.update_results_summary()
        self.status_label.setText("Command test completed")
        
    def on_step_test_complete(self, result):
        """Handle step test completion."""
        self.set_test_running(False)
        self.test_results.append(result)
        
        # Display results
        if "error" in result:
            text = f"Error: {result['error']}"
        else:
            analysis = result.get('analysis', {})
            if "error" in analysis:
                text = f"Analysis error: {analysis['error']}"
            else:
                text = f"""Step Response Test Results:
Target RPM: {result['target_rpm']}
Initial RPM: {result['initial_rpm']}
Final RPM: {analysis['final_value']:.1f}
Rise time: {analysis['rise_time_s']:.3f} s
Settling time: {analysis['settling_time_s']:.3f} s
Overshoot: {analysis['overshoot_percent']:.1f}%
Steady-state error: {analysis['steady_state_error']:.1f} RPM"""
        
        self.step_results_text.setText(text)
        self.update_results_summary()
        self.status_label.setText("Step test completed")
        
    def update_results_summary(self):
        """Update the results summary tab."""
        if not self.test_results:
            self.results_summary_text.setText("No test results yet.")
            return
            
        summary = ResponseTimeAnalyzer.generate_summary_report(self.test_results)
        self.results_summary_text.setText(summary)
        
    def clear_results(self):
        """Clear all test results."""
        self.test_results.clear()
        self.ping_results_text.clear()
        self.cmd_results_text.clear()
        self.step_results_text.clear()
        self.results_summary_text.clear()
        self.status_label.setText("Results cleared")
        
    def export_results(self):
        """Export results to CSV file."""
        if not self.test_results:
            self.status_label.setText("No results to export")
            return
            
        from PyQt5.QtWidgets import QFileDialog
        import time
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Results", 
            f"response_time_results_{int(time.time())}.csv",
            "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                message = ResponseTimeAnalyzer.export_to_csv(self.test_results, filename)
                self.status_label.setText(message)
            except Exception as e:
                self.status_label.setText(f"Export failed: {str(e)}")