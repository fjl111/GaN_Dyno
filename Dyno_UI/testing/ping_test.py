"""
Example script demonstrating PING test functionality.
This script shows how to use the response time testing system.
"""

import sys
import os
import time

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Dyno_UI.communication.serial_handler import SerialHandler, CommandInterface
from Dyno_UI.testing.response_time_test import PingTest


def run_ping_test_example():
    """Example of how to run a ping test."""
    
    print("Response Time Test Example")
    print("=" * 30)
    
    # Create serial handler and command interface
    serial_handler = SerialHandler()
    command_interface = CommandInterface(serial_handler)
    
    # Setup PONG callback for ping test
    ping_test = PingTest(command_interface)
    
    def pong_callback(esp32_timestamp):
        """Handle PONG responses from ESP32."""
        ping_test.process_pong_response(esp32_timestamp)
        print(f"Received PONG with timestamp: {esp32_timestamp}")
    
    def ack_callback(command, receive_time, send_time, ack_time):
        """Handle ACK responses from ESP32."""
        print(f"Command ACK - {command}: recv={receive_time}, send={send_time}, ack={ack_time}")
    
    # Set timing callbacks
    serial_handler.set_timing_callbacks(pong_callback, ack_callback)
    
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
        
        # Enable timing mode
        print("Enabling timing mode...")
        command_interface.enable_timing_mode()
        time.sleep(0.1)
        
        # Run ping test
        print("Running ping test (10 iterations)...")
        result = ping_test.run_test(iterations=10, delay_between_pings=0.1)
        
        # Print results
        print("\nPing Test Results:")
        print("-" * 20)
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Iterations: {result['iterations']}")
            print(f"Mean latency: {result['mean_us']:.1f} μs")
            print(f"Min latency: {result['min_us']:.1f} μs")
            print(f"Max latency: {result['max_us']:.1f} μs")
            print(f"Std deviation: {result['stdev_us']:.1f} μs")
        
        # Disable timing mode
        command_interface.disable_timing_mode()
        
        # Disconnect
        serial_handler.disconnect()
        print("Disconnected.")
        
    else:
        print("Failed to connect!")


if __name__ == "__main__":
    run_ping_test_example()