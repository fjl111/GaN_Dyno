"""
CSV export functionality for dyno test results.
Handles exporting test data to CSV format.
"""

import csv
from datetime import datetime
from PyQt5.QtWidgets import QFileDialog, QMessageBox


class CSVExporter:
    """Handles CSV export of test data."""
    
    def __init__(self, parent_widget=None):
        self.parent_widget = parent_widget
        
    def export_test_data(self, test_data, default_filename=None):
        """Export test data to CSV file."""
        if not test_data:
            if self.parent_widget:
                QMessageBox.warning(self.parent_widget, "Warning", "No test data to export")
            return False, "No test data to export"
            
        # Generate default filename if not provided
        if not default_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"dyno_test_results_{timestamp}.csv"
            
        # Get save location from user
        filename, _ = QFileDialog.getSaveFileName(
            self.parent_widget, 
            "Export Test Results",
            default_filename,
            "CSV files (*.csv);;All files (*.*)"
        )
        
        if not filename:
            return False, "Export cancelled"
            
        try:
            self._write_csv_file(filename, test_data)
            
            if self.parent_widget:
                QMessageBox.information(self.parent_widget, "Success", 
                                      f"Test results exported to {filename}")
            return True, f"Test results exported to {filename}"
            
        except Exception as e:
            error_msg = f"Failed to export: {str(e)}"
            if self.parent_widget:
                QMessageBox.critical(self.parent_widget, "Error", error_msg)
            return False, error_msg
            
    def _write_csv_file(self, filename, test_data):
        """Write test data to CSV file."""
        fieldnames = ['time', 'rpm', 'load_current', 'power', 
                     'temp_fet', 'temp_motor']
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write data rows
            for row in test_data:
                writer.writerow(row)
                
    def export_realtime_data(self, data_model, default_filename=None):
        """Export real-time data to CSV file."""
        if not data_model.has_data():
            if self.parent_widget:
                QMessageBox.warning(self.parent_widget, "Warning", "No real-time data to export")
            return False, "No real-time data to export"
            
        # Generate default filename if not provided
        if not default_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"dyno_realtime_data_{timestamp}.csv"
            
        # Get save location from user
        filename, _ = QFileDialog.getSaveFileName(
            self.parent_widget, 
            "Export Real-time Data",
            default_filename,
            "CSV files (*.csv);;All files (*.*)"
        )
        
        if not filename:
            return False, "Export cancelled"
            
        try:
            self._write_realtime_csv_file(filename, data_model)
            
            if self.parent_widget:
                QMessageBox.information(self.parent_widget, "Success", 
                                      f"Real-time data exported to {filename}")
            return True, f"Real-time data exported to {filename}"
            
        except Exception as e:
            error_msg = f"Failed to export: {str(e)}"
            if self.parent_widget:
                QMessageBox.critical(self.parent_widget, "Error", error_msg)
            return False, error_msg
            
    def _write_realtime_csv_file(self, filename, data_model, time_range_seconds=None):
        """Write real-time data to CSV file."""
        # Use database-backed data retrieval for specific time ranges
        if time_range_seconds is not None:
            plot_data = data_model.get_plot_data(time_range_seconds=time_range_seconds)
        else:
            plot_data = data_model.get_plot_data()
        
        fieldnames = ['timestamp', 'drive_rpm', 'drive_current', 'drive_temp_fet', 
                     'drive_temp_motor', 'brake_rpm', 'brake_current', 'brake_temp_fet', 
                     'brake_temp_motor', 'drive_power', 'brake_power']
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write data rows
            for i in range(len(plot_data['timestamps'])):
                row = {
                    'timestamp': plot_data['timestamps'][i],
                    'drive_rpm': plot_data['drive_rpm'][i],
                    'drive_current': plot_data['drive_current'][i],
                    'drive_temp_fet': plot_data['drive_temp_fet'][i],
                    'drive_temp_motor': plot_data['drive_temp_motor'][i],
                    'brake_rpm': plot_data['brake_rpm'][i],
                    'brake_current': plot_data['brake_current'][i],
                    'brake_temp_fet': plot_data['brake_temp_fet'][i],
                    'brake_temp_motor': plot_data['brake_temp_motor'][i],
                    'drive_power': plot_data['drive_power'][i],
                    'brake_power': plot_data['brake_power'][i]
                }
                writer.writerow(row)
                
    def export_current_values(self, data_model, default_filename=None):
        """Export current values snapshot to CSV file."""
        # Generate default filename if not provided
        if not default_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"dyno_current_values_{timestamp}.csv"
            
        # Get save location from user
        filename, _ = QFileDialog.getSaveFileName(
            self.parent_widget, 
            "Export Current Values",
            default_filename,
            "CSV files (*.csv);;All files (*.*)"
        )
        
        if not filename:
            return False, "Export cancelled"
            
        try:
            self._write_current_values_csv_file(filename, data_model)
            
            if self.parent_widget:
                QMessageBox.information(self.parent_widget, "Success", 
                                      f"Current values exported to {filename}")
            return True, f"Current values exported to {filename}"
            
        except Exception as e:
            error_msg = f"Failed to export: {str(e)}"
            if self.parent_widget:
                QMessageBox.critical(self.parent_widget, "Error", error_msg)
            return False, error_msg
            
    def _write_current_values_csv_file(self, filename, data_model):
        """Write current values to CSV file."""
        current_values = data_model.current_values
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['Section', 'Parameter', 'Value'])
            
            # Write drive motor values
            for key, value in current_values['drive'].items():
                writer.writerow(['Drive Motor', key.replace('_', ' ').title(), value])
                
            # Write brake motor values
            for key, value in current_values['brake'].items():
                writer.writerow(['Brake Motor', key.replace('_', ' ').title(), value])
                
            # Write dyno values
            for key, value in current_values['dyno'].items():
                writer.writerow(['Dyno', key.replace('_', ' ').title(), value])
                
    def export_time_range_data(self, data_model, time_range_seconds, default_filename=None):
        """Export data for a specific time range from database."""
        if not data_model.has_data():
            if self.parent_widget:
                QMessageBox.warning(self.parent_widget, "Warning", "No data to export")
            return False, "No data to export"
            
        # Generate default filename if not provided
        if not default_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if time_range_seconds == 0:
                range_desc = "all_time"
            elif time_range_seconds < 60:
                range_desc = f"{time_range_seconds}sec"
            elif time_range_seconds < 3600:
                range_desc = f"{time_range_seconds//60}min"
            else:
                range_desc = f"{time_range_seconds//3600}hr"
            default_filename = f"dyno_data_{range_desc}_{timestamp}.csv"
            
        # Get save location from user
        filename, _ = QFileDialog.getSaveFileName(
            self.parent_widget, 
            f"Export {range_desc} Data",
            default_filename,
            "CSV files (*.csv);;All files (*.*)"
        )
        
        if not filename:
            return False, "Export cancelled"
            
        try:
            self._write_realtime_csv_file(filename, data_model, time_range_seconds)
            
            if self.parent_widget:
                QMessageBox.information(self.parent_widget, "Success", 
                                      f"Time range data exported to {filename}")
            return True, f"Time range data exported to {filename}"
            
        except Exception as e:
            error_msg = f"Failed to export: {str(e)}"
            if self.parent_widget:
                QMessageBox.critical(self.parent_widget, "Error", error_msg)
            return False, error_msg
    
    def export_full_session_data(self, data_model, default_filename=None):
        """Export complete session data from database."""
        return self.export_time_range_data(data_model, 0, default_filename)  # 0 = all data
    
    def export_3d_sweep_data(self, sweep_data, default_filename=None):
        """Export 3D sweep data to CSV file in MATLAB-compatible format."""
        if not sweep_data:
            if self.parent_widget:
                QMessageBox.warning(self.parent_widget, "Warning", "No 3D sweep data to export")
            return False, "No 3D sweep data to export"
            
        # Generate default filename if not provided
        if not default_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"dyno_3d_sweep_{timestamp}.csv"
            
        # Get save location from user
        filename, _ = QFileDialog.getSaveFileName(
            self.parent_widget, 
            "Export 3D Sweep Data",
            default_filename,
            "CSV files (*.csv);;All files (*.*)"
        )
        
        if not filename:
            return False, "Export cancelled"
            
        try:
            self._write_3d_sweep_csv_file(filename, sweep_data)
            
            if self.parent_widget:
                QMessageBox.information(self.parent_widget, "Success", 
                                      f"3D sweep data exported to {filename}")
            return True, f"3D sweep data exported to {filename}"
            
        except Exception as e:
            error_msg = f"Failed to export: {str(e)}"
            if self.parent_widget:
                QMessageBox.critical(self.parent_widget, "Error", error_msg)
            return False, error_msg
            
    def _write_3d_sweep_csv_file(self, filename, sweep_data):
        """Write 3D sweep data to CSV file in MATLAB-compatible format."""
        # Define fieldnames optimized for MATLAB 3D plotting
        fieldnames = [
            'target_rpm', 'target_amperage', 'actual_rpm', 'actual_amperage',
            'total_power', 'drive_power', 'brake_power',
            'max_temp_fet', 'max_temp_motor', 'drive_temp_fet', 'drive_temp_motor',
            'brake_temp_fet', 'brake_temp_motor', 'drive_voltage', 'brake_voltage',
            'step_number'
        ]
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write metadata as comments (MATLAB can ignore lines starting with %)
            csvfile.write(f"% 3D Sweep Test Data Export\n")
            csvfile.write(f"% Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            csvfile.write(f"% Total Data Points: {len(sweep_data)}\n")
            
            if sweep_data:
                # Calculate sweep ranges from data
                rpm_values = sorted(set(d['target_rpm'] for d in sweep_data))
                amp_values = sorted(set(d['target_amperage'] for d in sweep_data))
                
                csvfile.write(f"% RPM Range: {min(rpm_values):.0f} to {max(rpm_values):.0f} ({len(rpm_values)} steps)\n")
                csvfile.write(f"% Amperage Range: {min(amp_values):.2f} to {max(amp_values):.2f} A ({len(amp_values)} steps)\n")
                csvfile.write(f"% \n")
                csvfile.write(f"% MATLAB Usage Examples:\n")
                csvfile.write(f"% data = readtable('{filename.split('/')[-1]}', 'CommentStyle', '%%');\n")
                csvfile.write(f"% [RPM, AMP] = meshgrid(unique(data.target_rpm), unique(data.target_amperage));\n")
                csvfile.write(f"% POWER = griddata(data.target_rpm, data.target_amperage, data.total_power, RPM, AMP);\n")
                csvfile.write(f"% surf(RPM, AMP, POWER); xlabel('RPM'); ylabel('Amperage (A)'); zlabel('Power (W)');\n")
                csvfile.write(f"% \n")
            
            # Write data rows
            for i, row in enumerate(sweep_data):
                # Ensure all required fields are present
                output_row = {}
                for field in fieldnames:
                    if field == 'step_number':
                        output_row[field] = i + 1
                    else:
                        output_row[field] = row.get(field, 0)
                
                writer.writerow(output_row)
    
    def get_export_options(self):
        """Get available export time range options."""
        return {
            'Last 10 seconds': 10,
            'Last 30 seconds': 30,
            'Last 1 minute': 60,
            'Last 2 minutes': 120,
            'Last 5 minutes': 300,
            'Last 10 minutes': 600,
            'Last 30 minutes': 1800,
            'Last 1 hour': 3600,
            'All session data': 0
        }