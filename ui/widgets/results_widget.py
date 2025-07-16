"""
Test results widget for dynamometer interface.
Displays test results in a tree view with export functionality.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTreeWidget, QTreeWidgetItem)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal


class ResultsWidget(QWidget):
    """Widget for displaying test results."""
    
    clear_results_requested = pyqtSignal()
    export_results_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Create the results UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        clear_button = QPushButton("Clear Results")
        clear_button.clicked.connect(self.clear_results_requested.emit)
        button_layout.addWidget(clear_button)
        
        export_button = QPushButton("Export CSV")
        export_button.clicked.connect(self.export_results_requested.emit)
        button_layout.addWidget(export_button)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # Results tree
        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(['Time', 'RPM', 'Load(A)', 'Power(W)', 
                                          'Torque(Nm)', 'Efficiency(%)', 'Temp_FET', 'Temp_Motor'])
        tree_font = QFont("Arial", 12)
        self.results_tree.setFont(tree_font)
        main_layout.addWidget(self.results_tree)
        
    def add_result(self, data_point):
        """Add a test result to the tree."""
        item = QTreeWidgetItem([
            data_point['time'],
            f"{data_point['rpm']:.0f}",
            f"{data_point['load_current']:.2f}",
            f"{data_point['power']:.2f}",
            f"{data_point['torque']:.3f}",
            f"{data_point['efficiency']:.1f}",
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
            
    def set_enabled(self, enabled):
        """Enable/disable the results widget."""
        self.results_tree.setEnabled(enabled)