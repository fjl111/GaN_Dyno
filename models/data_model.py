"""
Data model to hold data received from the Motor Controllers over CAN.
Handles current values and data storage for plotting.
"""

from collections import deque
from datetime import datetime
import json


class DynamometerData:
    """Manages all data for the dynamometer application."""
    
    def __init__(self, max_points=1000):
        self.max_points = max_points
        self.start_time = None
        
        # Time series data for plotting
        self.timestamps = deque(maxlen=max_points)
        
        # Drive motor data
        self.drive_rpm = deque(maxlen=max_points)
        self.drive_current = deque(maxlen=max_points)
        self.drive_voltage = deque(maxlen=max_points)
        self.drive_temp_fet = deque(maxlen=max_points)
        self.drive_temp_motor = deque(maxlen=max_points)
        
        # Brake motor data
        self.brake_rpm = deque(maxlen=max_points)
        self.brake_current = deque(maxlen=max_points)
        self.brake_voltage = deque(maxlen=max_points)
        self.brake_temp_fet = deque(maxlen=max_points)
        self.brake_temp_motor = deque(maxlen=max_points)
        
        # Dyno metrics
        self.mechanical_power = deque(maxlen=max_points)
        self.efficiency = deque(maxlen=max_points)
        self.torque_nm = deque(maxlen=max_points)
        
        # Current values for display
        self.current_values = {
            'drive': {
                'rpm': 0, 'current': 0.0, 'voltage': 0.0, 'temp_fet': 0.0, 
                'temp_motor': 0.0, 'duty_cycle': 0.0, 'data_age': 0
            },
            'brake': {
                'rpm': 0, 'current': 0.0, 'voltage': 0.0, 'temp_fet': 0.0,
                'temp_motor': 0.0, 'duty_cycle': 0.0, 'data_age': 0
            },
            'dyno': {
                'target_rpm': 0, 'target_load': 0.0, 'drive_enabled': False,
                'brake_enabled': False, 'emergency_stop': False, 
                'mechanical_power': 0.0, 'efficiency': 0.0, 'torque_nm': 0.0
            }
        }
        
        # Test data storage
        self.test_data = []
        
    def update_from_json(self, data):
        """Update data from JSON received from ESP32."""
        # Update current values from JSON data
        if 'drive' in data:
            for key, value in data['drive'].items():
                if key in self.current_values['drive']:
                    self.current_values['drive'][key] = value
                    
        if 'brake' in data:
            for key, value in data['brake'].items():
                if key in self.current_values['brake']:
                    self.current_values['brake'][key] = value
                    
        if 'dyno' in data:
            for key, value in data['dyno'].items():
                if key in self.current_values['dyno']:
                    self.current_values['dyno'][key] = value
        
        # Add to time series data
        if 'timestamp' in data:
            # Convert timestamp to relative seconds
            if not self.start_time:
                self.start_time = data['timestamp'] / 1000.0
            
            rel_time = (data['timestamp'] / 1000.0) - self.start_time
            self.timestamps.append(rel_time)
            
            # Add data points
            self.drive_rpm.append(self.current_values['drive']['rpm'])
            self.drive_current.append(self.current_values['drive']['current'])
            self.drive_voltage.append(self.current_values['drive']['voltage'])
            self.drive_temp_fet.append(self.current_values['drive']['temp_fet'])
            self.drive_temp_motor.append(self.current_values['drive']['temp_motor'])
            
            self.brake_rpm.append(self.current_values['brake']['rpm'])
            self.brake_current.append(self.current_values['brake']['current'])
            self.brake_voltage.append(self.current_values['brake']['voltage'])
            self.brake_temp_fet.append(self.current_values['brake']['temp_fet'])
            self.brake_temp_motor.append(self.current_values['brake']['temp_motor'])
            
            self.mechanical_power.append(self.current_values['dyno']['mechanical_power'])
            self.efficiency.append(self.current_values['dyno']['efficiency'])
            self.torque_nm.append(self.current_values['dyno']['torque_nm'])
            
    def add_test_result(self):
        """Add current data to test results."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        data_point = {
            'time': timestamp,
            'rpm': self.current_values['drive']['rpm'],
            'load_current': self.current_values['brake']['current'],
            'power': self.current_values['dyno']['mechanical_power'],
            'torque': self.current_values['dyno']['torque_nm'],
            'efficiency': self.current_values['dyno']['efficiency'],
            'temp_fet': max(self.current_values['drive']['temp_fet'], 
                          self.current_values['brake']['temp_fet']),
            'temp_motor': max(self.current_values['drive']['temp_motor'], 
                            self.current_values['brake']['temp_motor'])
        }
        
        self.test_data.append(data_point)
        return data_point
        
    def clear_test_data(self):
        """Clear all test data."""
        self.test_data = []
        
    def get_plot_data(self):
        """Get all data needed for plotting."""
        return {
            'timestamps': list(self.timestamps),
            'drive_rpm': list(self.drive_rpm),
            'drive_current': list(self.drive_current),
            'drive_temp_fet': list(self.drive_temp_fet),
            'drive_temp_motor': list(self.drive_temp_motor),
            'brake_rpm': list(self.brake_rpm),
            'brake_current': list(self.brake_current),
            'brake_temp_fet': list(self.brake_temp_fet),
            'brake_temp_motor': list(self.brake_temp_motor),
            'mechanical_power': list(self.mechanical_power),
            'efficiency': list(self.efficiency),
            'torque_nm': list(self.torque_nm)
        }
        
    def has_data(self):
        """Check if there's any data to plot."""
        return len(self.timestamps) > 0