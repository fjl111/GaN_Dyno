"""
3D plotting widget for visualizing sweep test results.
Provides 3D surface plots for temperature and power vs speed/amperage.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
# Try to import scipy for interpolation, fallback to simple plotting if not available
try:
    from scipy.interpolate import griddata
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QComboBox, QLabel, QFileDialog, QMessageBox, QSizePolicy)
from PyQt5.QtCore import pyqtSignal
import os
from datetime import datetime


class Plot3DWidget(QWidget):
    """Widget for displaying 3D plots of sweep test data."""
    
    plot_exported = pyqtSignal(str)  # Emitted when plot is exported
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sweep_data = []
        self.current_plot_type = "temperature"
        self.setup_ui()
        
    def setup_ui(self):
        """Create the 3D plot widget UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Controls layout
        controls_layout = QHBoxLayout()
        
        # Plot type selection
        controls_layout.addWidget(QLabel("Plot Type:"))
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems([
            "Temperature vs Speed & Amperage",
            "Power vs Speed & Amperage"
        ])
        self.plot_type_combo.currentTextChanged.connect(self._on_plot_type_changed)
        controls_layout.addWidget(self.plot_type_combo)
        
        controls_layout.addStretch()
        
        # Control buttons
        self.refresh_button = QPushButton("Refresh Plot")
        self.refresh_button.clicked.connect(self.update_plot)
        controls_layout.addWidget(self.refresh_button)
        
        self.export_button = QPushButton("Export Plot")
        self.export_button.clicked.connect(self.export_plot)
        controls_layout.addWidget(self.export_button)
        
        self.export_data_button = QPushButton("Export Data")
        self.export_data_button.clicked.connect(self.export_data)
        controls_layout.addWidget(self.export_data_button)
        
        main_layout.addLayout(controls_layout)
        
        # Create matplotlib figure for 3D plotting
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.canvas)
        
        # Initialize with empty plot
        self._create_empty_plot()
        
    def _create_empty_plot(self):
        """Create an empty 3D plot with placeholder text."""
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection='3d')
        ax.text(0.5, 0.5, 0.5, 'No 3D sweep data available\nRun a 3D sweep test to see plots', 
                transform=ax.transAxes, ha='center', va='center', fontsize=14)
        ax.set_xlabel('RPM')
        ax.set_ylabel('Amperage (A)')
        ax.set_zlabel('Value')
        ax.set_title('3D Sweep Data Visualization')
        self.canvas.draw()
        
    def _on_plot_type_changed(self, plot_type):
        """Handle plot type change."""
        if "Temperature" in plot_type:
            self.current_plot_type = "temperature"
        elif "Power" in plot_type:
            self.current_plot_type = "power"
        self.update_plot()
        
    def set_sweep_data(self, sweep_data):
        """Set the sweep data to plot."""
        self.sweep_data = sweep_data
        self.update_plot()
        
    def update_plot(self):
        """Update the 3D plot with current data and settings."""
        if not self.sweep_data:
            self._create_empty_plot()
            return
            
        try:
            # Extract data for plotting
            rpm_values = [d['target_rpm'] for d in self.sweep_data]
            amperage_values = [d['target_amperage'] for d in self.sweep_data]
            
            if self.current_plot_type == "temperature":
                z_values = [d['max_temp_fet'] for d in self.sweep_data]  # Use max FET temperature
                z_label = 'Temperature (°C)'
                title = 'FET Temperature vs Speed & Amperage'
                colormap = 'coolwarm'
            else:  # power
                z_values = [d['total_power'] for d in self.sweep_data]
                z_label = 'Power (W)'
                title = 'Total Power vs Speed & Amperage'
                colormap = 'viridis'
                
            # Clear figure and create 3D subplot
            self.figure.clear()
            ax = self.figure.add_subplot(111, projection='3d')
            
            # Create grid for surface plot
            rpm_unique = sorted(list(set(rpm_values)))
            amp_unique = sorted(list(set(amperage_values)))
            
            if len(rpm_unique) < 2 or len(amp_unique) < 2 or not SCIPY_AVAILABLE:
                # Not enough data points for surface plot or scipy not available, use scatter plot
                scatter = ax.scatter(rpm_values, amperage_values, z_values, 
                                   c=z_values, cmap=colormap, s=50, alpha=0.8)
                self.figure.colorbar(scatter, ax=ax, shrink=0.8)
                
                if not SCIPY_AVAILABLE:
                    # Add note about missing scipy
                    ax.text(0.02, 0.98, 'Note: Install scipy for surface plots', 
                           transform=ax.transAxes, fontsize=8, color='red', 
                           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            else:
                # Create meshgrid for surface plot
                RPM, AMP = np.meshgrid(rpm_unique, amp_unique)
                
                # Interpolate z values onto grid
                Z = griddata((rpm_values, amperage_values), z_values, (RPM, AMP), method='linear')
                
                # Create surface plot
                surface = ax.plot_surface(RPM, AMP, Z, cmap=colormap, alpha=0.8, 
                                        linewidth=0, antialiased=True)
                
                # Add colorbar
                self.figure.colorbar(surface, ax=ax, shrink=0.8)
                
                # Also add scatter points for actual data
                ax.scatter(rpm_values, amperage_values, z_values, 
                          c='red', s=20, alpha=1.0, label='Data Points')
                ax.legend()
                
            # Set labels and title
            ax.set_xlabel('RPM', fontsize=12)
            ax.set_ylabel('Amperage (A)', fontsize=12)
            ax.set_zlabel(z_label, fontsize=12)
            ax.set_title(title, fontsize=14, fontweight='bold')
            
            # Improve the viewing angle
            ax.view_init(elev=20, azim=45)
            
            # Add grid
            ax.grid(True, alpha=0.3)
            
            # Tight layout
            self.figure.tight_layout()
            
        except Exception as e:
            # If plotting fails, show error message
            self.figure.clear()
            ax = self.figure.add_subplot(111, projection='3d')
            ax.text(0.5, 0.5, 0.5, f'Error creating 3D plot:\n{str(e)}', 
                    transform=ax.transAxes, ha='center', va='center', fontsize=12, color='red')
            ax.set_xlabel('RPM')
            ax.set_ylabel('Amperage (A)')
            ax.set_zlabel('Value')
            ax.set_title('3D Plot Error')
            
        # Refresh canvas
        self.canvas.draw()
        
    def export_plot(self):
        """Export the current plot as an image file."""
        if not self.sweep_data:
            QMessageBox.warning(self, "Warning", "No data to export")
            return
            
        # Generate default filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_type = "temperature" if self.current_plot_type == "temperature" else "power"
        default_filename = f"dyno_3d_{plot_type}_plot_{timestamp}.png"
        
        # Get save location from user
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Export 3D Plot",
            default_filename,
            "PNG files (*.png);;PDF files (*.pdf);;SVG files (*.svg);;All files (*.*)"
        )
        
        if filename:
            try:
                # Save the figure
                self.figure.savefig(filename, dpi=300, bbox_inches='tight', 
                                  facecolor='white', edgecolor='none')
                
                QMessageBox.information(self, "Success", f"Plot exported to {filename}")
                self.plot_exported.emit(filename)
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export plot: {str(e)}")
                
    def export_data(self):
        """Export the raw sweep data as CSV."""
        if not self.sweep_data:
            QMessageBox.warning(self, "Warning", "No data to export")
            return
            
        # Generate default filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"dyno_3d_sweep_data_{timestamp}.csv"
        
        # Get save location from user
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Export 3D Sweep Data",
            default_filename,
            "CSV files (*.csv);;All files (*.*)"
        )
        
        if filename:
            try:
                # Import csv here to avoid import at module level
                import csv
                
                # Define fieldnames
                fieldnames = [
                    'target_rpm', 'target_amperage', 'actual_rpm', 'actual_amperage',
                    'total_power', 'drive_power', 'brake_power',
                    'max_temp_fet', 'max_temp_motor', 'drive_temp_fet', 'drive_temp_motor',
                    'brake_temp_fet', 'brake_temp_motor', 'drive_voltage', 'brake_voltage'
                ]
                
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    # Write metadata comments
                    csvfile.write(f"# 3D Sweep Data Export\n")
                    csvfile.write(f"# Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    csvfile.write(f"# Total Data Points: {len(self.sweep_data)}\n")
                    
                    # Write data
                    for data_point in self.sweep_data:
                        # Filter to only include fields that exist
                        filtered_point = {k: data_point.get(k, 0) for k in fieldnames}
                        writer.writerow(filtered_point)
                
                QMessageBox.information(self, "Success", f"Data exported to {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export data: {str(e)}")
                
    def clear_plot(self):
        """Clear the plot and reset to empty state."""
        self.sweep_data = []
        self._create_empty_plot()
        
    def get_data_summary(self):
        """Get a summary of the current data."""
        if not self.sweep_data:
            return "No data"
            
        rpm_values = [d['target_rpm'] for d in self.sweep_data]
        amp_values = [d['target_amperage'] for d in self.sweep_data]
        
        return (f"{len(self.sweep_data)} data points\n"
                f"RPM range: {min(rpm_values):.0f} - {max(rpm_values):.0f}\n"
                f"Amperage range: {min(amp_values):.2f} - {max(amp_values):.2f} A")
        
    def set_enabled(self, enabled):
        """Enable/disable the widget."""
        self.plot_type_combo.setEnabled(enabled)
        self.refresh_button.setEnabled(enabled)
        self.export_button.setEnabled(enabled and bool(self.sweep_data))
        self.export_data_button.setEnabled(enabled and bool(self.sweep_data))