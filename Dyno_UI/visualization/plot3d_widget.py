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
        
        self.import_data_button = QPushButton("Import CSV")
        self.import_data_button.clicked.connect(self.import_csv_data)
        controls_layout.addWidget(self.import_data_button)
        
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
            
            # Create a plane surface from the data
            if len(rpm_values) >= 3 and SCIPY_AVAILABLE:
                # Use all available data to create a smooth plane surface
                rpm_min, rpm_max = min(rpm_values), max(rpm_values)
                amp_min, amp_max = min(amperage_values), max(amperage_values)
                
                # Create a fine grid for smooth plane
                rpm_range = np.linspace(rpm_min, rpm_max, 50)
                amp_range = np.linspace(amp_min, amp_max, 50)
                RPM, AMP = np.meshgrid(rpm_range, amp_range)
                
                # Interpolate z values onto the fine grid to create plane
                Z = griddata((rpm_values, amperage_values), z_values, (RPM, AMP), method='linear')
                
                # Fill NaN values with nearest neighbor interpolation for complete plane
                mask = np.isnan(Z)
                if np.any(mask):
                    Z_nearest = griddata((rpm_values, amperage_values), z_values, (RPM, AMP), method='nearest')
                    Z[mask] = Z_nearest[mask]
                
                # Create smooth surface plane
                surface = ax.plot_surface(RPM, AMP, Z, cmap=colormap, alpha=0.7, 
                                        linewidth=0, antialiased=True, shade=True)
                
                # Add colorbar
                self.figure.colorbar(surface, ax=ax, shrink=0.8)
                
                # Add scatter points for actual data on top of plane
                ax.scatter(rpm_values, amperage_values, z_values, 
                          c='red', s=30, alpha=1.0, label='Data Points', edgecolors='black', linewidth=0.5)
                ax.legend()
                
            else:
                # Fallback: Create a basic plane using linear regression if scipy not available
                # or insufficient data points
                if len(rpm_values) >= 3:
                    # Fit a plane using least squares
                    A = np.column_stack([rpm_values, amperage_values, np.ones(len(rpm_values))])
                    coeffs, _, _, _ = np.linalg.lstsq(A, z_values, rcond=None)
                    
                    # Create plane grid
                    rpm_min, rpm_max = min(rpm_values), max(rpm_values)
                    amp_min, amp_max = min(amperage_values), max(amperage_values)
                    
                    # Extend range slightly for better visualization
                    rpm_range_ext = (rpm_max - rpm_min) * 0.1
                    amp_range_ext = (amp_max - amp_min) * 0.1
                    
                    rpm_plane = np.linspace(rpm_min - rpm_range_ext, rpm_max + rpm_range_ext, 30)
                    amp_plane = np.linspace(amp_min - amp_range_ext, amp_max + amp_range_ext, 30)
                    RPM, AMP = np.meshgrid(rpm_plane, amp_plane)
                    
                    # Calculate Z values for the fitted plane
                    Z = coeffs[0] * RPM + coeffs[1] * AMP + coeffs[2]
                    
                    # Create surface plot
                    surface = ax.plot_surface(RPM, AMP, Z, cmap=colormap, alpha=0.6, 
                                            linewidth=0, antialiased=True)
                    
                    # Add colorbar
                    self.figure.colorbar(surface, ax=ax, shrink=0.8)
                    
                    # Add scatter points for actual data
                    ax.scatter(rpm_values, amperage_values, z_values, 
                              c='red', s=30, alpha=1.0, label='Data Points', edgecolors='black', linewidth=0.5)
                    ax.legend()
                    
                else:
                    # Very few points, just show scatter with note
                    scatter = ax.scatter(rpm_values, amperage_values, z_values, 
                                       c=z_values, cmap=colormap, s=80, alpha=0.8, edgecolors='black', linewidth=0.5)
                    self.figure.colorbar(scatter, ax=ax, shrink=0.8)
                    
                    ax.text(0.02, 0.98, 0.98, 'Note: Need at least 3 data points for plane visualization', 
                           transform=ax.transAxes, fontsize=8, color='orange', 
                           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
                
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
                    # Write metadata comments first
                    csvfile.write(f"# 3D Sweep Data Export\n")
                    csvfile.write(f"# Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    csvfile.write(f"# Total Data Points: {len(self.sweep_data)}\n")
                    
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
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
        
    def import_csv_data(self):
        """Import sweep data from a CSV file."""
        # Get file from user
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import 3D Sweep Data",
            "",
            "CSV files (*.csv);;All files (*.*)"
        )
        
        if not filename:
            return
            
        try:
            import csv
            
            # Read CSV file
            imported_data = []
            required_columns = ['target_rpm', 'target_amperage', 'max_temp_fet', 'total_power']
            
            with open(filename, 'r', newline='') as csvfile:
                # Skip comment lines that start with #
                lines = [line for line in csvfile if not line.strip().startswith('#')]
                csvfile.seek(0)
                
                # Read the file content without comment lines
                content = ''.join(line for line in csvfile if not line.strip().startswith('#'))
                
                # Create a string reader for the filtered content
                from io import StringIO
                string_reader = StringIO(content)
                
                # Detect delimiter with fallback options
                try:
                    dialect = csv.Sniffer().sniff(content[:1024], delimiters=',;\t ')
                    reader = csv.DictReader(string_reader, dialect=dialect)
                except csv.Error:
                    # Fallback: try common delimiters manually
                    string_reader.seek(0)
                    first_line = string_reader.readline().strip()
                    
                    # Count occurrences of different delimiters
                    comma_count = first_line.count(',')
                    semicolon_count = first_line.count(';')
                    tab_count = first_line.count('\t')
                    space_count = len(first_line.split()) - 1  # spaces between words
                    
                    # Choose delimiter with highest count
                    delimiter_counts = [
                        (',', comma_count),
                        (';', semicolon_count),
                        ('\t', tab_count),
                        (' ', space_count)
                    ]
                    delimiter = max(delimiter_counts, key=lambda x: x[1])[0]
                    
                    string_reader.seek(0)
                    reader = csv.DictReader(string_reader, delimiter=delimiter)
                
                # Validate required columns exist
                fieldnames = reader.fieldnames
                if not fieldnames:
                    raise ValueError("CSV file appears to be empty or malformed")
                
                missing_columns = [col for col in required_columns if col not in fieldnames]
                if missing_columns:
                    QMessageBox.warning(self, "Missing Columns", 
                                      f"CSV file is missing required columns: {', '.join(missing_columns)}\n\n"
                                      f"Required columns: {', '.join(required_columns)}\n"
                                      f"Found columns: {', '.join(fieldnames)}")
                    return
                
                # Read and convert data
                for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
                    try:
                        # Create data point with required fields
                        data_point = {
                            'target_rpm': float(row['target_rpm']),
                            'target_amperage': float(row['target_amperage']),
                            'max_temp_fet': float(row['max_temp_fet']),
                            'total_power': float(row['total_power'])
                        }
                        
                        # Add optional fields if they exist
                        optional_fields = {
                            'actual_rpm': 'target_rpm',  # Default to target if not present
                            'actual_amperage': 'target_amperage',
                            'drive_power': 'total_power',
                            'brake_power': 'total_power',
                            'max_temp_motor': 'max_temp_fet',
                            'drive_temp_fet': 'max_temp_fet',
                            'drive_temp_motor': 'max_temp_fet',
                            'brake_temp_fet': 'max_temp_fet',
                            'brake_temp_motor': 'max_temp_fet',
                            'drive_voltage': 0,
                            'brake_voltage': 0
                        }
                        
                        for field, default_field in optional_fields.items():
                            if field in row and row[field]:
                                try:
                                    data_point[field] = float(row[field])
                                except ValueError:
                                    if isinstance(default_field, str) and default_field in data_point:
                                        data_point[field] = data_point[default_field]
                                    else:
                                        data_point[field] = default_field
                            else:
                                if isinstance(default_field, str) and default_field in data_point:
                                    data_point[field] = data_point[default_field]
                                else:
                                    data_point[field] = default_field
                        
                        imported_data.append(data_point)
                        
                    except ValueError as e:
                        QMessageBox.warning(self, "Data Error", 
                                          f"Error parsing row {row_num}: {str(e)}\n"
                                          f"Row data: {dict(row)}")
                        return
                
            if not imported_data:
                QMessageBox.warning(self, "No Data", "No valid data found in CSV file")
                return
                
            # Ask user if they want to replace or append data
            if self.sweep_data:
                reply = QMessageBox.question(self, "Import Data", 
                                           f"Found {len(imported_data)} data points.\n\n"
                                           f"Replace existing data ({len(self.sweep_data)} points) or append to it?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                                           QMessageBox.StandardButton.Yes)
                
                if reply == QMessageBox.StandardButton.Cancel:
                    return
                elif reply == QMessageBox.StandardButton.Yes:
                    # Replace existing data
                    self.sweep_data = imported_data
                else:
                    # Append to existing data
                    self.sweep_data.extend(imported_data)
            else:
                # No existing data, just set it
                self.sweep_data = imported_data
            
            # Update the plot
            self.update_plot()
            
            QMessageBox.information(self, "Success", 
                                  f"Successfully imported {len(imported_data)} data points from CSV.\n"
                                  f"Total data points: {len(self.sweep_data)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import CSV file:\n{str(e)}")
    
    def set_enabled(self, enabled):
        """Enable/disable the widget."""
        self.plot_type_combo.setEnabled(enabled)
        self.refresh_button.setEnabled(enabled)
        self.export_button.setEnabled(enabled and bool(self.sweep_data))
        self.export_data_button.setEnabled(enabled and bool(self.sweep_data))
        self.import_data_button.setEnabled(enabled)