"""
Matplotlib plotting functionality for visualization of motor controller data.
Handles all real-time chart updates and formatting.
"""

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QVBoxLayout


class DynamometerPlotter:
    """Handles all matplotlib plotting to create graphs of motor controller data."""
    
    def __init__(self, parent_widget):
        self.parent_widget = parent_widget
        self.data_model = None
        
        # Create matplotlib figure
        self.fig, self.axes = plt.subplots(2, 2, figsize=(12, 10))
        self.fig.suptitle('Dynamometer Real-time Monitoring', fontsize=12, fontweight='bold')
        
        # Adjust spacing between subplots
        plt.subplots_adjust(left=0.08, bottom=0.08, right=0.95, top=0.92, wspace=0.3, hspace=0.4)
        
        # Configure subplots
        self.ax_rpm = self.axes[0, 0]
        self.ax_power = self.axes[0, 1]
        self.ax_temp = self.axes[1, 0]
        self.ax_current = self.axes[1, 1]
        
        # Setup plot formatting
        self._setup_plot_formatting()
        
        # Create canvas
        self.canvas = FigureCanvas(self.fig)
        
        # Add canvas to parent widget
        layout = QVBoxLayout(self.parent_widget)
        layout.addWidget(self.canvas)
        
        # Setup animation to update plots
        self.ani = FuncAnimation(self.fig, self.update_plots, interval=200, blit=False)
        
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
        self.ax_rpm.grid(True, alpha=0.3, linestyle='--')
        self.ax_rpm.tick_params(axis='both', which='major', labelsize=tick_fontsize)
        
        # Power plot
        self.ax_power.set_title('Mechanical Power', fontsize=title_fontsize, fontweight='bold')
        self.ax_power.set_ylabel('Power (W)', fontsize=label_fontsize)
        self.ax_power.grid(True, alpha=0.3, linestyle='--')
        self.ax_power.tick_params(axis='both', which='major', labelsize=tick_fontsize)
        
        # Temperature plot
        self.ax_temp.set_title('Temperatures', fontsize=title_fontsize, fontweight='bold')
        self.ax_temp.set_ylabel('Temperature (°C)', fontsize=label_fontsize)
        self.ax_temp.grid(True, alpha=0.3, linestyle='--')
        self.ax_temp.tick_params(axis='both', which='major', labelsize=tick_fontsize)
        
        # Current plot
        self.ax_current.set_title('Current (Drive vs Brake)', fontsize=title_fontsize, fontweight='bold')
        self.ax_current.set_ylabel('Current (A)', fontsize=label_fontsize)
        self.ax_current.grid(True, alpha=0.3, linestyle='--')
        self.ax_current.tick_params(axis='both', which='major', labelsize=tick_fontsize)
        
        
    def update_plots(self, frame):
        """Update all plots with current data."""
        if not self.data_model or not self.data_model.has_data():
            return
            
        # Get plot data
        plot_data = self.data_model.get_plot_data()
        times = plot_data['timestamps']
        
        # Clear all plots
        self.ax_rpm.clear()
        self.ax_power.clear()
        self.ax_temp.clear()
        self.ax_current.clear()
        
        # Font sizes for consistency
        title_fontsize = 9
        label_fontsize = 8
        tick_fontsize = 7
        legend_fontsize = 7
        
        # Plot RPM comparison
        self.ax_rpm.plot(times, plot_data['drive_rpm'], 'b-', linewidth=2.5, label='Drive RPM')
        self.ax_rpm.plot(times, plot_data['brake_rpm'], 'r-', linewidth=2.5, label='Brake RPM')
        self.ax_rpm.set_title('RPM (Drive vs Brake)', fontsize=title_fontsize, fontweight='bold')
        self.ax_rpm.set_ylabel('RPM', fontsize=label_fontsize)
        self.ax_rpm.set_xlabel('Time (s)', fontsize=label_fontsize)
        self.ax_rpm.legend(fontsize=legend_fontsize)
        self.ax_rpm.grid(True, alpha=0.3, linestyle='--')
        self.ax_rpm.tick_params(axis='both', which='major', labelsize=tick_fontsize)
        
        # Plot Power
        self.ax_power.plot(times, plot_data['mechanical_power'], 'r-', linewidth=2.5, label='Power')
        self.ax_power.set_title('Mechanical Power', fontsize=title_fontsize, fontweight='bold')
        self.ax_power.set_ylabel('Power (W)', fontsize=label_fontsize)
        self.ax_power.set_xlabel('Time (s)', fontsize=label_fontsize)
        self.ax_power.grid(True, alpha=0.3, linestyle='--')
        self.ax_power.tick_params(axis='both', which='major', labelsize=tick_fontsize)
        
        # Plot Temperatures
        self.ax_temp.plot(times, plot_data['drive_temp_fet'], 'r-', linewidth=2.5, label='Drive FET')
        self.ax_temp.plot(times, plot_data['drive_temp_motor'], 'orange', linewidth=2.5, label='Drive Motor')
        self.ax_temp.plot(times, plot_data['brake_temp_fet'], 'purple', linewidth=2.5, label='Brake FET')
        self.ax_temp.plot(times, plot_data['brake_temp_motor'], 'brown', linewidth=2.5, label='Brake Motor')
        self.ax_temp.set_title('Temperatures', fontsize=title_fontsize, fontweight='bold')
        self.ax_temp.set_ylabel('Temperature (°C)', fontsize=label_fontsize)
        self.ax_temp.set_xlabel('Time (s)', fontsize=label_fontsize)
        self.ax_temp.legend(fontsize=legend_fontsize)
        self.ax_temp.grid(True, alpha=0.3, linestyle='--')
        self.ax_temp.tick_params(axis='both', which='major', labelsize=tick_fontsize)
        
        # Plot Current comparison
        self.ax_current.plot(times, plot_data['drive_current'], 'g-', linewidth=2.5, label='Drive Current')
        self.ax_current.plot(times, plot_data['brake_current'], 'm-', linewidth=2.5, label='Brake Current')
        self.ax_current.set_title('Current (Drive vs Brake)', fontsize=title_fontsize, fontweight='bold')
        self.ax_current.set_ylabel('Current (A)', fontsize=label_fontsize)
        self.ax_current.set_xlabel('Time (s)', fontsize=label_fontsize)
        self.ax_current.legend(fontsize=legend_fontsize)
        self.ax_current.grid(True, alpha=0.3, linestyle='--')
        self.ax_current.tick_params(axis='both', which='major', labelsize=tick_fontsize)
        
            
        # Apply consistent spacing
        plt.subplots_adjust(left=0.08, bottom=0.08, right=0.95, top=0.92, wspace=0.25, hspace=0.4)
        
        # Refresh canvas
        self.canvas.draw()
        
    def stop_animation(self):
        """Stop the animation."""
        if self.ani:
            self.ani.event_source.stop()
            
    def start_animation(self):
        """Start the animation."""
        if self.ani:
            self.ani.event_source.start()