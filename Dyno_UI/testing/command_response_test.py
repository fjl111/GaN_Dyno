"""
Example script demonstrating command response testing functionality.
This script shows how to measure motor controller response times.
"""

import sys
import os
import time

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Dyno_UI.communication.serial_handler import SerialHandler, CommandInterface
from Dyno_UI.testing.response_time_test import CommandResponseTest
from Dyno_UI.models.data_model import DynamometerData


def run_command_response_test_example():
    """Example of how to run command response tests."""
    
    print("Command Response Time Test Example")
    print("=" * 35)
    
    # Create components
    serial_handler = SerialHandler()
    command_interface = CommandInterface(serial_handler)
    data_model = DynamometerData()
    
    # Setup data callback to update model
    def data_callback(line):
        """Process JSON data from ESP32."""
        try:
            import json
            if line.startswith('{') and line.endswith('}'):
                data = json.loads(line)
                data_model.update_from_json(data)
        except json.JSONDecodeError:
            # Not JSON data, ignore
            pass
    
    def error_callback(error):
        """Handle serial errors."""
        print(f"Serial error: {error}")
    
    # Setup callbacks
    serial_handler.set_callbacks(data_callback, error_callback)
    
    # Get available ports
    ports = serial_handler.get_available_ports()
    print(f"Available ports: {ports}")
    
    if not ports:
        print("No serial ports found!")
        return
    
    # Try to connect to first available port
    port = ports[0]  # You may need to change this to the correct port
    print(f"Attempting to connect to {port}...")
    
    if serial_handler.connect(port):
        print("Connected successfully!")
        
        # Wait for initial data
        print("Waiting for initial data...")
        time.sleep(2)
        
        # Create command response test
        cmd_test = CommandResponseTest(command_interface, data_model)
        
        # Test RPM response
        print("\nTesting RPM response...")
        print("Current RPM:", data_model.current_values['drive']['rpm'])
        
        rpm_result = cmd_test.run_rpm_response_test(target_rpm=500, timeout_seconds=5.0)
        
        print("RPM Test Results:")
        print("-" * 20)
        if "error" in rpm_result:
            print(f"Error: {rpm_result['error']}")
        else:
            print(f"Target RPM: {rpm_result['target_rpm']}")
            print(f"Initial RPM: {rpm_result['initial_rpm']}")
            print(f"Final RPM: {rpm_result['final_rpm']}")
            print(f"Response time: {rpm_result['response_time_ms']:.2f} ms")
        
        time.sleep(2)
        
        # Test Load response
        print("\nTesting Load response...")
        print("Current Load:", data_model.current_values['brake']['current'])
        
        load_result = cmd_test.run_load_response_test(target_load=2.0, timeout_seconds=5.0)
        
        print("Load Test Results:")
        print("-" * 20)
        if "error" in load_result:
            print(f"Error: {load_result['error']}")
        else:
            print(f"Target Load: {load_result['target_load']} A")
            print(f"Initial Current: {load_result['initial_current']} A")
            print(f"Final Current: {load_result['final_current']} A")
            print(f"Response time: {load_result['response_time_ms']:.2f} ms")
        
        # Make sure everything is stopped
        command_interface.disable_all()
        
        # Disconnect
        serial_handler.disconnect()
        print("\nDisconnected.")
        
    else:
        print("Failed to connect!")


if __name__ == "__main__":
    run_command_response_test_example()