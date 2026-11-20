#!/usr/bin/env python3
"""
FlowMatic — Visual Automation Tool
===================================
Main entry point. Run this file to start the application.

Usage:
    python main.py

Requirements:
    pip install PySide6 psutil pygetwindow keyboard
"""

import sys
import os

# Ensure the project root is on the Python path
sys.path.insert(0, os.path.dirname(__file__))

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("FlowMatic")
    app.setApplicationDisplayName("FlowMatic")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("FlowMatic")
    # Keep running in tray when the main window is hidden
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()
    window.install_hotkey_filter(app)
    if not window.should_start_in_tray():
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
