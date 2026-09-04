"""
RoboStudio Main Window UI – coded manually with PySide6.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QTextEdit, QLabel, QFrame, QMenuBar, QMenu, QMessageBox, QFileDialog, QTabWidget, QGroupBox, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QAction, QCursor

from ui.hardware_tab import HardwareTab


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        MainWindow.setWindowTitle("RoboStudio")
        MainWindow.resize(850, 650)

        # Menu Bar
        menubar = QMenuBar(MainWindow)
        MainWindow.setMenuBar(menubar)

        # File menu
        self.file_menu = menubar.addMenu("&File")
        self.file_menu.setObjectName("menuFile")

        # Examples menu
        self.examples_menu = menubar.addMenu("&Examples")

        # Help menu
        help_menu = menubar.addMenu("&Help")
        self.about_action = QAction("About", MainWindow)
        help_menu.addAction(self.about_action)

        # Central widget
        central_widget = QWidget(MainWindow)
        MainWindow.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Main tabs
        self.main_tabs = QTabWidget()
        main_layout.addWidget(self.main_tabs, 1)

        # Program tab
        self.program_tab = QWidget()
        program_layout = QVBoxLayout(self.program_tab)
        program_layout.setSpacing(10)
        program_layout.setContentsMargins(0, 0, 0, 0)

        # H26-L target selector
        target_layout = QHBoxLayout()
        target_layout.setSpacing(8)
        target_layout.addWidget(QLabel("Target:"))
        self.target_combo = QComboBox()
        self.target_combo.setObjectName("target_combo")
        self.target_combo.setMinimumWidth(180)
        target_layout.addWidget(self.target_combo)
        self.target_description = QLabel("")
        self.target_description.setWordWrap(True)
        self.target_description.setStyleSheet("color: #666666;")
        target_layout.addWidget(self.target_description, 1)
        program_layout.addLayout(target_layout)

        # Code Editor
        self.code_editor = QPlainTextEdit()
        self.code_editor.setPlaceholderText("Paste your RoboSim Python code here...")
        font = QFont("Courier New", 11)
        self.code_editor.setFont(font)
        self.code_editor.setMinimumHeight(250)
        program_layout.addWidget(self.code_editor)

        # H25-J / H26-L capability status
        self.capability_group = QGroupBox("Hardware & Target Capability")
        capability_layout = QVBoxLayout(self.capability_group)
        capability_layout.setContentsMargins(10, 8, 10, 8)
        capability_layout.setSpacing(4)

        self.capability_summary = QLabel("Analyzing program requirements...")
        self.capability_summary.setWordWrap(True)
        self.capability_summary.setStyleSheet("font-weight: bold;")
        capability_layout.addWidget(self.capability_summary)

        self.capability_details = QLabel("")
        self.capability_details.setWordWrap(True)
        self.capability_details.setStyleSheet("color: #666666;")
        capability_layout.addWidget(self.capability_details)

        self.target_capability_details = QLabel("")
        self.target_capability_details.setWordWrap(True)
        self.target_capability_details.setStyleSheet("color: #666666;")
        capability_layout.addWidget(self.target_capability_details)

        program_layout.addWidget(self.capability_group)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.compile_button = QPushButton("Compile")
        self.compile_button.setMinimumWidth(100)
        self.compile_button.setEnabled(True)
        button_layout.addWidget(self.compile_button)

        self.open_firmware_button = QPushButton("Open Firmware")
        self.open_firmware_button.setMinimumWidth(100)
        button_layout.addWidget(self.open_firmware_button)

        button_layout.addStretch()
        program_layout.addLayout(button_layout)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        program_layout.addWidget(line)

        # Build Output
        self.build_output = QTextEdit()
        self.build_output.setReadOnly(True)
        self.build_output.setPlaceholderText("Build output will appear here...")
        font_output = QFont("Courier New", 10)
        self.build_output.setFont(font_output)
        self.build_output.setMinimumHeight(150)
        program_layout.addWidget(self.build_output)

        self.main_tabs.addTab(self.program_tab, "Program")

        # Hardware tab (H25-B)
        self.hardware_tab = HardwareTab()
        self.main_tabs.addTab(self.hardware_tab, "Hardware")

        # Status Bar
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold; color: green;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        main_layout.addLayout(status_layout)

        # Store menubar reference for later
        self.menubar = menubar
