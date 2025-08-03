"""
Test automation controller for dyno.
Handles automated test sequences and data collection.
"""

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal


class TestThread(QThread):
    """Thread for running automated test sequences."""
    
    status_update = pyqtSignal(str)
    test_complete = pyqtSignal()
    
    def __init__(self, start_rpm, end_rpm, steps, command_interface, step_duration=3):
        super().__init__()
        self.start_rpm = start_rpm
        self.end_rpm = end_rpm
        self.steps = steps
        self.command_interface = command_interface
        self.step_duration = step_duration  # Duration in seconds for each step
        self.running = False
        
    def run(self):
        """Execute the test sequence."""
        self.running = True
        rpm_values = np.linspace(self.start_rpm, self.end_rpm, self.steps)
        
        for i, rpm in enumerate(rpm_values):
            if not self.running:
                break
                
            self.status_update.emit(f"Step {i+1}/{self.steps}: {rpm:.0f} RPM ({self.step_duration}s)")
            
            # Set speed
            self.command_interface.set_drive_speed(int(rpm))
            
            # Wait for stabilization and measurement
            self.msleep(self.step_duration * 1000)  # Convert seconds to milliseconds
            
        self.test_complete.emit()
        
    def stop(self):
        """Stop the test sequence."""
        self.running = False


class TestController:
    """Controller for automated testing functionality."""
    
    def __init__(self, command_interface, data_model):
        self.command_interface = command_interface
        self.data_model = data_model
        self.test_thread = None
        self.test_running = False
        
        # Callbacks
        self.status_callback = None
        self.complete_callback = None
        
    def set_callbacks(self, status_callback, complete_callback):
        """Set callback functions for test status updates."""
        self.status_callback = status_callback
        self.complete_callback = complete_callback
        
    def start_speed_sweep(self, start_rpm, end_rpm, steps, step_duration=3):
        """Start an automated speed sweep test."""
        if self.test_running:
            return False, "Test already running"
            
        try:
            # Validate parameters
            if start_rpm < 0 or end_rpm < 0 or steps <= 0:
                return False, "Invalid test parameters"
                
            if start_rpm >= end_rpm:
                return False, "Start RPM must be less than end RPM"
                
            if step_duration <= 0:
                return False, "Step duration must be positive"
                
            if step_duration > 300:  # Safety limit of 5 minutes per step
                return False, "Step duration exceeds safety limit (300 seconds)"
                
            # Clear previous test data
            self.data_model.clear_test_data()
            
            # Create and start test thread
            self.test_thread = TestThread(start_rpm, end_rpm, steps, self.command_interface, step_duration)
            
            if self.status_callback:
                self.test_thread.status_update.connect(self.status_callback)
            if self.complete_callback:
                self.test_thread.test_complete.connect(self._on_test_complete)
                
            self.test_thread.start()
            self.test_running = True
            
            return True, f"Starting speed sweep: {start_rpm} to {end_rpm} RPM in {steps} steps ({step_duration}s each)"
            
        except Exception as e:
            return False, f"Failed to start test: {str(e)}"
            
    def stop_test(self):
        """Stop the currently running test."""
        if self.test_thread and self.test_running:
            self.test_thread.stop()
            self.test_running = False
            return True
        return False
        
    def is_test_running(self):
        """Check if a test is currently running."""
        return self.test_running
        
    def _on_test_complete(self):
        """Handle test completion."""
        self.test_running = False
        if self.complete_callback:
            self.complete_callback()


class TestSequence:
    """Defines different types of test sequences."""
    
    @staticmethod
    def speed_sweep(start_rpm, end_rpm, steps):
        """Create a speed sweep test sequence."""
        return {
            'type': 'speed_sweep',
            'start_rpm': start_rpm,
            'end_rpm': end_rpm,
            'steps': steps,
            'description': f"Speed sweep from {start_rpm} to {end_rpm} RPM in {steps} steps"
        }
        
    @staticmethod
    def load_sweep(start_load, end_load, steps, rpm):
        """Create a load sweep test sequence at fixed RPM."""
        return {
            'type': 'load_sweep',
            'start_load': start_load,
            'end_load': end_load,
            'steps': steps,
            'rpm': rpm,
            'description': f"Load sweep from {start_load} to {end_load} A at {rpm} RPM in {steps} steps"
        }
        
    @staticmethod
    def efficiency_map(rpm_points, load_points):
        """Create an efficiency mapping test sequence."""
        return {
            'type': 'efficiency_map',
            'rpm_points': rpm_points,
            'load_points': load_points,
            'description': f"Efficiency map with {len(rpm_points)} RPM points and {len(load_points)} load points"
        }


class TestValidator:
    """Validates test parameters and safety conditions."""
    
    @staticmethod
    def validate_speed_sweep(start_rpm, end_rpm, steps, step_duration=3):
        """Validate speed sweep parameters."""
        errors = []
        
        if start_rpm < 0:
            errors.append("Start RPM cannot be negative")
        if end_rpm < 0:
            errors.append("End RPM cannot be negative")
        if steps <= 0:
            errors.append("Steps must be positive")
        if start_rpm >= end_rpm:
            errors.append("Start RPM must be less than end RPM")
        if end_rpm > 10000:  # Safety limit
            errors.append("End RPM exceeds safety limit (10000 RPM)")
        if step_duration <= 0:
            errors.append("Step duration must be positive")
        if step_duration > 300:
            errors.append("Step duration exceeds safety limit (300 seconds)")
            
        return len(errors) == 0, errors
        
    @staticmethod
    def validate_load_sweep(start_load, end_load, steps, rpm):
        """Validate load sweep parameters."""
        errors = []
        
        if start_load < 0:
            errors.append("Start load cannot be negative")
        if end_load < 0:
            errors.append("End load cannot be negative")
        if steps <= 0:
            errors.append("Steps must be positive")
        if start_load >= end_load:
            errors.append("Start load must be less than end load")
        if end_load > 50:  # Safety limit
            errors.append("End load exceeds safety limit (50 A)")
        if rpm < 0:
            errors.append("RPM cannot be negative")
        if rpm > 10000:
            errors.append("RPM exceeds safety limit (10000 RPM)")
            
        return len(errors) == 0, errors