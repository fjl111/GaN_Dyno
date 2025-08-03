"""
Response time testing module for dynamometer interface.
Provides comprehensive testing of motor controller response times including
communication latency, motor response characteristics, and statistical analysis.
"""

import time
import statistics
import numpy as np
from datetime import datetime, timedelta
from PyQt5.QtCore import QThread, pyqtSignal
from collections import deque


class PingTest:
    """Tests pure communication latency using PING/PONG commands."""
    
    def __init__(self, command_interface):
        self.command_interface = command_interface
        self.ping_times = []
        self.response_times = []
        
    def run_test(self, iterations=100, delay_between_pings=0.01):
        """
        Run ping test for specified iterations.
        
        Args:
            iterations: Number of ping commands to send
            delay_between_pings: Delay between pings in seconds
            
        Returns:
            dict: Test results with statistics
        """
        self.ping_times.clear()
        self.response_times.clear()
        
        for i in range(iterations):
            # Send ping and record time
            ping_time = time.perf_counter_ns()
            success = self.command_interface.send_raw_command("ping")
            
            if success:
                self.ping_times.append(ping_time)
                
            # Wait between pings
            if delay_between_pings > 0:
                time.sleep(delay_between_pings)
                
        return self._calculate_statistics()
    
    def process_pong_response(self, esp32_timestamp):
        """Process PONG response from ESP32."""
        if self.ping_times:
            # Calculate round-trip time
            current_time = time.perf_counter_ns()
            ping_time = self.ping_times.pop(0)
            rtt_microseconds = (current_time - ping_time) / 1000
            self.response_times.append(rtt_microseconds)
    
    def _calculate_statistics(self):
        """Calculate statistics from response times."""
        if not self.response_times:
            return {"error": "No valid responses received"}
            
        return {
            "test_type": "ping",
            "iterations": len(self.response_times),
            "min_us": min(self.response_times),
            "max_us": max(self.response_times),
            "mean_us": statistics.mean(self.response_times),
            "median_us": statistics.median(self.response_times),
            "stdev_us": statistics.stdev(self.response_times) if len(self.response_times) > 1 else 0,
            "raw_data": self.response_times.copy()
        }


class CommandResponseTest:
    """Tests motor controller response to control commands."""
    
    def __init__(self, command_interface, data_model):
        self.command_interface = command_interface
        self.data_model = data_model
        self.test_results = []
        
    def run_rpm_response_test(self, target_rpm=1000, timeout_seconds=5.0):
        """
        Test RPM command response time.
        
        Args:
            target_rpm: RPM to command
            timeout_seconds: Maximum time to wait for response
            
        Returns:
            dict: Test results with response time
        """
        # Enable drive motor
        self.command_interface.enable_drive()
        time.sleep(0.1)
        
        # Record initial RPM
        initial_rpm = self.data_model.current_values['drive']['rpm']
        
        # Send command and record time
        command_time = time.perf_counter_ns()
        success = self.command_interface.set_drive_speed(target_rpm)
        
        if not success:
            return {"error": "Failed to send command"}
            
        # Wait for RPM change
        start_time = time.perf_counter()
        response_detected = False
        response_time_us = 0
        
        while (time.perf_counter() - start_time) < timeout_seconds:
            current_rpm = self.data_model.current_values['drive']['rpm']
            
            # Detect significant change (>10% of command difference)
            rpm_change = abs(current_rpm - initial_rpm)
            expected_change = abs(target_rpm - initial_rpm)
            
            if expected_change > 0 and rpm_change > (0.1 * expected_change):
                response_time_us = (time.perf_counter_ns() - command_time) / 1000
                response_detected = True
                break
                
            time.sleep(0.001)  # 1ms polling
            
        # Stop motor
        self.command_interface.set_drive_speed(0)
        self.command_interface.disable_all()
        
        if response_detected:
            return {
                "test_type": "rpm_response",
                "target_rpm": target_rpm,
                "initial_rpm": initial_rpm,
                "final_rpm": current_rpm,
                "response_time_us": response_time_us,
                "response_time_ms": response_time_us / 1000
            }
        else:
            return {
                "error": "No response detected within timeout",
                "timeout_seconds": timeout_seconds
            }
    
    def run_load_response_test(self, target_load=1.0, timeout_seconds=5.0):
        """
        Test brake load command response time.
        
        Args:
            target_load: Load current to command (Amps)
            timeout_seconds: Maximum time to wait for response
            
        Returns:
            dict: Test results with response time
        """
        # Enable brake motor
        self.command_interface.enable_brake()
        time.sleep(0.1)
        
        # Record initial current
        initial_current = self.data_model.current_values['brake']['current']
        
        # Send command and record time
        command_time = time.perf_counter_ns()
        success = self.command_interface.set_brake_load(target_load)
        
        if not success:
            return {"error": "Failed to send command"}
            
        # Wait for current change
        start_time = time.perf_counter()
        response_detected = False
        response_time_us = 0
        
        while (time.perf_counter() - start_time) < timeout_seconds:
            current_load = self.data_model.current_values['brake']['current']
            
            # Detect significant change (>10% of command difference)
            load_change = abs(current_load - initial_current)
            expected_change = abs(target_load - initial_current)
            
            if expected_change > 0 and load_change > (0.1 * expected_change):
                response_time_us = (time.perf_counter_ns() - command_time) / 1000
                response_detected = True
                break
                
            time.sleep(0.001)  # 1ms polling
            
        # Stop brake
        self.command_interface.set_brake_load(0.0)
        self.command_interface.disable_all()
        
        if response_detected:
            return {
                "test_type": "load_response",
                "target_load": target_load,
                "initial_current": initial_current,
                "final_current": current_load,
                "response_time_us": response_time_us,
                "response_time_ms": response_time_us / 1000
            }
        else:
            return {
                "error": "No response detected within timeout",
                "timeout_seconds": timeout_seconds
            }


