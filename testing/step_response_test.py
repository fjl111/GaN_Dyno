"""
Example script demonstrating step response testing functionality.
This script shows how to analyze motor controller step response characteristics.
"""

import sys
import os
import time
import matplotlib.pyplot as plt

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from communication.serial_handler import SerialHandler, CommandInterface
from testing.response_time_test import StepResponseTest
from models.data_model import DynamometerData


def run_step_response_test_example():
    """Example of how to run step response tests."""
    
    print("Step Response Test Example")
    print("=" * 25)
    
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
        
        # Create step response test
        step_test = StepResponseTest(command_interface, data_model)
        
        # Test RPM step response
        print("\nRunning RPM step response test...")
        print("This test will take about 10 seconds...")
        print("Target: 800 RPM step input")
        
        step_result = step_test.run_rpm_step_test(
            target_rpm=800, 
            duration_seconds=10.0, 
            sample_rate_hz=50
        )
        
        print("\nStep Response Test Results:")
        print("-" * 30)
        
        if "error" in step_result:
            print(f"Error: {step_result['error']}")
        else:
            analysis = step_result['analysis']
            if "error" in analysis:
                print(f"Analysis error: {analysis['error']}")
            else:
                print(f"Target RPM: {step_result['target_rpm']}")
                print(f"Initial RPM: {step_result['initial_rpm']}")
                print(f"Final RPM: {analysis['final_value']:.1f}")
                print(f"Rise time: {analysis['rise_time_s']:.3f} s" if analysis['rise_time_s'] else "Rise time: N/A")
                print(f"Settling time: {analysis['settling_time_s']:.3f} s" if analysis['settling_time_s'] else "Settling time: N/A")
                print(f"Overshoot: {analysis['overshoot_percent']:.1f}%")
                print(f"Steady-state error: {analysis['steady_state_error']:.1f} RPM")
            
            # Plot results
            try:
                timestamps = step_result['timestamps']
                rpm_values = step_result['rpm_values']
                target_values = step_result['target_values']
                
                plt.figure(figsize=(10, 6))
                plt.plot(timestamps, rpm_values, 'b-', label='Actual RPM', linewidth=2)
                plt.plot(timestamps, target_values, 'r--', label='Target RPM', linewidth=1)
                plt.xlabel('Time (seconds)')
                plt.ylabel('RPM')
                plt.title('Motor RPM Step Response')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                # Save plot
                filename = f"step_response_{int(time.time())}.png"
                plt.savefig(filename)
                print(f"\nStep response plot saved as: {filename}")
                
                # Show plot (comment out if running headless)
                # plt.show()
                
            except ImportError:
                print("matplotlib not available - skipping plot generation")
            except Exception as e:
                print(f"Error generating plot: {e}")
        
        # Make sure everything is stopped
        command_interface.disable_all()
        
        # Disconnect
        serial_handler.disconnect()
        print("\nDisconnected.")
        
    else:
        print("Failed to connect!")


if __name__ == "__main__":
    run_step_response_test_example()