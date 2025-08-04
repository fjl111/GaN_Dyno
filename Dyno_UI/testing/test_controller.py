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


class TwoDimensionalSweepThread(QThread):
    """Thread for running 2D sweep tests over speed and brake amperage."""
    
    status_update = pyqtSignal(str)
    test_complete = pyqtSignal()
    data_point_collected = pyqtSignal(dict)  # Emit data points as they're collected
    
    def __init__(self, rpm_range, amperage_range, rpm_steps, amperage_steps, 
                 command_interface, data_model, step_duration=5):
        super().__init__()
        self.start_rpm, self.end_rpm = rpm_range
        self.start_amperage, self.end_amperage = amperage_range
        self.rpm_steps = rpm_steps
        self.amperage_steps = amperage_steps
        self.command_interface = command_interface
        self.data_model = data_model
        self.step_duration = step_duration
        self.sample_rate_hz = 5  # Fixed 5Hz sampling rate
        self.running = False
        self.total_steps = rpm_steps * amperage_steps
        self.current_step = 0
        
    def run(self):
        """Execute the 2D sweep test sequence."""
        self.running = True
        self.current_step = 0
        
        rpm_values = np.linspace(self.start_rpm, self.end_rpm, self.rpm_steps)
        amperage_values = np.linspace(self.end_amperage, self.start_amperage, self.amperage_steps)
        
        # Perform nested sweep: for each RPM, sweep through all amperage values
        for rpm_idx, rpm in enumerate(rpm_values):
            if not self.running:
                break
                
            # Set drive speed
            self.command_interface.set_drive_speed(int(rpm))
            
            for amp_idx, amperage in enumerate(amperage_values):
                if not self.running:
                    break
                    
                self.current_step += 1
                
                # Update status
                self.status_update.emit(
                    f"Step {self.current_step}/{self.total_steps}: "
                    f"{rpm:.0f} RPM, {amperage:.2f} A ({self.step_duration}s)"
                )
                
                # Set brake load
                self.command_interface.set_brake_load(amperage)
                
                # Wait for stabilization
                stabilization_time = max(1, self.step_duration - 2)  # Reserve 2s for sampling
                self.msleep(stabilization_time * 1000)
                
                # Collect averaged data point
                data_point = self._collect_averaged_data_point(rpm, amperage)
                self.data_point_collected.emit(data_point)
                
        # Reset to safe state
        self.command_interface.set_drive_speed(0)
        self.command_interface.set_brake_load(0.0)
        
        self.test_complete.emit()
        
    def _collect_data_point(self, target_rpm, target_amperage):
        """Collect a single data point with current system state."""
        current_values = self.data_model.current_values
        
        data_point = {
            'target_rpm': target_rpm,
            'target_amperage': target_amperage,
            'actual_rpm': current_values['drive']['rpm'],
            'actual_amperage': current_values['brake']['current'],
            'drive_power': current_values['dyno']['drive_power'],
            'brake_power': current_values['dyno']['brake_power'],
            'total_power': current_values['dyno']['drive_power'] + current_values['dyno']['brake_power'],
            'drive_temp_fet': current_values['drive']['temp_fet'],
            'drive_temp_motor': current_values['drive']['temp_motor'],
            'brake_temp_fet': current_values['brake']['temp_fet'],
            'brake_temp_motor': current_values['brake']['temp_motor'],
            'max_temp_fet': max(current_values['drive']['temp_fet'], current_values['brake']['temp_fet']),
            'max_temp_motor': max(current_values['drive']['temp_motor'], current_values['brake']['temp_motor']),
            'drive_voltage': current_values['drive']['voltage'],
            'brake_voltage': current_values['brake']['voltage'],
            'timestamp': self.current_step
        }
        
        return data_point
    
    def _collect_averaged_data_point(self, target_rpm, target_amperage):
        """Collect multiple samples at 5Hz and return averaged data point."""
        # Data fields to average
        numeric_fields = [
            'actual_rpm', 'actual_amperage', 'drive_power', 'brake_power', 'total_power',
            'drive_temp_fet', 'drive_temp_motor', 'brake_temp_fet', 'brake_temp_motor',
            'drive_voltage', 'brake_voltage'
        ]
        
        # Calculate sampling parameters based on fixed 5Hz rate
        sampling_time = 2  # Use 2 seconds for sampling
        sample_interval_ms = int(1000 / self.sample_rate_hz)  # 200ms for 5Hz
        total_samples = int(sampling_time * self.sample_rate_hz)  # 10 samples at 5Hz for 2 seconds
        
        # Collect multiple samples
        samples = []
        
        for i in range(total_samples):
            if not self.running:
                break
                
            # Update status to show sampling progress
            if i == 0 or i == total_samples - 1:  # Update at start and end only
                self.status_update.emit(
                    f"Step {self.current_step}/{self.total_steps}: "
                    f"{target_rpm:.0f} RPM, {target_amperage:.2f} A - Sampling at 5Hz ({i+1}/{total_samples})"
                )
            
            # Get current values
            current_values = self.data_model.current_values
            
            sample = {
                'actual_rpm': current_values['drive']['rpm'],
                'actual_amperage': current_values['brake']['current'],
                'drive_power': current_values['dyno']['drive_power'],
                'brake_power': current_values['dyno']['brake_power'],
                'total_power': current_values['dyno']['drive_power'] + current_values['dyno']['brake_power'],
                'drive_temp_fet': current_values['drive']['temp_fet'],
                'drive_temp_motor': current_values['drive']['temp_motor'],
                'brake_temp_fet': current_values['brake']['temp_fet'],
                'brake_temp_motor': current_values['brake']['temp_motor'],
                'drive_voltage': current_values['drive']['voltage'],
                'brake_voltage': current_values['brake']['voltage']
            }
            
            samples.append(sample)
            
            # Wait before next sample (200ms for 5Hz)
            if i < total_samples - 1:  # Don't wait after last sample
                self.msleep(sample_interval_ms)
        
        # Calculate averages
        if not samples:
            # Fallback to single sample if no samples collected
            return self._collect_data_point(target_rpm, target_amperage)
        
        averaged_data = {
            'target_rpm': target_rpm,
            'target_amperage': target_amperage,
            'timestamp': self.current_step
        }
        
        # Calculate mean for each numeric field
        for field in numeric_fields:
            values = [sample[field] for sample in samples if field in sample]
            if values:
                averaged_data[field] = np.mean(values)
            else:
                averaged_data[field] = 0.0
        
        # Calculate derived fields from averages
        averaged_data['max_temp_fet'] = max(averaged_data['drive_temp_fet'], averaged_data['brake_temp_fet'])
        averaged_data['max_temp_motor'] = max(averaged_data['drive_temp_motor'], averaged_data['brake_temp_motor'])
        
        # Add statistical information for quality assessment
        averaged_data['sample_count'] = len(samples)
        
        # Calculate standard deviations for key measurements (optional quality metrics)
        key_fields = ['actual_rpm', 'actual_amperage', 'total_power', 'max_temp_fet']
        for field in key_fields:
            values = [sample.get(field, 0) for sample in samples if field in sample or field == 'max_temp_fet']
            if field == 'max_temp_fet':
                values = [max(sample.get('drive_temp_fet', 0), sample.get('brake_temp_fet', 0)) for sample in samples]
            
            if len(values) > 1:
                averaged_data[f'{field}_std'] = np.std(values)
            else:
                averaged_data[f'{field}_std'] = 0.0
        
        return averaged_data
        
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
        self.data_point_callback = None
        
        # 3D sweep data storage
        self.sweep_data = []
        
    def set_callbacks(self, status_callback, complete_callback, data_point_callback=None):
        """Set callback functions for test status updates."""
        self.status_callback = status_callback
        self.complete_callback = complete_callback
        self.data_point_callback = data_point_callback
        
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
    
    def start_3d_sweep(self, rpm_range, amperage_range, rpm_steps, amperage_steps, step_duration=5):
        """Start an automated 3D sweep test over RPM and brake amperage."""
        if self.test_running:
            return False, "Test already running"
            
        try:
            # Validate parameters
            start_rpm, end_rpm = rpm_range
            start_amperage, end_amperage = amperage_range
            
            validation_ok, errors = TestValidator.validate_3d_sweep(
                start_rpm, end_rpm, rpm_steps, 
                start_amperage, end_amperage, amperage_steps, 
                step_duration
            )
            
            if not validation_ok:
                return False, "; ".join(errors)
                
            # Clear previous test data
            self.data_model.clear_test_data()
            self.sweep_data = []
            
            # Create and start 3D sweep thread
            self.test_thread = TwoDimensionalSweepThread(
                rpm_range, amperage_range, rpm_steps, amperage_steps,
                self.command_interface, self.data_model, step_duration
            )
            
            # Connect callbacks
            if self.status_callback:
                self.test_thread.status_update.connect(self.status_callback)
            if self.complete_callback:
                self.test_thread.test_complete.connect(self._on_test_complete)
            
            # Connect data point collection
            self.test_thread.data_point_collected.connect(self._on_data_point_collected)
                
            self.test_thread.start()
            self.test_running = True
            
            total_steps = rpm_steps * amperage_steps
            return True, (f"Starting 3D sweep: {start_rpm}-{end_rpm} RPM ({rpm_steps} steps), "
                         f"{end_amperage}-{start_amperage} A ({amperage_steps} steps), "
                         f"{total_steps} total measurements ({step_duration}s each)")
            
        except Exception as e:
            return False, f"Failed to start 3D sweep: {str(e)}"
            
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
    
    def _on_data_point_collected(self, data_point):
        """Handle data point collection during 3D sweep."""
        self.sweep_data.append(data_point)
        if self.data_point_callback:
            self.data_point_callback(data_point)
    
    def get_sweep_data(self):
        """Get collected 3D sweep data."""
        return self.sweep_data.copy()
    
    def clear_sweep_data(self):
        """Clear collected 3D sweep data."""
        self.sweep_data = []


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
    
    @staticmethod
    def validate_3d_sweep(start_rpm, end_rpm, rpm_steps, start_amperage, end_amperage, amperage_steps, step_duration=5):
        """Validate 3D sweep parameters."""
        errors = []
        
        # Validate RPM parameters
        if start_rpm < 0:
            errors.append("Start RPM cannot be negative")
        if end_rpm < 0:
            errors.append("End RPM cannot be negative")
        if start_rpm >= end_rpm:
            errors.append("Start RPM must be less than end RPM")
        if end_rpm > 10000:
            errors.append("End RPM exceeds safety limit (10000 RPM)")
        if rpm_steps <= 0:
            errors.append("RPM steps must be positive")
        if rpm_steps > 50:
            errors.append("RPM steps exceed reasonable limit (50)")
            
        # Validate amperage parameters
        if start_amperage < 0:
            errors.append("Start amperage cannot be negative")
        if end_amperage < 0:
            errors.append("End amperage cannot be negative")
        if start_amperage >= end_amperage:
            errors.append("Start amperage must be less than end amperage")
        if end_amperage > 50:
            errors.append("End amperage exceeds safety limit (50 A)")
        if amperage_steps <= 0:
            errors.append("Amperage steps must be positive")
        if amperage_steps > 50:
            errors.append("Amperage steps exceed reasonable limit (50)")
            
        # Validate step duration
        if step_duration <= 0:
            errors.append("Step duration must be positive")
        if step_duration > 300:
            errors.append("Step duration exceeds safety limit (300 seconds)")
            
        # Validate total test duration
        total_steps = rpm_steps * amperage_steps
        total_duration = total_steps * step_duration
        if total_duration > 7200:  # 2 hours
            errors.append(f"Total test duration ({total_duration/60:.1f} minutes) exceeds safety limit (120 minutes)")
        if total_steps > 2500:  # Reasonable data point limit
            errors.append(f"Total data points ({total_steps}) exceeds reasonable limit (2500)")
            
        return len(errors) == 0, errors