class StepResponseTest:
    """Analyzes motor step response characteristics."""
    
    def __init__(self, command_interface, data_model):
        self.command_interface = command_interface
        self.data_model = data_model
        
    def run_rpm_step_test(self, target_rpm=1000, duration_seconds=10.0, sample_rate_hz=100):
        """
        Run RPM step response test with detailed data collection.
        
        Args:
            target_rpm: Target RPM for step input
            duration_seconds: Test duration
            sample_rate_hz: Data sampling rate
            
        Returns:
            dict: Step response data and analysis
        """
        # Calculate sampling interval
        sample_interval = 1.0 / sample_rate_hz
        
        # Data storage
        timestamps = []
        rpm_values = []
        target_values = []
        
        # Enable drive motor
        self.command_interface.enable_drive()
        time.sleep(0.1)
        
        # Record initial state
        start_time = time.perf_counter()
        initial_rpm = self.data_model.current_values['drive']['rpm']
        
        # Send step command
        command_time = time.perf_counter()
        self.command_interface.set_drive_speed(target_rpm)
        
        # Collect data
        while (time.perf_counter() - start_time) < duration_seconds:
            current_time = time.perf_counter() - start_time
            current_rpm = self.data_model.current_values['drive']['rpm']
            
            timestamps.append(current_time)
            rpm_values.append(current_rpm)
            target_values.append(target_rpm)
            
            time.sleep(sample_interval)
            
        # Stop motor
        self.command_interface.set_drive_speed(0)
        self.command_interface.disable_all()
        
        # Analyze step response
        analysis = self._analyze_step_response(
            timestamps, rpm_values, initial_rpm, target_rpm
        )
        
        return {
            "test_type": "rpm_step_response",
            "target_rpm": target_rpm,
            "initial_rpm": initial_rpm,
            "duration_seconds": duration_seconds,
            "sample_rate_hz": sample_rate_hz,
            "timestamps": timestamps,
            "rpm_values": rpm_values,
            "target_values": target_values,
            "analysis": analysis
        }
    
    def _analyze_step_response(self, timestamps, values, initial_value, target_value):
        """Analyze step response characteristics."""
        if len(values) < 10:
            return {"error": "Insufficient data for analysis"}
            
        # Convert to numpy arrays
        t = np.array(timestamps)
        y = np.array(values)
        
        # Calculate step change
        step_size = target_value - initial_value
        if abs(step_size) < 1:
            return {"error": "Step size too small for analysis"}
            
        # Find response characteristics
        final_value = np.mean(y[-20:])  # Average of last 20 points
        steady_state_error = abs(final_value - target_value)
        
        # Find 10%, 90% rise time points
        threshold_10 = initial_value + 0.1 * step_size
        threshold_90 = initial_value + 0.9 * step_size
        
        rise_start_idx = next((i for i, v in enumerate(y) if abs(v - threshold_10) < abs(step_size * 0.05)), None)
        rise_end_idx = next((i for i, v in enumerate(y) if abs(v - threshold_90) < abs(step_size * 0.05)), None)
        
        rise_time = None
        if rise_start_idx is not None and rise_end_idx is not None and rise_end_idx > rise_start_idx:
            rise_time = t[rise_end_idx] - t[rise_start_idx]
            
        # Find settling time (within 2% of final value)
        settling_threshold = abs(step_size * 0.02)
        settling_idx = None
        
        for i in range(len(y) - 1, -1, -1):
            if abs(y[i] - final_value) > settling_threshold:
                settling_idx = i + 1
                break
                
        settling_time = t[settling_idx] if settling_idx else None
        
        # Find overshoot
        if step_size > 0:
            max_value = np.max(y)
            overshoot = max_value - target_value if max_value > target_value else 0
        else:
            min_value = np.min(y)
            overshoot = target_value - min_value if min_value < target_value else 0
            
        overshoot_percent = (overshoot / abs(step_size)) * 100 if step_size != 0 else 0
        
        return {
            "rise_time_s": rise_time,
            "settling_time_s": settling_time,
            "overshoot": overshoot,
            "overshoot_percent": overshoot_percent,
            "steady_state_error": steady_state_error,
            "final_value": final_value
        }


