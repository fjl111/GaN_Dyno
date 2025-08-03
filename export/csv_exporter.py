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
            
    def _write_realtime_csv_file(self, filename, data_model):
        """Write real-time data to CSV file."""
        plot_data = data_model.get_plot_data()
        
        fieldnames = ['timestamp', 'drive_rpm', 'drive_current', 'drive_temp_fet', 
                     'drive_temp_motor', 'brake_rpm', 'brake_current', 'brake_temp_fet', 
                     'brake_temp_motor', 'mechanical_power']
        
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
                    'mechanical_power': plot_data['mechanical_power'][i]
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