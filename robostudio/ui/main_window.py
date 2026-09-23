"""RoboStudio Main Window UI – coded manually with PySide6."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPlainTextEdit,
    QPushButton, QTextEdit, QLabel, QFrame, QMenuBar, QTabWidget,
    QGroupBox, QComboBox, QSizePolicy
)
from PySide6.QtGui import QFont, QAction

from ui import theme
from ui.components import DisclosureButton
from ui.responsive import make_scroll_area
from ui.responsive_hardware_tab import ResponsiveHardwareTab


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        MainWindow.setWindowTitle("RoboStudio")
        MainWindow.resize(1180, 780)
        MainWindow.setMinimumSize(760, 540)

        menubar = QMenuBar(MainWindow)
        MainWindow.setMenuBar(menubar)

        self.file_menu = menubar.addMenu("&File")
        self.file_menu.setObjectName("menuFile")
        self.examples_menu = menubar.addMenu("&Examples")

        self.advanced_menu = menubar.addMenu("&Advanced")
        self.open_firmware_action = QAction("Open Firmware", MainWindow)
        self.advanced_menu.addAction(self.open_firmware_action)

        help_menu = menubar.addMenu("&Help")
        self.about_action = QAction("About", MainWindow)
        help_menu.addAction(self.about_action)

        central_widget = QWidget(MainWindow)
        MainWindow.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.main_tabs = QTabWidget()
        self.main_tabs.setDocumentMode(True)
        main_layout.addWidget(self.main_tabs, 1)

        self.program_tab = QWidget()
        program_root = QVBoxLayout(self.program_tab)
        program_root.setContentsMargins(0, 0, 0, 0)
        program_root.setSpacing(0)

        program_content = QWidget()
        program_layout = QVBoxLayout(program_content)
        program_layout.setSpacing(10)
        program_layout.setContentsMargins(4, 4, 4, 4)

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
        self.target_description.setStyleSheet(f"color: {theme.TEXT_SECONDARY};")
        target_grid.addWidget(self.target_description, 1, 0, 1, 2)
        program_layout.addLayout(target_grid)

        self.code_editor = QPlainTextEdit()
        self.code_editor.setPlaceholderText("Paste your RoboSim Python code here...")
        self.code_editor.setFont(QFont("Courier New", 11))
        self.code_editor.setMinimumHeight(180)
        self.code_editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        program_layout.addWidget(self.code_editor, 3)

        self.capability_group = QGroupBox("Program Readiness")
        capability_layout = QVBoxLayout(self.capability_group)
        capability_layout.setContentsMargins(10, 8, 10, 8)
        capability_layout.setSpacing(4)

        capability_header = QHBoxLayout()
        self.capability_summary = QLabel("Analyzing program requirements...")
        self.capability_summary.setWordWrap(True)
        self.capability_summary.setStyleSheet("font-weight: 700;")
        capability_header.addWidget(self.capability_summary, 1)
        self.capability_disclosure = DisclosureButton("Readiness details")
        capability_header.addWidget(self.capability_disclosure)
        capability_layout.addLayout(capability_header)

        self.capability_details = QLabel("")
        self.capability_details.setWordWrap(True)
        self.capability_details.setStyleSheet(f"color: {theme.TEXT_SECONDARY};")
        self.capability_details.setVisible(False)
        capability_layout.addWidget(self.capability_details)

        self.target_capability_details = QLabel("")
        self.target_capability_details.setWordWrap(True)
        self.target_capability_details.setStyleSheet(f"color: {theme.TEXT_SECONDARY};")
        self.target_capability_details.setVisible(False)
        capability_layout.addWidget(self.target_capability_details)

        def toggle_capability_details(expanded: bool) -> None:
            self.capability_details.setVisible(expanded)
            self.target_capability_details.setVisible(expanded)

        self.capability_disclosure.toggled.connect(toggle_capability_details)
        program_layout.addWidget(self.capability_group)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        self.compile_button = QPushButton("Compile Program")
        self.compile_button.setMinimumWidth(110)
        self.compile_button.setStyleSheet(theme.primary_button_style())
        self.compile_button.setEnabled(True)
        button_layout.addWidget(self.compile_button)

        # Compatibility handle for controller/tests. The technical firmware
        # action now lives under Advanced rather than beside the primary compile
        # action in the student workflow.
        self.open_firmware_button = QPushButton("Open Firmware")
        self.open_firmware_button.setVisible(False)
        button_layout.addStretch(1)
        program_layout.addLayout(button_layout)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        program_layout.addWidget(line)

        output_header = QHBoxLayout()
        output_title = QLabel("Build Output")
        output_title.setStyleSheet("font-weight: 700;")
        output_header.addWidget(output_title)
        output_header.addStretch(1)
        program_layout.addLayout(output_header)

        self.build_output = QTextEdit()
        self.build_output.setReadOnly(True)
        self.build_output.setPlaceholderText("Build output will appear here...")
        self.build_output.setFont(QFont("Courier New", 10))
        self.build_output.setMinimumHeight(110)
        self.build_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        program_layout.addWidget(self.build_output, 2)

        self.program_scroll = make_scroll_area(program_content)
        self.program_scroll.setObjectName("program_scroll")
        program_root.addWidget(self.program_scroll, 1)
        self.main_tabs.addTab(self.program_tab, "Program")

        self.hardware_tab = ResponsiveHardwareTab()
        self.main_tabs.addTab(self.hardware_tab, "Hardware")

        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("font-weight: bold; color: green;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        main_layout.addLayout(status_layout)

        self.menubar = menubar
