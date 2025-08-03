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
                'mechanical_power': 0.0
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
            current_timestamp = data['timestamp'] / 1000.0
            
            # Detect ESP32 restart (timestamp reset to ~0)
            if self.start_time is not None and current_timestamp < 5.0 and len(self.timestamps) > 10:
                # ESP32 has restarted - clear all chart data and reset
                self._clear_time_series_data()
                self.start_time = None
            
            # Convert timestamp to relative seconds
            if not self.start_time:
                self.start_time = current_timestamp
            
            rel_time = current_timestamp - self.start_time
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
            
    def add_test_result(self):
        """Add current data to test results."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        data_point = {
            'time': timestamp,
            'rpm': self.current_values['drive']['rpm'],
            'load_current': self.current_values['brake']['current'],
            'power': self.current_values['dyno']['mechanical_power'],
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
        
    def _clear_time_series_data(self):
        """Clear all time series data (used on ESP32 restart detection)."""
        self.timestamps.clear()
        self.drive_rpm.clear()
        self.drive_current.clear()
        self.drive_voltage.clear()
        self.drive_temp_fet.clear()
        self.drive_temp_motor.clear()
        self.brake_rpm.clear()
        self.brake_current.clear()
        self.brake_voltage.clear()
        self.brake_temp_fet.clear()
        self.brake_temp_motor.clear()
        self.mechanical_power.clear()
        
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
            'mechanical_power': list(self.mechanical_power)
        }
        
    def has_data(self):
        """Check if there's any data to plot."""
        return len(self.timestamps) > 0