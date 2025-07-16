#!/usr/bin/env python3
"""
VESC Dyno Controller
===============================================

Features:
- Drive motor speed control
- Brake motor load control  
- Real-time power/torque curves
- Automated test sequences
- Data logging and export
- Safety monitoring

Usage:
python main.py
"""

import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import DynamometerMainWindow, setup_application_style


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Set up the UI styling
    setup_application_style()
    
    # Create and show main window
    window = DynamometerMainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()