"""
Test results widget for dynamometer interface.
Displays test results in a tree view with export functionality.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTreeWidget, QTreeWidgetItem, QTabWidget, QLabel, QSizePolicy)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal
import sys
import os

# Add visualization module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from visualization.plot3d_widget import Plot3DWidget


class ResultsWidget(QWidget):
    """Widget for displaying test results."""
    
    clear_results_requested = pyqtSignal()
    export_results_requested = pyqtSignal()
    plot_exported = pyqtSignal(str)  # Forward signal from 3D plot widget
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Create the results UI with tabs for different views."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create traditional results tab
        self.results_tab = QWidget()
        self.tab_widget.addTab(self.results_tab, "Test Results")
        self._setup_results_tab()
        
        # Create 3D plots tab
        self.plots_tab = QWidget()
        self.tab_widget.addTab(self.plots_tab, "3D Visualization")
        self._setup_plots_tab()
        
    def _setup_results_tab(self):
        """Setup the traditional results tab."""
        layout = QVBoxLayout(self.results_tab)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        clear_button = QPushButton("Clear Results")
        clear_button.clicked.connect(self.clear_results_requested.emit)
        button_layout.addWidget(clear_button)
        
        export_button = QPushButton("Export CSV")
        export_button.clicked.connect(self.export_results_requested.emit)
        button_layout.addWidget(export_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Results tree
        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(['Time', 'RPM', 'Load(A)', 'Power(W)', 
                                          'Temp_FET', 'Temp_Motor'])
        tree_font = QFont("Arial", 12)
        self.results_tree.setFont(tree_font)
        layout.addWidget(self.results_tree)
        
    def _setup_plots_tab(self):
        """Setup the 3D plots tab."""
        layout = QVBoxLayout(self.plots_tab)
        
        # Info label
        info_layout = QHBoxLayout()
        info_label = QLabel("3D visualization of sweep test data. Run a 3D sweep test to see plots.")
        info_label.setStyleSheet("color: #666; font-style: italic; margin: 5px;")
        info_layout.addWidget(info_label)
        info_layout.addStretch()
        
        # Data summary label
        self.data_summary_label = QLabel("No 3D sweep data")
        self.data_summary_label.setStyleSheet("color: #333; font-weight: bold; margin: 5px;")
        info_layout.addWidget(self.data_summary_label)
        
        layout.addLayout(info_layout)
        
        # Create 3D plot widget
        self.plot3d_widget = Plot3DWidget()
        self.plot3d_widget.plot_exported.connect(self.plot_exported.emit)  # Forward signal
        layout.addWidget(self.plot3d_widget)
        
    def add_result(self, data_point):
        """Add a test result to the tree."""
        item = QTreeWidgetItem([
            data_point['time'],
            f"{data_point['rpm']:.0f}",
            f"{data_point['load_current']:.2f}",
            f"{data_point['power']:.2f}",
            f"{data_point['temp_fet']:.1f}",
            f"{data_point['temp_motor']:.1f}"
        ])
        self.results_tree.addTopLevelItem(item)
        
        # Auto-scroll to bottom
        self.results_tree.scrollToBottom()
        
    def clear_results(self):
        """Clear all results from the tree."""
        self.results_tree.clear()
        
    def get_result_count(self):
        """Get the number of results in the tree."""
        return self.results_tree.topLevelItemCount()
        
    def update_results(self, test_data):
        """Update the tree with all test data."""
        self.clear_results()
        for data_point in test_data:
            self.add_result(data_point)
    
    def update_3d_plots(self, sweep_data):
        """Update 3D plots with sweep test data."""
        self.plot3d_widget.set_sweep_data(sweep_data)
        
        # Update data summary
        if sweep_data:
            summary = self.plot3d_widget.get_data_summary()
            self.data_summary_label.setText(summary)
            
            # Switch to 3D plots tab to show the new data
            self.tab_widget.setCurrentWidget(self.plots_tab)
        else:
            self.data_summary_label.setText("No 3D sweep data")
    
    def clear_3d_plots(self):
        """Clear 3D plots."""
        self.plot3d_widget.clear_plot()
        self.data_summary_label.setText("No 3D sweep data")
    
    def export_3d_plot(self):
        """Export current 3D plot."""
        self.plot3d_widget.export_plot()
    
    def export_3d_data(self):
        """Export 3D sweep data."""
        self.plot3d_widget.export_data()
            
    def set_enabled(self, enabled):
        """Enable/disable the results widget."""
        self.results_tree.setEnabled(enabled)
        self.plot3d_widget.setEnabled(enabled)