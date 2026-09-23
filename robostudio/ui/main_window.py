"""
RoboStudio Main Window UI – coded manually with PySide6.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPlainTextEdit,
    QPushButton, QTextEdit, QLabel, QFrame, QMenuBar, QMenu, QMessageBox,
    QFileDialog, QTabWidget, QGroupBox, QComboBox, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QAction, QCursor

from ui.responsive import make_scroll_area
from ui.responsive_hardware_tab import ResponsiveHardwareTab


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        MainWindow.setWindowTitle("RoboStudio")
        MainWindow.resize(1180, 780)
        # Phase 1 deliberately permits compact desktop sizes. Individual tabs
        # now scroll/stack instead of relying on a near-1000px window floor.
        MainWindow.setMinimumSize(760, 540)

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
        self.main_tabs.setDocumentMode(True)
        main_layout.addWidget(self.main_tabs, 1)

        # Program tab. The content itself can scroll vertically at compact
        # heights; long target/capability text therefore never competes with
        # editor/output hard minimums.
        self.program_tab = QWidget()
        program_root = QVBoxLayout(self.program_tab)
        program_root.setContentsMargins(0, 0, 0, 0)
        program_root.setSpacing(0)

        program_content = QWidget()
        program_layout = QVBoxLayout(program_content)
        program_layout.setSpacing(10)
        program_layout.setContentsMargins(4, 4, 4, 4)

        # H26-L target selector. Description sits on its own row so a long
        # target description cannot squeeze the selector horizontally.
        target_grid = QGridLayout()
        target_grid.setHorizontalSpacing(8)
        target_grid.setVerticalSpacing(4)
        target_grid.addWidget(QLabel("Target:"), 0, 0)
        self.target_combo = QComboBox()
        self.target_combo.setObjectName("target_combo")
        self.target_combo.setMinimumWidth(140)
        self.target_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        target_grid.addWidget(self.target_combo, 0, 1)
        target_grid.setColumnStretch(1, 1)

        self.target_description = QLabel("")
        self.target_description.setWordWrap(True)
        self.target_description.setStyleSheet("color: #666666;")
        target_grid.addWidget(self.target_description, 1, 0, 1, 2)
        program_layout.addLayout(target_grid)

        # Code Editor
        self.code_editor = QPlainTextEdit()
        self.code_editor.setPlaceholderText("Paste your RoboSim Python code here...")
        font = QFont("Courier New", 11)
        self.code_editor.setFont(font)
        self.code_editor.setMinimumHeight(180)
        self.code_editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        program_layout.addWidget(self.code_editor, 3)

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
        self.compile_button.setMinimumWidth(90)
        self.compile_button.setEnabled(True)
        button_layout.addWidget(self.compile_button)

        self.open_firmware_button = QPushButton("Open Firmware")
        self.open_firmware_button.setMinimumWidth(90)
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
        self.build_output.setMinimumHeight(110)
        self.build_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        program_layout.addWidget(self.build_output, 2)

        self.program_scroll = make_scroll_area(program_content)
        self.program_scroll.setObjectName("program_scroll")
        program_root.addWidget(self.program_scroll, 1)
        self.main_tabs.addTab(self.program_tab, "Program")

        # Hardware tab keeps the existing hardware behaviour but places long
        # device lists/status text inside a vertical scroll container.
        self.hardware_tab = ResponsiveHardwareTab()
        self.main_tabs.addTab(self.hardware_tab, "Hardware")

        # Status Bar
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("font-weight: bold; color: green;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        main_layout.addLayout(status_layout)

        # Store menubar reference for later
        self.menubar = menubar
