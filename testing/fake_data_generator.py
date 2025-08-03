#!/usr/bin/env python3
"""
Fake Data Generator for Dynamometer UI Testing
==============================================

Generates realistic fake data matching the DynamometerData JSON structure
for testing UI charts and data display widgets without hardware.

Usage:
    python testing/fake_data_generator.py [scenario]
    
    Scenarios:
    - startup: Motor startup sequence
    - load_test: Variable load testing
    - temp_ramp: Temperature increase simulation
    - steady_state: Constant operation
    - default: Mixed operation patterns

Example Integration:
    from testing.fake_data_generator import FakeDataGenerator
    generator = FakeDataGenerator()
    data = generator.generate_data_point()
    data_model.update_from_json(data)
"""

import json
import math
import random
import time
import sys
from typing import Dict, Any


class FakeDataGenerator:
    """Generates realistic fake dynamometer data for UI testing."""
    
    def __init__(self, scenario: str = "default"):
        self.scenario = scenario
        self.start_time = time.time() * 1000  # milliseconds
        self.time_offset = 0
        
        # Simulation parameters
        self.drive_rpm_target = 0
        self.brake_rpm_target = 0
        self.load_current_target = 0
        self.temp_ambient = 25.0
        
        # Current state tracking
        self.drive_rpm = 0
        self.brake_rpm = 0
        self.drive_current = 0
        self.brake_current = 0
        self.drive_temp_fet = self.temp_ambient
        self.drive_temp_motor = self.temp_ambient
        self.brake_temp_fet = self.temp_ambient
        self.brake_temp_motor = self.temp_ambient
        
        # Scenario setup
        self._setup_scenario()
        
    def _setup_scenario(self):
        """Configure parameters based on selected scenario."""
        if self.scenario == "startup":
            self.drive_rpm_target = 2000
            self.brake_rpm_target = 1980
            self.load_current_target = 15.0
        elif self.scenario == "load_test":
            self.drive_rpm_target = 2500
            self.brake_rpm_target = 2480
            self.load_current_target = 35.0
        elif self.scenario == "temp_ramp":
            self.drive_rpm_target = 3000
            self.brake_rpm_target = 2970
            self.load_current_target = 45.0
            self.temp_ambient = 40.0
        elif self.scenario == "steady_state":
            self.drive_rpm_target = 1500
            self.brake_rpm_target = 1495
            self.load_current_target = 20.0
        else:  # default - mixed patterns
            self.drive_rpm_target = 2200
            self.brake_rpm_target = 2180
            self.load_current_target = 25.0
            
    def _add_noise(self, value: float, noise_percent: float = 2.0) -> float:
        """Add realistic noise to a value."""
        noise = value * (noise_percent / 100.0) * random.uniform(-1, 1)
        return value + noise
        
    def _simulate_rpm_response(self, current_rpm: float, target_rpm: float, time_constant: float = 0.8) -> float:
        """Simulate realistic RPM response with acceleration/deceleration."""
        error = target_rpm - current_rpm
        response = current_rpm + (error * time_constant * 0.1)  # 0.1 for step size
        return max(0, self._add_noise(response, 1.5))
        
    def _simulate_temperature(self, current_temp: float, power_watts: float, ambient: float = None) -> float:
        """Simulate temperature based on power dissipation."""
        if ambient is None:
            ambient = self.temp_ambient
            
        # Temperature rise based on power (simplified thermal model)
        target_temp = ambient + (power_watts * 0.8)  # 0.8°C per watt
        
        # Thermal time constant (slow response)
        thermal_constant = 0.02
        temp_error = target_temp - current_temp
        new_temp = current_temp + (temp_error * thermal_constant)
        
        return self._add_noise(new_temp, 0.5)
        
    def _calculate_power(self, rpm: float, current: float, voltage: float) -> float:
        """Calculate mechanical power based on motor parameters."""
        # Simplified power calculation: P = V*I*efficiency - losses
        electrical_power = voltage * current
        efficiency = 0.85  # Typical motor efficiency
        mechanical_power = electrical_power * efficiency
        
        # Add some variation based on RPM
        rpm_factor = min(1.0, rpm / 3000.0)  # Efficiency varies with speed
        mechanical_power *= (0.7 + 0.3 * rpm_factor)
        
        return max(0, self._add_noise(mechanical_power, 2.0))
        
    def generate_data_point(self) -> Dict[str, Any]:
        """Generate a single data point matching DynamometerData JSON structure."""
        # Update time
        self.time_offset += random.uniform(180, 220)  # ~200ms intervals
        timestamp = int(self.start_time + self.time_offset)
        
        # Apply scenario-specific variations
        if self.scenario == "startup":
            # Gradual ramp-up
            time_factor = min(1.0, self.time_offset / 10000)  # 10 second ramp
            current_drive_target = self.drive_rpm_target * time_factor
            current_brake_target = self.brake_rpm_target * time_factor
            current_load_target = self.load_current_target * time_factor
        elif self.scenario == "load_test":
            # Sinusoidal load variation
            load_variation = math.sin(self.time_offset / 5000) * 0.3 + 0.7
            current_drive_target = self.drive_rpm_target
            current_brake_target = self.brake_rpm_target
            current_load_target = self.load_current_target * load_variation
        elif self.scenario == "temp_ramp":
            # Continuous high load
            current_drive_target = self.drive_rpm_target
            current_brake_target = self.brake_rpm_target
            current_load_target = self.load_current_target
        else:  # default or steady_state
            # Add some natural variation
            variation = math.sin(self.time_offset / 3000) * 0.1 + 1.0
            current_drive_target = self.drive_rpm_target * variation
            current_brake_target = self.brake_rpm_target * variation
            current_load_target = self.load_current_target * variation
            
        # Simulate RPM response
        self.drive_rpm = self._simulate_rpm_response(self.drive_rpm, current_drive_target)
        self.brake_rpm = self._simulate_rpm_response(self.brake_rpm, current_brake_target)
        
        # Simulate electrical parameters
        drive_voltage = self._add_noise(48.0, 3.0)  # Typical 48V system
        brake_voltage = self._add_noise(48.0, 3.0)
        
        # Current based on load and RPM
        self.drive_current = self._add_noise(
            (self.drive_rpm / 3000) * 30 + random.uniform(2, 8), 5.0
        )
        self.brake_current = self._add_noise(current_load_target, 3.0)
        
        # Calculate power
        mechanical_power = self._calculate_power(
            self.drive_rpm, self.drive_current, drive_voltage
        )
        
        # Simulate temperatures
        drive_power_loss = self.drive_current * drive_voltage * 0.15  # 15% losses
        brake_power_loss = self.brake_current * brake_voltage * 0.15
        
        self.drive_temp_fet = self._simulate_temperature(
            self.drive_temp_fet, drive_power_loss * 0.6
        )
        self.drive_temp_motor = self._simulate_temperature(
            self.drive_temp_motor, drive_power_loss * 0.4
        )
        self.brake_temp_fet = self._simulate_temperature(
            self.brake_temp_fet, brake_power_loss * 0.6
        )
        self.brake_temp_motor = self._simulate_temperature(
            self.brake_temp_motor, brake_power_loss * 0.4
        )
        
        # Generate duty cycles
        drive_duty = min(100.0, (self.drive_current / 50.0) * 100.0)
        brake_duty = min(100.0, (self.brake_current / 50.0) * 100.0)
        
        # Build JSON structure matching DynamometerData expectations
        data = {
            "timestamp": timestamp,
            "drive": {
                "rpm": int(self.drive_rpm),
                "current": round(self.drive_current, 2),
                "voltage": round(drive_voltage, 2),
                "temp_fet": round(self.drive_temp_fet, 1),
                "temp_motor": round(self.drive_temp_motor, 1),
                "duty_cycle": round(drive_duty, 1),
                "data_age": random.randint(50, 150)  # ms
            },
            "brake": {
                "rpm": int(self.brake_rpm),
                "current": round(self.brake_current, 2),
                "voltage": round(brake_voltage, 2),
                "temp_fet": round(self.brake_temp_fet, 1),
                "temp_motor": round(self.brake_temp_motor, 1),
                "duty_cycle": round(brake_duty, 1),
                "data_age": random.randint(50, 150)  # ms
            },
            "dyno": {
                "target_rpm": int(current_drive_target),
                "target_load": round(current_load_target, 2),
                "drive_enabled": self.drive_rpm > 100,
                "brake_enabled": self.brake_current > 5.0,
                "emergency_stop": False,
                "mechanical_power": round(mechanical_power, 3)
            }
        }
        
        return data
        
    def generate_continuous_data(self, duration_seconds: int = 60, interval_ms: int = 200):
        """Generate continuous data stream for specified duration."""
        points = int((duration_seconds * 1000) / interval_ms)
        
        for i in range(points):
            data_point = self.generate_data_point()
            yield data_point
            
            # Simulate real-time delay if running standalone
            if __name__ == "__main__":
                time.sleep(interval_ms / 1000.0)


def main():
    """Main function for standalone usage."""
    scenario = "default"
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
        
    print(f"Generating fake dynamometer data - Scenario: {scenario}")
    print("Press Ctrl+C to stop\n")
    
    generator = FakeDataGenerator(scenario)
    
    try:
        for data_point in generator.generate_continuous_data(duration_seconds=300):  # 5 minutes
            print(json.dumps(data_point, indent=2))
            print("-" * 40)
            
    except KeyboardInterrupt:
        print("\nData generation stopped.")


if __name__ == "__main__":
    main()