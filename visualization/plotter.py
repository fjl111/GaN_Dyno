"""
Matplotlib plotting functionality for visualization of motor controller data.
Handles all real-time chart updates and formatting.
"""

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtCore import QTimer
import numpy as np
try:
    import mplcursors
    MPLCURSORS_AVAILABLE = True
except ImportError:
    MPLCURSORS_AVAILABLE = False


class DynamometerPlotter:
    """Handles all matplotlib plotting to create graphs of motor controller data."""
    
    def __init__(self, parent_widget):
        self.parent_widget = parent_widget
        self.data_model = None
        
        # Interactive features settings
        self.time_range_seconds = 120  # Show last 120 seconds by default (matches slider default)
        self.auto_scroll = True
        self.update_interval = 10  # 100 FPS hard-coded
        
        # Create matplotlib figure
        self.fig, self.axes = plt.subplots(2, 2, figsize=(12, 10))
        self.fig.suptitle('Dynamometer Real-time Monitoring', fontsize=12, fontweight='bold')
        
        # Adjust spacing between subplots
        plt.subplots_adjust(left=0.08, bottom=0.12, right=0.95, top=0.92, wspace=0.3, hspace=0.4)
        
        # Configure subplots
        self.ax_rpm = self.axes[0, 0]
        self.ax_power = self.axes[0, 1]
        self.ax_temp = self.axes[1, 0]
        self.ax_current = self.axes[1, 1]
        
        # Setup plot formatting and initialize line objects
        self._setup_plot_formatting()
        self._initialize_line_objects()
        
        # Create canvas
        self.canvas = FigureCanvas(self.fig)
        
        # Add canvas to parent widget
        layout = QVBoxLayout(self.parent_widget)
        layout.addWidget(self.canvas)
        
        # Setup interactive features
        self._setup_interactive_features()
        
        # Setup high-performance timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(self.update_interval)
        
    def set_data_model(self, data_model):
        """Set the data model to plot from."""
        self.data_model = data_model
        
    def _setup_plot_formatting(self):
        """Setup consistent formatting for all plots."""
        # Set font sizes for better readability
        title_fontsize = 9
        label_fontsize = 8
        tick_fontsize = 7
        
        # RPM plot
        self.ax_rpm.set_title('RPM (Drive vs Brake)', fontsize=title_fontsize, fontweight='bold')
        self.ax_rpm.set_ylabel('RPM', fontsize=label_fontsize)
        self.ax_rpm.set_xlabel('Time (s)', fontsize=label_fontsize)
        self.ax_rpm.grid(True, alpha=0.3, linestyle='--')
        self.ax_rpm.tick_params(axis='both', which='major', labelsize=tick_fontsize)
        
        # Power plot
        self.ax_power.set_title('Power', fontsize=title_fontsize, fontweight='bold')
        self.ax_power.set_ylabel('Power (W)', fontsize=label_fontsize)
        self.ax_power.set_xlabel('Time (s)', fontsize=label_fontsize)
        self.ax_power.grid(True, alpha=0.3, linestyle='--')
        self.ax_power.tick_params(axis='both', which='major', labelsize=tick_fontsize)
        
        # Temperature plot
        self.ax_temp.set_title('Temperatures', fontsize=title_fontsize, fontweight='bold')
        self.ax_temp.set_ylabel('Temperature (°C)', fontsize=label_fontsize)
        self.ax_temp.set_xlabel('Time (s)', fontsize=label_fontsize)
        self.ax_temp.grid(True, alpha=0.3, linestyle='--')
        self.ax_temp.tick_params(axis='both', which='major', labelsize=tick_fontsize)
        
        # Current plot
        self.ax_current.set_title('Current (Drive vs Brake)', fontsize=title_fontsize, fontweight='bold')
        self.ax_current.set_ylabel('Current (A)', fontsize=label_fontsize)
        self.ax_current.set_xlabel('Time (s)', fontsize=label_fontsize)
        self.ax_current.grid(True, alpha=0.3, linestyle='--')
        self.ax_current.tick_params(axis='both', which='major', labelsize=tick_fontsize)
        
    def _initialize_line_objects(self):
        """Initialize line objects for efficient updates."""
        # Initialize empty line objects for each data series
        self.rpm_drive_line, = self.ax_rpm.plot([], [], 'b-', linewidth=2.5, label='Drive RPM')
        self.rpm_brake_line, = self.ax_rpm.plot([], [], 'r-', linewidth=2.5, label='Brake RPM')
        self.ax_rpm.legend(fontsize=7)
        
        self.drive_power_line, = self.ax_power.plot([], [], 'b-', linewidth=2.5, label='Drive Power')
        self.brake_power_line, = self.ax_power.plot([], [], 'r-', linewidth=2.5, label='Brake Power')
        self.ax_power.legend(fontsize=7)
        
        self.temp_drive_fet_line, = self.ax_temp.plot([], [], 'r-', linewidth=2.5, label='Drive FET')
        self.temp_drive_motor_line, = self.ax_temp.plot([], [], 'orange', linewidth=2.5, label='Drive Motor')
        self.temp_brake_fet_line, = self.ax_temp.plot([], [], 'purple', linewidth=2.5, label='Brake FET')
        self.temp_brake_motor_line, = self.ax_temp.plot([], [], 'brown', linewidth=2.5, label='Brake Motor')
        self.ax_temp.legend(fontsize=7)
        
        self.current_drive_line, = self.ax_current.plot([], [], 'g-', linewidth=2.5, label='Drive Current')
        self.current_brake_line, = self.ax_current.plot([], [], 'm-', linewidth=2.5, label='Brake Current')
        self.ax_current.legend(fontsize=7)
        
        # Store all line objects for easy access
        self.all_lines = [
            self.rpm_drive_line, self.rpm_brake_line, self.drive_power_line, self.brake_power_line,
            self.temp_drive_fet_line, self.temp_drive_motor_line, 
            self.temp_brake_fet_line, self.temp_brake_motor_line,
            self.current_drive_line, self.current_brake_line
        ]
        
    def _setup_interactive_features(self):
        """Setup interactive features like tooltips."""
        # Add hover tooltips if mplcursors is available
        if MPLCURSORS_AVAILABLE:
            self.cursor_annotations = []
            for line in self.all_lines:
                cursor = mplcursors.cursor(line, hover=True)
                cursor.connect("add", self._on_hover)
                self.cursor_annotations.append(cursor)
                
    def _on_hover(self, sel):
        """Handle hover tooltip display."""
        # Get the line that was hovered over
        line = sel.artist
        x, y = sel.target
        
        # Format tooltip based on which line was hovered
        if line == self.rpm_drive_line:
            text = f"Drive RPM\nTime: {x:.1f}s\nRPM: {y:.0f}"
        elif line == self.rpm_brake_line:
            text = f"Brake RPM\nTime: {x:.1f}s\nRPM: {y:.0f}"
        elif line == self.drive_power_line:
            text = f"Drive Power\nTime: {x:.1f}s\nPower: {y:.1f}W"
        elif line == self.brake_power_line:
            text = f"Brake Power\nTime: {x:.1f}s\nPower: {y:.1f}W"
        elif line == self.temp_drive_fet_line:
            text = f"Drive FET Temp\nTime: {x:.1f}s\nTemp: {y:.1f}°C"
        elif line == self.temp_drive_motor_line:
            text = f"Drive Motor Temp\nTime: {x:.1f}s\nTemp: {y:.1f}°C"
        elif line == self.temp_brake_fet_line:
            text = f"Brake FET Temp\nTime: {x:.1f}s\nTemp: {y:.1f}°C"
        elif line == self.temp_brake_motor_line:
            text = f"Brake Motor Temp\nTime: {x:.1f}s\nTemp: {y:.1f}°C"
        elif line == self.current_drive_line:
            text = f"Drive Current\nTime: {x:.1f}s\nCurrent: {y:.2f}A"
        elif line == self.current_brake_line:
            text = f"Brake Current\nTime: {x:.1f}s\nCurrent: {y:.2f}A"
        else:
            text = f"Time: {x:.1f}s\nValue: {y:.2f}"
            
        sel.annotation.set_text(text)
        
    def update_plots(self):
        """Update all plots with current data using efficient line updates."""
        if not self.data_model or not self.data_model.has_data():
            return
            
        # Get plot data - use database for longer time ranges
        use_database = self.time_range_seconds > 0 and self.time_range_seconds > 100  # Use DB for >100s
        
        if use_database and self.auto_scroll:
            # Get data from database for the specified time range
            plot_data = self.data_model.get_plot_data(time_range_seconds=self.time_range_seconds)
        else:
            # Use in-memory data for short ranges or manual scrolling
            plot_data = self.data_model.get_plot_data()
        
        times = np.array(plot_data['timestamps'])
        
        # Apply time range filter if not showing all data and not using database
        if self.time_range_seconds > 0 and len(times) > 0 and not use_database:
            if self.auto_scroll:
                # Show last N seconds
                max_time = times[-1]
                min_time = max_time - self.time_range_seconds
                mask = times >= min_time
            else:
                # Use current axis limits (user may have zoomed/panned)
                xlim = self.ax_rpm.get_xlim()
                mask = (times >= xlim[0]) & (times <= xlim[1])
                
            # Apply filter to all data
            if np.any(mask):
                times = times[mask]
                filtered_data = {}
                for key, values in plot_data.items():
                    if key != 'timestamps':
                        filtered_data[key] = np.array(values)[mask]
            else:
                return  # No data in range
        else:
            filtered_data = {key: np.array(values) for key, values in plot_data.items() if key != 'timestamps'}
            
        # Update line data efficiently
        self.rpm_drive_line.set_data(times, filtered_data['drive_rpm'])
        self.rpm_brake_line.set_data(times, filtered_data['brake_rpm'])
        self.drive_power_line.set_data(times, filtered_data['drive_power'])
        self.brake_power_line.set_data(times, filtered_data['brake_power'])
        self.temp_drive_fet_line.set_data(times, filtered_data['drive_temp_fet'])
        self.temp_drive_motor_line.set_data(times, filtered_data['drive_temp_motor'])
        self.temp_brake_fet_line.set_data(times, filtered_data['brake_temp_fet'])
        self.temp_brake_motor_line.set_data(times, filtered_data['brake_temp_motor'])
        self.current_drive_line.set_data(times, filtered_data['drive_current'])
        self.current_brake_line.set_data(times, filtered_data['brake_current'])
        
        # Auto-scale axes if in auto-scroll mode
        if self.auto_scroll and len(times) > 0:
            # Update x-axis limits
            for ax in [self.ax_rpm, self.ax_power, self.ax_temp, self.ax_current]:
                ax.set_xlim(times[0], times[-1])
                
            # Update y-axis limits with some padding
            self._update_y_limits(filtered_data)
        elif len(times) > 0:
            # If not auto-scrolling, just ensure data is visible
            for ax in [self.ax_rpm, self.ax_power, self.ax_temp, self.ax_current]:
                if ax.get_xlim()[1] < times[-1]:
                    # Extend x-axis if new data goes beyond current view
                    ax.set_xlim(ax.get_xlim()[0], times[-1])
            
        # Refresh canvas
        self.canvas.draw_idle()
            
    def _update_y_limits(self, data):
        """Update y-axis limits with appropriate padding."""
        padding_factor = 0.05  # 5% padding
        
        # RPM plot
        rpm_data = np.concatenate([data['drive_rpm'], data['brake_rpm']])
        if len(rpm_data) > 0:
            rpm_min, rpm_max = np.min(rpm_data), np.max(rpm_data)
            rpm_range = rpm_max - rpm_min
            self.ax_rpm.set_ylim(rpm_min - rpm_range * padding_factor, 
                               rpm_max + rpm_range * padding_factor)
                               
        # Power plot
        if len(data['drive_power']) > 0 or len(data['brake_power']) > 0:
            all_power_values = []
            if len(data['drive_power']) > 0:
                all_power_values.extend(data['drive_power'])
            if len(data['brake_power']) > 0:
                all_power_values.extend(data['brake_power'])
            
            if all_power_values:
                power_min, power_max = np.min(all_power_values), np.max(all_power_values)
                power_range = power_max - power_min
                self.ax_power.set_ylim(power_min - power_range * padding_factor,
                                     power_max + power_range * padding_factor)
                                 
        # Temperature plot
        temp_data = np.concatenate([data['drive_temp_fet'], data['drive_temp_motor'],
                                  data['brake_temp_fet'], data['brake_temp_motor']])
        if len(temp_data) > 0:
            temp_min, temp_max = np.min(temp_data), np.max(temp_data)
            temp_range = temp_max - temp_min
            self.ax_temp.set_ylim(temp_min - temp_range * padding_factor,
                                temp_max + temp_range * padding_factor)
                                
        # Current plot
        current_data = np.concatenate([data['drive_current'], data['brake_current']])
        if len(current_data) > 0:
            current_min, current_max = np.min(current_data), np.max(current_data)
            current_range = current_max - current_min
            self.ax_current.set_ylim(current_min - current_range * padding_factor,
                                   current_max + current_range * padding_factor)
        
    def stop_animation(self):
        """Stop the animation."""
        self.timer.stop()
            
    def start_animation(self):
        """Start the animation."""
        self.timer.start(self.update_interval)
        
    def set_time_range(self, seconds):
        """Set the time range to display in seconds (0 = show all)."""
        self.time_range_seconds = seconds
        
    def set_auto_scroll(self, enabled):
        """Enable/disable auto-scrolling to follow latest data."""
        self.auto_scroll = enabled
        
    def reset_zoom(self):
        """Reset all axes to auto-scale."""
        for ax in [self.ax_rpm, self.ax_power, self.ax_temp, self.ax_current]:
            ax.relim()
            ax.autoscale()
        self.canvas.draw()
        
    def get_performance_stats(self):
        """Get current performance statistics."""
        return {
            'update_interval_ms': self.update_interval,
            'time_range_seconds': self.time_range_seconds,
            'auto_scroll': self.auto_scroll,
            'mplcursors_available': MPLCURSORS_AVAILABLE
        }