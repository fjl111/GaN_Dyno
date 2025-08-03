"""
Serial communication handler for ESP32 dyno interface.
Handles USB serial communication and command/response parsing.
"""

import json
import serial
import serial.tools.list_ports
from PyQt5.QtCore import QThread, pyqtSignal


class SerialThread(QThread):
    """Thread for reading serial data from ESP32."""
    
    data_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, port, baudrate=115200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.running = False
        self.serial_connection = None
        
    def run(self):
        """Main thread loop for reading serial data."""
        try:
            self.serial_connection = serial.Serial(self.port, self.baudrate, timeout=1)
            self.running = True
            
            while self.running:
                if self.serial_connection and self.serial_connection.in_waiting:
                    try:
                        line = self.serial_connection.readline().decode('utf-8').strip()
                        if line:
                            self.data_received.emit(line)
                    except Exception as e:
                        self.error_occurred.emit(f"Read error: {str(e)}")
                        break
                        
        except Exception as e:
            self.error_occurred.emit(f"Connection error: {str(e)}")
            
    def stop(self):
        """Stop the serial thread."""
        self.running = False
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            
    def send_command(self, command):
        """Send a command to the ESP32."""
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.write(f"{command}\n".encode())
                return True
            except Exception as e:
                self.error_occurred.emit(f"Send error: {str(e)}")
                return False
        return False


class SerialHandler:
    """High-level serial communication handler."""
    
    def __init__(self):
        self.serial_thread = None
        self.connected = False
        self.data_callback = None
        self.error_callback = None
        self.pong_callback = None
        self.ack_callback = None
        
    def set_callbacks(self, data_callback, error_callback):
        """Set callback functions for data and errors."""
        self.data_callback = data_callback
        self.error_callback = error_callback
        
    def set_timing_callbacks(self, pong_callback, ack_callback):
        """Set callback functions for timing responses."""
        self.pong_callback = pong_callback
        self.ack_callback = ack_callback
        
    def get_available_ports(self):
        """Get list of available serial ports."""
        return [port.device for port in serial.tools.list_ports.comports()]
        
    def connect(self, port, baudrate=115200):
        """Connect to ESP32 on specified port."""
        if self.connected:
            return False
            
        try:
            self.serial_thread = SerialThread(port, baudrate)
            
            if self.data_callback:
                self.serial_thread.data_received.connect(self._process_received_data)
            if self.error_callback:
                self.serial_thread.error_occurred.connect(self.error_callback)
                
            self.serial_thread.start()
            self.connected = True
            return True
            
        except Exception as e:
            if self.error_callback:
                self.error_callback(f"Connection failed: {str(e)}")
            return False
            
    def disconnect(self):
        """Disconnect from ESP32."""
        self.connected = False
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread.wait()
            self.serial_thread = None
            
    def send_command(self, command):
        """Send a command to ESP32."""
        if self.connected and self.serial_thread:
            return self.serial_thread.send_command(command)
        return False
        
    def is_connected(self):
        """Check if connected to ESP32."""
        return self.connected
        
    def _process_received_data(self, line):
        """Process received data and route to appropriate callbacks."""
        if line.startswith("PONG:"):
            # Handle PONG response
            if self.pong_callback:
                try:
                    timestamp = int(line.split(":")[1])
                    self.pong_callback(timestamp)
                except (IndexError, ValueError):
                    pass
        elif line.startswith("ACK:"):
            # Handle command acknowledgment
            if self.ack_callback:
                try:
                    parts = line.split(":")
                    if len(parts) >= 5:
                        command = parts[1]
                        receive_time = int(parts[2])
                        send_time = int(parts[3])
                        ack_time = int(parts[4])
                        self.ack_callback(command, receive_time, send_time, ack_time)
                except (IndexError, ValueError):
                    pass
        else:
            # Regular data - pass to main data callback
            if self.data_callback:
                self.data_callback(line)


class CommandInterface:
    """Interface for sending commands to ESP32."""
    
    def __init__(self, serial_handler):
        self.serial_handler = serial_handler
        
    def set_drive_speed(self, rpm):
        """Set drive motor speed in RPM."""
        return self.serial_handler.send_command(f"speed {int(rpm)}")
        
    def set_brake_load(self, current):
        """Set brake motor load current in Amps."""
        return self.serial_handler.send_command(f"load {float(current)}")
        
    def enable_drive(self):
        """Enable drive motor."""
        return self.serial_handler.send_command("enable_drive")
        
    def enable_brake(self):
        """Enable brake motor."""
        return self.serial_handler.send_command("enable_brake")
        
    def disable_all(self):
        """Disable all motors."""
        return self.serial_handler.send_command("disable_all")
        
    def emergency_stop(self):
        """Trigger emergency stop."""
        return self.serial_handler.send_command("estop")
        
    def send_raw_command(self, command):
        """Send raw command to ESP32."""
        return self.serial_handler.send_command(command)
        
    def enable_timing_mode(self):
        """Enable timing mode on ESP32."""
        return self.serial_handler.send_command("timing_on")
        
    def disable_timing_mode(self):
        """Disable timing mode on ESP32."""
        return self.serial_handler.send_command("timing_off")
        
    def send_ping(self):
        """Send ping command to ESP32."""
        return self.serial_handler.send_command("ping")


class DataParser:
    """Parser for ESP32 JSON data responses."""
    
    @staticmethod
    def parse_line(line):
        """Parse a line of data from ESP32."""
        # Try to parse as JSON
        if line.startswith('{') and line.endswith('}'):
            try:
                return json.loads(line), True
            except json.JSONDecodeError:
                return line, False
        else:
            return line, False
            
    @staticmethod
    def validate_data(data):
        """Validate that received data has expected structure."""
        if not isinstance(data, dict):
            return False
            
        required_sections = ['drive', 'brake', 'dyno']
        for section in required_sections:
            if section not in data:
                return False
                
        return True