class ResponseTimeTestThread(QThread):
    """Thread for running response time tests without blocking UI."""
    
    progress_update = pyqtSignal(str)
    test_complete = pyqtSignal(dict)
    
    def __init__(self, test_type, test_params, command_interface, data_model):
        super().__init__()
        self.test_type = test_type
        self.test_params = test_params
        self.command_interface = command_interface
        self.data_model = data_model
        self.running = False
        
    def run(self):
        """Execute the specified test."""
        self.running = True
        
        try:
            if self.test_type == "ping":
                self.progress_update.emit("Running ping test...")
                ping_test = PingTest(self.command_interface)
                result = ping_test.run_test(**self.test_params)
                
            elif self.test_type == "rpm_response":
                self.progress_update.emit("Running RPM response test...")
                cmd_test = CommandResponseTest(self.command_interface, self.data_model)
                result = cmd_test.run_rpm_response_test(**self.test_params)
                
            elif self.test_type == "load_response":
                self.progress_update.emit("Running load response test...")
                cmd_test = CommandResponseTest(self.command_interface, self.data_model)
                result = cmd_test.run_load_response_test(**self.test_params)
                
            elif self.test_type == "rpm_step":
                self.progress_update.emit("Running RPM step response test...")
                step_test = StepResponseTest(self.command_interface, self.data_model)
                result = step_test.run_rpm_step_test(**self.test_params)
                
            else:
                result = {"error": f"Unknown test type: {self.test_type}"}
                
            self.test_complete.emit(result)
            
        except Exception as e:
            self.test_complete.emit({"error": f"Test failed: {str(e)}"})
            
    def stop(self):
        """Stop the test."""
        self.running = False


class ResponseTimeAnalyzer:
    """Analyzes and generates reports from response time test data."""
    
    @staticmethod
    def generate_summary_report(test_results):
        """Generate a summary report from multiple test results."""
        if not test_results:
            return "No test results available."
            
        report = ["Response Time Test Summary", "=" * 30, ""]
        
        for i, result in enumerate(test_results, 1):
            report.append(f"Test {i}: {result.get('test_type', 'Unknown')}")
            
            if "error" in result:
                report.append(f"  Error: {result['error']}")
            else:
                if result.get("test_type") == "ping":
                    report.append(f"  Iterations: {result.get('iterations', 0)}")
                    report.append(f"  Mean latency: {result.get('mean_us', 0):.1f} μs")
                    report.append(f"  Min/Max: {result.get('min_us', 0):.1f}/{result.get('max_us', 0):.1f} μs")
                    
                elif "response_time_us" in result:
                    report.append(f"  Response time: {result['response_time_us']:.1f} μs ({result.get('response_time_ms', 0):.2f} ms)")
                    
                elif result.get("test_type") == "rpm_step_response":
                    analysis = result.get("analysis", {})
                    if "error" not in analysis:
                        report.append(f"  Rise time: {analysis.get('rise_time_s', 0):.3f} s")
                        report.append(f"  Settling time: {analysis.get('settling_time_s', 0):.3f} s")
                        report.append(f"  Overshoot: {analysis.get('overshoot_percent', 0):.1f}%")
                        
            report.append("")
            
        return "\n".join(report)
    
    @staticmethod
    def export_to_csv(test_results, filename):
        """Export test results to CSV file."""
        import csv
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['Timestamp', 'Test Type', 'Parameter', 'Value', 'Units'])
            
            timestamp = datetime.now().isoformat()
            
            for result in test_results:
                test_type = result.get('test_type', 'Unknown')
                
                if result.get('test_type') == 'ping' and 'raw_data' in result:
                    for i, rtt in enumerate(result['raw_data']):
                        writer.writerow([timestamp, test_type, f'RTT_{i}', rtt, 'microseconds'])
                        
                elif 'response_time_us' in result:
                    writer.writerow([timestamp, test_type, 'response_time', result['response_time_us'], 'microseconds'])
                    
                # Add more export formats as needed
                
        return f"Results exported to {filename}"